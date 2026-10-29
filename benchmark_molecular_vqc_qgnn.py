"""Train reusable VQC/QGNN artifacts and compare on the saved EGFR split.

Writes only to benchmark_reports/egfr_regression/vqc_qgnn_same_day and refuses
to overwrite it. Existing VQC and benchmark result directories are untouched.
"""

from __future__ import annotations

import csv
import json
import platform
import time
from pathlib import Path

import joblib
import numpy as np
import qiskit
import qiskit_machine_learning
import rdkit
import sklearn
from rdkit import Chem, DataStructs
from rdkit.Chem import rdFingerprintGenerator
from sklearn.decomposition import TruncatedSVD
from sklearn.metrics import accuracy_score, balanced_accuracy_score, roc_auc_score
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from sklearn.svm import SVC

from benchmark_egfr_vqc import (
    BALANCED_TRAIN_PER_CLASS, CURATED_PATH, FEATURES_PATH, N_COMPONENTS,
    SEED, VQC_MAXITER, VQC_REPS, SHOTS, _label,
)
from quantum.algorithms.qgnn import MolecularQGNN, graph_message_passing, molecular_graph_from_mol
from quantum.algorithms.vqc import create_vqc_classifier, fit_vqc, predict_vqc


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "benchmark_reports" / "egfr_regression" / "vqc_qgnn_same_day_v3"
FP_GENERATOR = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)


def _metrics(y, labels, scores):
    return {
        "sample_count": int(len(y)),
        "accuracy": float(accuracy_score(y, labels)),
        "balanced_accuracy": float(balanced_accuracy_score(y, labels)),
        "roc_auc": float(roc_auc_score(y, scores)) if len(np.unique(y)) == 2 else None,
    }


