import json
import time
from pathlib import Path

import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.svm import SVR
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from qiskit.circuit.library import ZZFeatureMap
from qiskit.primitives import StatevectorSampler
from qiskit_machine_learning.kernels import FidelityQuantumKernel
from qiskit_machine_learning.state_fidelities import ComputeUncompute

ROOT = Path("benchmark_reports/egfr_regression")
DATA_PATH = ROOT / "fingerprints_and_targets.npz"
BASELINE_PATH = ROOT / "baseline_results.json"
OUT_PATH = ROOT / "quantum_kernel_results.json"
FEATURES_PATH = ROOT / "quantum_features.npz"

SEED = 42
N_COMPONENTS = 4
N_LANDMARKS = 12
SHOTS = 256

data = np.load(DATA_PATH, allow_pickle=False)
X = data["X"]
y = data["y"]
splits = data["splits"]
smiles = data["smiles"]
scaffolds = data["scaffold_groups"]

train_idx = np.flatnonzero(splits == "train")
val_idx = np.flatnonzero(splits == "validation")
test_idx = np.flatnonzero(splits == "test")

if not (len(train_idx) and len(val_idx) and len(test_idx)):
    raise RuntimeError("Expected train, validation, and test split labels.")

# Reduce the 2048-bit fingerprints to four dimensions.
# Fit every transformation on training data only.
print("Fitting training-only fingerprint reduction...")
start = time.perf_counter()

svd = TruncatedSVD(n_components=N_COMPONENTS, random_state=SEED)
X_train_reduced = svd.fit_transform(X[train_idx])

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train_reduced)

angle_scaler = MinMaxScaler(feature_range=(0, np.pi))
X_train_angles = angle_scaler.fit_transform(X_train_scaled)

def transform(indices):
    reduced = svd.transform(X[indices])
    scaled = scaler.transform(reduced)
    return angle_scaler.transform(scaled)

X_val_angles = transform(val_idx)
X_test_angles = transform(test_idx)

# Save the exact reduced features and their row identities.
np.savez_compressed(
    FEATURES_PATH,
    train_angles=X_train_angles,
    validation_angles=X_val_angles,
    test_angles=X_test_angles,
    train_y=y[train_idx],
    validation_y=y[val_idx],
    test_y=y[test_idx],
    train_smiles=smiles[train_idx],
    validation_smiles=smiles[val_idx],
    test_smiles=smiles[test_idx],
    train_scaffolds=scaffolds[train_idx],
    validation_scaffolds=scaffolds[val_idx],
    test_scaffolds=scaffolds[test_idx],
)
print(f"Feature preparation: {time.perf_counter() - start:.1f}s")

# Pick landmark rows from training compounds only.
rng = np.random.default_rng(SEED)
landmark_positions = np.sort(
    rng.choice(len(train_idx), size=min(N_LANDMARKS, len(train_idx)),
               replace=False)
)
Z = X_train_angles[landmark_positions]

# StatevectorSampler is a classical simulator, not quantum hardware.
sampler = StatevectorSampler(default_shots=SHOTS, seed=SEED)
fidelity = ComputeUncompute(sampler=sampler)
feature_map = ZZFeatureMap(
    feature_dimension=N_COMPONENTS,
    reps=1,
    entanglement="linear",
)
kernel = FidelityQuantumKernel(
    feature_map=feature_map,
    fidelity=fidelity,
    enforce_psd=True,
)

def symmetrize(matrix):
    return (matrix + matrix.T) / 2.0

print(
    f"Computing kernel: {len(train_idx)} training rows, "
    f"{len(Z)} landmarks, {SHOTS} shots..."
)
kernel_start = time.perf_counter()

K_mm = symmetrize(kernel.evaluate(x_vec=Z))
K_train_m = kernel.evaluate(x_vec=X_train_angles, y_vec=Z)
K_val_m = kernel.evaluate(x_vec=X_val_angles, y_vec=Z)
K_test_m = kernel.evaluate(x_vec=X_test_angles, y_vec=Z)

# Nyström approximation: K(X,Y) ~= K(X,Z) K(Z,Z)^+ K(Z,Y)
K_mm_pinv = np.linalg.pinv(K_mm, rcond=1e-8)
K_train = K_train_m @ K_mm_pinv @ K_train_m.T
K_train = symmetrize(K_train)
K_val = K_val_m @ K_mm_pinv @ K_train_m.T
K_test = K_test_m @ K_mm_pinv @ K_train_m.T

kernel_seconds = time.perf_counter() - kernel_start
print(f"Kernel construction: {kernel_seconds:.1f}s")

# Fixed, un-tuned SVR settings; use validation only for future model selection.
model = SVR(kernel="precomputed", C=10.0, epsilon=0.2)
model.fit(K_train, y[train_idx])

def metrics(actual, predicted):
    return {
        "mae": float(mean_absolute_error(actual, predicted)),
        "rmse": float(np.sqrt(mean_squared_error(actual, predicted))),
        "r2": float(r2_score(actual, predicted)),
    }

validation_pred = model.predict(K_val)
test_pred = model.predict(K_test)

with BASELINE_PATH.open(encoding="utf-8") as f:
    baseline = json.load(f)

result = {
    "experiment": "EGFR real-data Nyström quantum-kernel SVR",
    "dataset": "Heuristically curated EGFR biochemical candidate cohort",
    "seed": SEED,
    "feature_pipeline": {
        "input": "2048-bit Morgan fingerprints",
        "reduction": "training-only TruncatedSVD",
        "components": N_COMPONENTS,
        "scaling": "training-only StandardScaler then MinMaxScaler to [0, pi]",
        "variance_explained_ratio_sum": float(svd.explained_variance_ratio_.sum()),
    },
    "quantum_kernel": {
        "feature_map": "ZZFeatureMap",
        "reps": 1,
        "qubits": N_COMPONENTS,
        "landmarks": len(Z),
        "shots": SHOTS,
        "simulator": "Qiskit StatevectorSampler",
        "hardware_execution": False,
        "kernel_construction_seconds": kernel_seconds,
        "nystrom_formula": "K(X,Z) @ pinv(K(Z,Z)) @ K(Z,Y)",
    },
    "split_sizes": {
        "train": int(len(train_idx)),
        "validation": int(len(val_idx)),
        "test": int(len(test_idx)),
    },
    "metrics": {
        "validation": metrics(y[val_idx], validation_pred),
        "test": metrics(y[test_idx], test_pred),
    },
    "fixed_baseline_test_metrics": {
        name: model_results["test"]
        for name, model_results in baseline["results"].items()
    },
    "limitations": [
        "Assay cohort is selected with heuristic description filters.",
        "Four reduced features do not represent the full molecular structure.",
        "StatevectorSampler is a classical simulation, not quantum hardware.",
        "Only 12 training landmarks are used in this initial feasibility run.",
        "SVR hyperparameters are fixed, not optimized.",
        "No quantum advantage is established by this experiment.",
    ],
}

OUT_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")

print("\n===== QUANTUM-KERNEL REGRESSION =====")
print(json.dumps(result, indent=2))
print("\nSaved:", OUT_PATH)
print("Saved:", FEATURES_PATH)
