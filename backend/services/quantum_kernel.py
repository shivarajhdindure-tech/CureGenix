
"""Small, reproducible quantum-kernel experiments for CureGenix.

This module uses illustrative synthetic data only. It does not predict
real drug activity and is intended for integration and demonstration.
"""

import time

import numpy as np
from qiskit.circuit.library import ZZFeatureMap
from qiskit.primitives import StatevectorSampler
from qiskit_machine_learning.kernels import FidelityQuantumKernel
from qiskit_machine_learning.state_fidelities import ComputeUncompute
from sklearn.metrics import (
    accuracy_score,
    mean_absolute_error,
)
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC, SVR


def run_quantum_kernel_demo(
    task: str = "classification",
    landmarks: int = 4,
    seed: int = 42,
) -> dict:
    """Compare quantum and classical models on a small synthetic dataset."""
    if task not in {"classification", "regression"}:
        raise ValueError("task must be classification or regression")

    if not 2 <= landmarks <= 6:
        raise ValueError("landmarks must be between 2 and 6")

    # Fixed, reproducible synthetic inputs; not experimental chemistry data.
    X = np.array([
        [0.05, 0.10],
        [0.10, 0.20],
        [0.80, 0.75],
        [0.90, 0.85],
        [0.15, 0.10],
        [0.85, 0.90],
        [0.20, 0.30],
        [0.75, 0.65],
        [0.30, 0.15],
        [0.70, 0.80],
        [0.25, 0.35],
        [0.95, 0.70],
    ], dtype=float)

    y_class = np.array([0, 0, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1])
    y_reg = np.array([1.1, 1.3, 4.0, 4.4, 1.2, 4.2,
                      1.5, 3.8, 1.4, 4.1, 1.6, 4.3])

    y = y_class if task == "classification" else y_reg
    indices = np.arange(len(X))
    train_idx, test_idx = train_test_split(
        indices,
        test_size=0.33,
        random_state=seed,
        stratify=y_class if task == "classification" else None,
    )

    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]

    # Use only training examples as Nyström landmarks.
    landmark_count = min(landmarks, len(X_train))
    landmark_idx = np.linspace(
        0, len(X_train) - 1, landmark_count, dtype=int
    )
    X_landmarks = X_train[landmark_idx]

    feature_map = ZZFeatureMap(feature_dimension=2, reps=1)
    sampler = StatevectorSampler(default_shots=1024, seed=seed)
    fidelity = ComputeUncompute(sampler=sampler)
    kernel = FidelityQuantumKernel(
        feature_map=feature_map,
        fidelity=fidelity,
    )

    started = time.perf_counter()

    # Nyström approximation: K(X, landmarks) K(landmarks, landmarks)^+ K(landmarks, X)
    K_mm = kernel.evaluate(x_vec=X_landmarks)
    K_train_m = kernel.evaluate(x_vec=X_train, y_vec=X_landmarks)
    K_test_m = kernel.evaluate(x_vec=X_test, y_vec=X_landmarks)

    K_mm_pinv = np.linalg.pinv(K_mm, hermitian=True)
    K_train = K_train_m @ K_mm_pinv @ K_train_m.T
    K_test = K_test_m @ K_mm_pinv @ K_train_m.T

    # Stabilize numerical asymmetry in the approximate training kernel.
    K_train = (K_train + K_train.T) / 2.0

    if task == "classification":
        quantum_model = SVC(kernel="precomputed")
        classical_model = SVC(kernel="rbf")
    else:
        quantum_model = SVR(kernel="precomputed")
        classical_model = SVR(kernel="rbf")

    quantum_model.fit(K_train, y_train)
    quantum_predictions = quantum_model.predict(K_test)

    classical_model.fit(X_train, y_train)
    classical_predictions = classical_model.predict(X_test)

    if task == "classification":
        quantum_metric = accuracy_score(y_test, quantum_predictions)
        classical_metric = accuracy_score(y_test, classical_predictions)
        metric_name = "test_accuracy"
    else:
        quantum_metric = mean_absolute_error(y_test, quantum_predictions)
        classical_metric = mean_absolute_error(y_test, classical_predictions)
        metric_name = "test_mae"

    elapsed = time.perf_counter() - started

    return {
        "task": task,
        "dataset": "synthetic_illustration_not_drug_data",
        "evaluation": "held_out_split",
        "seed": seed,
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "feature_dimension": X.shape[1],
        "landmark_count": landmark_count,
        "metric": metric_name,
        "quantum_kernel_model": {
            metric_name: float(quantum_metric),
            "predictions": np.asarray(quantum_predictions).tolist(),
        },
        "classical_rbf_baseline": {
            metric_name: float(classical_metric),
            "predictions": np.asarray(classical_predictions).tolist(),
        },
        "kernel_visualization": {
            "landmark_kernel": K_mm.tolist(),
            "approximate_train_kernel": K_train.tolist(),
        },
        "runtime_seconds": round(elapsed, 4),
        "quantum_method": "ZZFeatureMap + fidelity kernel + Nyström approximation",
        "hardware": "classical statevector sampling simulator",
        "scientific_warning": (
            "Synthetic demonstration only. Metrics are not evidence of "
            "drug activity, clinical efficacy, or quantum advantage."
        ),
    }