def run_experiment():
    if OUT.exists():
        raise FileExistsError(f"Refusing to overwrite existing experiment directory: {OUT}")
    with np.load(FEATURES_PATH, allow_pickle=False) as archive:
        fingerprints = np.asarray(archive["X"], dtype=np.float32)
        saved_smiles = archive["smiles"].astype(str)
        saved_splits = archive["splits"].astype(str)
        saved_scaffolds = archive["scaffold_groups"].astype(str)
    with CURATED_PATH.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != len(fingerprints):
        raise ValueError("Source rows and saved fingerprints are misaligned")

    labels = np.full(len(rows), -1, dtype=np.int64)
    graphs = [None] * len(rows)
    graph_vectors = []
    vector_indices = []
    for i, row in enumerate(rows):
        smiles = row["canonical_smiles"].strip()
        if saved_smiles[i] != smiles or saved_splits[i] != row["split"]:
            raise ValueError(f"Source identity or split mismatch at row {i}")
        if saved_scaffolds[i] != row["scaffold_group"]:
            raise ValueError(f"Saved scaffold mismatch at row {i}")
        y, _ = _label(row)
        molecule = Chem.MolFromSmiles(smiles) if smiles else None
        if molecule is not None and y is not None:
            labels[i] = y
            graphs[i] = molecular_graph_from_mol(molecule)
            graph_vectors.append(graph_message_passing(graphs[i]))
            vector_indices.append(i)

    graph_matrix = np.vstack(graph_vectors)
    graph_to_idx = {index: offset for offset, index in enumerate(vector_indices)}
    partitions = {
        name: np.asarray([i for i, row in enumerate(rows) if row["split"] == name and labels[i] >= 0], dtype=int)
        for name in ("train", "validation", "test")
    }
    group_sets = {
        part: {saved_scaffolds[i] for i in indices}
        for part, indices in partitions.items()
    }
    if any(group_sets[a] & group_sets[b] for a, b in (("train", "validation"), ("train", "test"), ("validation", "test"))):
        raise ValueError("Saved Murcko scaffold partition contains overlap")
    # Preserve the exact deterministic balanced training row selection used by VQC.
    train_idx = partitions["train"]
    rng = np.random.default_rng(SEED)
    selected = np.sort(np.concatenate([
        rng.choice(train_idx[labels[train_idx] == cls], size=BALANCED_TRAIN_PER_CLASS, replace=False)
        for cls in (0, 1)
    ]))

    # Both representations are fit on the labeled training partition only.
    svd = TruncatedSVD(n_components=N_COMPONENTS, random_state=SEED).fit(fingerprints[train_idx])
    standard = StandardScaler().fit(svd.transform(fingerprints[train_idx]))
    angle = MinMaxScaler(feature_range=(0.0, np.pi)).fit(standard.transform(svd.transform(fingerprints[train_idx])))
    def vqc_x(indices):
        return angle.transform(standard.transform(svd.transform(fingerprints[indices])))

    graph_train_rows = np.asarray([graph_to_idx[i] for i in train_idx])
    graph_svd = TruncatedSVD(n_components=N_COMPONENTS, random_state=SEED).fit(graph_matrix[graph_train_rows])
    graph_standard = StandardScaler().fit(graph_svd.transform(graph_matrix[graph_train_rows]))
    graph_angle = MinMaxScaler(feature_range=(0.0, np.pi)).fit(
        graph_standard.transform(graph_svd.transform(graph_matrix[graph_train_rows]))
    )
    def qgnn_x(indices):
        offsets = np.asarray([graph_to_idx[i] for i in indices])
        return graph_angle.transform(graph_standard.transform(graph_svd.transform(graph_matrix[offsets])))

    x_selected = vqc_x(selected)
    y_selected = labels[selected]
    vqc = create_vqc_classifier(N_COMPONENTS, VQC_REPS, VQC_MAXITER, SHOTS, SEED)
    vqc_diagnostics = fit_vqc(vqc, x_selected, y_selected)
    vqc_test = predict_vqc(vqc, vqc_x(partitions["test"]))
    vqc_validation = predict_vqc(vqc, vqc_x(partitions["validation"]))
    vqc_weights = np.asarray(vqc.weights, dtype=np.float64)
    if hasattr(vqc, "_callback"):
        vqc._callback = None  # Remove fit helper closure; weights are the persisted model state.

    qgnn = MolecularQGNN(reps=1, maxiter=24, seed=SEED)
    qgnn_train_indices = np.asarray([graph_to_idx[i] for i in selected])
    qgnn_diagnostics = qgnn.fit(graph_angle.transform(
        graph_standard.transform(graph_svd.transform(graph_matrix[qgnn_train_indices]))
    ), y_selected)
    qgnn_test_x, qgnn_validation_x = qgnn_x(partitions["test"]), qgnn_x(partitions["validation"])
    qgnn_test_probs = qgnn.predict_proba(qgnn_test_x)[:, 1]
    qgnn_test_labels = (qgnn_test_probs >= 0.5).astype(int)
    qgnn_validation_probs = qgnn.predict_proba(qgnn_validation_x)[:, 1]
    qgnn_validation_labels = (qgnn_validation_probs >= 0.5).astype(int)

    classical = SVC(kernel="rbf", C=1.0, gamma="scale", class_weight="balanced")
    classical_started = time.perf_counter()
    classical.fit(x_selected, y_selected)
    classical_runtime = time.perf_counter() - classical_started
    test_idx = partitions["test"]
    validation_idx = partitions["validation"]
    vqc_test_labels = np.asarray(vqc_test["predictions"], dtype=int)
    vqc_test_prob = np.asarray(vqc_test["probabilities"], dtype=float)[:, 1]
    y_test = labels[test_idx]
    y_validation = labels[validation_idx]
    classical_test_scores = classical.decision_function(vqc_x(test_idx))
    classical_validation_scores = classical.decision_function(vqc_x(validation_idx))

    OUT.mkdir(parents=True)
    # Joblib bundle stores only transformations and learned numeric weights,
    # avoiding Qiskit's non-pickleable local interpretation closure.
    joblib.dump({
        "model_id": "egfr-vqc-zz-real-amplitudes-v1",
        "svd": svd, "standard_scaler": standard, "angle_scaler": angle,
        "vqc_weights": vqc_weights,
        "config": {"feature_dimension": N_COMPONENTS, "reps": VQC_REPS, "maxiter": VQC_MAXITER, "shots": SHOTS, "seed": SEED},
    }, OUT / "vqc_model.joblib")
    joblib.dump({
        "model_id": "egfr-qgnn-message-passing-pqc-v1",
        "graph_svd": graph_svd, "graph_standard_scaler": graph_standard, "graph_angle_scaler": graph_angle,
        "qgnn_weights": qgnn.weights,
        "config": {"reps": qgnn.reps, "maxiter": qgnn.maxiter, "seed": SEED},
    }, OUT / "qgnn_model.joblib")

    predictions = []
    for partition, indices in (("validation", validation_idx), ("test", test_idx)):
        pred_vqc = vqc_validation if partition == "validation" else vqc_test
        q_probs = qgnn_validation_probs if partition == "validation" else qgnn_test_probs
        q_labels = qgnn_validation_labels if partition == "validation" else qgnn_test_labels
        c_scores = classical_validation_scores if partition == "validation" else classical_test_scores
        c_labels = classical.predict(vqc_x(indices))
        for pos, source_index in enumerate(indices):
            predictions.append({
                "partition": partition,
                "source_row_index": int(source_index),
                "molecule_chembl_ids": rows[source_index]["molecule_chembl_ids"],
                "canonical_smiles": rows[source_index]["canonical_smiles"],
                "label": int(labels[source_index]),
                "vqc_prediction": int(pred_vqc["predictions"][pos]),
                "vqc_probability_active_uncalibrated": float(pred_vqc["probabilities"][pos][1]),
                "qgnn_prediction": int(q_labels[pos]),
                "qgnn_probability_active_uncalibrated": float(q_probs[pos]),
                "classical_rbf_svm_prediction": int(c_labels[pos]),
                "classical_rbf_svm_score": float(c_scores[pos]),
            })
    with (OUT / "heldout_predictions.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(predictions[0]))
        writer.writeheader()
        writer.writerows(predictions)
    with (OUT / "split_membership.csv").open("w", encoding="utf-8", newline="") as handle:
        fields = ("source_row_index", "molecule_chembl_ids", "canonical_smiles", "murcko_scaffold", "original_partition", "label", "selected_for_training")
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for i, row in enumerate(rows):
            writer.writerow({
                "source_row_index": i,
                "molecule_chembl_ids": row["molecule_chembl_ids"],
                "canonical_smiles": row["canonical_smiles"],
                "murcko_scaffold": saved_scaffolds[i],
                "original_partition": row["split"],
                "label": int(labels[i]) if labels[i] >= 0 else "excluded",
                "selected_for_training": i in set(selected.tolist()),
            })

    metrics = {}
    for name, test_labels, test_scores, val_labels, val_scores in (
        ("vqc", vqc_test_labels, vqc_test_prob,
         np.asarray(vqc_validation["predictions"], dtype=int), np.asarray(vqc_validation["probabilities"])[:, 1]),
        ("qgnn", qgnn_test_labels, qgnn_test_probs, qgnn_validation_labels, qgnn_validation_probs),
        ("classical_rbf_svm", classical.predict(vqc_x(test_idx)), classical_test_scores,
         classical.predict(vqc_x(validation_idx)), classical_validation_scores),
    ):
        metrics[name] = {
            "validation": _metrics(y_validation, val_labels, val_scores),
            "test": _metrics(y_test, test_labels, test_scores),
        }

    results = {
        "status": "completed",
        "experiment": "Same-scaffold-split EGFR activity-proxy VQC/QGNN/classical comparison",
        "artifact_directory": "benchmark_reports/egfr_regression/vqc_qgnn_same_day_v3",
        "dataset": {
            "source": "benchmark_reports/egfr_regression/curated_compounds.csv",
            "label_definition": {"active": "pIC50_min >= 7", "inactive": "pIC50_max <= 6", "excluded": "borderline/discordant or invalid SMILES"},
            "partition_rows": {name: int(len(indices)) for name, indices in partitions.items()},
            "balanced_training_subset_per_class": BALANCED_TRAIN_PER_CLASS,
        },
        "split": {"seed": SEED, "membership": "Existing saved Murcko scaffold-disjoint split; identical training row selection for all three models."},
        "preprocessing": {
            "vqc_and_classical": "2048-bit Morgan radius-2 fingerprints; TruncatedSVD(4), StandardScaler, MinMaxScaler[0,pi], fit on labeled train partition only.",
            "qgnn": "RDKit atom/bond graphs; one weighted message-passing round and mean/max graph readout; TruncatedSVD(4), StandardScaler, MinMaxScaler[0,pi], fit on labeled train partition only.",
        },
        "models": {
            "vqc": {"id": "egfr-vqc-zz-real-amplitudes-v1", "feature_map": "4-qubit ZZFeatureMap; RealAmplitudes reps=1", "loss": "cross_entropy", "optimizer": "COBYLA maxiter=15", "sampler": "StatevectorSampler, 256 shots", "training": vqc_diagnostics},
            "qgnn": {"id": "egfr-qgnn-message-passing-pqc-v1", "graph": "12 atom features, 5 bond features; bond-weighted one-round message passing; tanh; mean/max readout", "circuit": "4-qubit graph-angle RY encoding, trainable RY/RZ ansatz with entangling CNOTs; first-qubit measurement", "loss": "binary cross entropy", "optimizer": "COBYLA maxiter=24", "training": qgnn_diagnostics},
            "classical_rbf_svm": {"id": "egfr-classical-rbf-svm-v1", "configuration": "SVC RBF C=1 gamma=scale class_weight=balanced", "training_runtime_seconds": round(classical_runtime, 6)},
        },
        "metrics": metrics,
        "package_versions": {"python": platform.python_version(), "numpy": np.__version__, "scikit_learn": sklearn.__version__, "rdkit": rdkit.__version__, "qiskit": qiskit.__version__, "qiskit_machine_learning": qiskit_machine_learning.__version__},
        "artifacts": ["vqc_model.joblib", "qgnn_model.joblib", "split_membership.csv", "heldout_predictions.csv"],
        "limitations": [
            "Activity labels are retrospective heuristic biochemical proxies, not experimental confirmation of new compounds.",
            "One fixed scaffold split, a small balanced training subset, and limited optimizer evaluations; no quantum advantage claim.",
            "QGNN is a small hybrid message-passing plus statevector-PQC prototype; readout probabilities are not calibrated.",
        ],
    }
    (OUT / "results.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    return results


if __name__ == "__main__":
    print(json.dumps(run_experiment(), indent=2))
