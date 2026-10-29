"""Small scaffold-disjoint EGFR VQC/classical classification comparison.

Labels are conservative activity proxies from the existing curated IC50
cohort: active iff every retained measurement has pIC50 >= 7 (minimum >= 7),
inactive iff maximum pIC50 <= 6. Borderline or discordant rows are excluded.
The existing saved train/validation/test scaffold partitions are preserved.
"""

from __future__ import annotations

import csv
import json
import platform
import time
from pathlib import Path

import numpy as np
import qiskit
import qiskit_machine_learning
import rdkit
import sklearn
from rdkit import Chem
from rdkit.Chem.Scaffolds import MurckoScaffold
from sklearn.decomposition import TruncatedSVD
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from sklearn.svm import SVC

from quantum.algorithms.vqc import create_vqc_classifier, fit_vqc, predict_vqc


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "benchmark_reports" / "egfr_regression"
CURATED_PATH = DATA_DIR / "curated_compounds.csv"
FEATURES_PATH = DATA_DIR / "fingerprints_and_targets.npz"
OUTPUT_DIR = DATA_DIR / "vqc_same_day_final"
SEED = 42
N_COMPONENTS = 4
BALANCED_TRAIN_PER_CLASS = 64
VQC_REPS = 1
VQC_MAXITER = 15
SHOTS = 256
ACTIVE_MIN = 7.0
INACTIVE_MAX = 6.0


def _murcko(smiles: str) -> str | None:
    molecule = Chem.MolFromSmiles(smiles)
    if molecule is None:
        return None
    scaffold = MurckoScaffold.GetScaffoldForMol(molecule)
    return Chem.MolToSmiles(scaffold, canonical=True, isomericSmiles=False) if scaffold.GetNumAtoms() else "ACYCLIC::"


def _label(row: dict) -> tuple[int | None, str]:
    minimum = float(row["pIC50_min"])
    maximum = float(row["pIC50_max"])
    if minimum >= ACTIVE_MIN:
        return 1, "active_all_measurements_pIC50_min_ge_7"
    if maximum <= INACTIVE_MAX:
        return 0, "inactive_all_measurements_pIC50_max_le_6"
    return None, "excluded_borderline_or_discordant_measurements"


def _metrics(y_true: np.ndarray, labels: np.ndarray, scores: np.ndarray) -> dict:
    return {
        "sample_count": int(len(y_true)),
        "class_counts": {"inactive": int(np.sum(y_true == 0)), "active": int(np.sum(y_true == 1))},
        "accuracy": float(accuracy_score(y_true, labels)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, labels)),
        "precision_active": float(precision_score(y_true, labels, pos_label=1, zero_division=0)),
        "recall_active": float(recall_score(y_true, labels, pos_label=1, zero_division=0)),
        "f1_active": float(f1_score(y_true, labels, pos_label=1, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_true, scores)),
        "confusion_matrix_inactive_active": confusion_matrix(y_true, labels, labels=[0, 1]).tolist(),
    }


def run_experiment() -> dict:
    if OUTPUT_DIR.exists():
        raise FileExistsError(f"Refusing to overwrite existing VQC artifacts: {OUTPUT_DIR}")

    with np.load(FEATURES_PATH, allow_pickle=False) as archive:
        fingerprints = np.asarray(archive["X"], dtype=np.float32)
        saved_smiles = archive["smiles"].astype(str)
        saved_scaffolds = archive["scaffold_groups"].astype(str)
        saved_splits = archive["splits"].astype(str)
        saved_targets = np.asarray(archive["y"], dtype=float)
    with CURATED_PATH.open(encoding="utf-8", newline="") as handle:
        compounds = list(csv.DictReader(handle))

    if len(compounds) != len(fingerprints):
        raise ValueError("Curated compound rows do not align with saved fingerprint rows.")

    records = []
    excluded_counts: dict[str, int] = {}
    for index, row in enumerate(compounds):
        smiles = row["canonical_smiles"].strip()
        label, label_reason = _label(row)
        scaffold = _murcko(smiles) if smiles else None
        valid = bool(smiles and scaffold is not None)
        if saved_smiles[index] != smiles or saved_splits[index] != row["split"]:
            raise ValueError(f"Saved feature/source identity mismatch at row {index}.")
        if valid and saved_scaffolds[index] != scaffold:
            raise ValueError(f"Saved/recomputed scaffold mismatch at row {index}.")
        included = valid and label is not None
        reason = label_reason if valid else "excluded_invalid_or_blank_smiles"
        if not included:
            excluded_counts[reason] = excluded_counts.get(reason, 0) + 1
        records.append({
            "index": index,
            "smiles": smiles,
            "scaffold": scaffold or "",
            "split": row["split"],
            "label": label if included else None,
            "median_pIC50": float(row["pIC50_median"]),
            "measurement_count": int(row["measurement_count"]),
            "molecule_chembl_ids": row["molecule_chembl_ids"],
            "label_reason": reason,
            "included": included,
        })

    partition_indices = {
        split: np.asarray([r["index"] for r in records if r["split"] == split and r["included"]], dtype=int)
        for split in ("train", "validation", "test")
    }
    partition_groups = {
        split: {records[int(i)]["scaffold"] for i in indices}
        for split, indices in partition_indices.items()
    }
    for left, right in (("train", "validation"), ("train", "test"), ("validation", "test")):
        overlap = partition_groups[left] & partition_groups[right]
        if overlap:
            raise ValueError(f"Scaffold leakage across {left}/{right}: {len(overlap)} groups.")

    y_all = np.asarray([r["label"] if r["label"] is not None else -1 for r in records], dtype=int)
    train_idx = partition_indices["train"]
    validation_idx = partition_indices["validation"]
    test_idx = partition_indices["test"]
    y_train = y_all[train_idx]
    class_rows = {label: train_idx[y_train == label] for label in (0, 1)}
    n_train = min(BALANCED_TRAIN_PER_CLASS, *(len(indices) for indices in class_rows.values()))
    if n_train < 8:
        raise ValueError("Too few examples per class to train a VQC.")
    rng = np.random.default_rng(SEED)
    selected_train = np.sort(np.concatenate([
        rng.choice(class_rows[label], size=n_train, replace=False) for label in (0, 1)
    ]))

    # All dimensionality reduction/scaling is fitted on labeled training rows only.
    svd = TruncatedSVD(n_components=N_COMPONENTS, random_state=SEED)
    svd.fit(fingerprints[train_idx])
    scaler = StandardScaler().fit(svd.transform(fingerprints[train_idx]))
    angle_scaler = MinMaxScaler(feature_range=(0.0, np.pi)).fit(
        scaler.transform(svd.transform(fingerprints[train_idx]))
    )

    def transform(indices: np.ndarray) -> np.ndarray:
        reduced = svd.transform(fingerprints[indices])
        return angle_scaler.transform(scaler.transform(reduced))

    x_train_balanced = transform(selected_train)
    x_validation = transform(validation_idx)
    x_test = transform(test_idx)
    y_train_balanced = y_all[selected_train]
    y_validation = y_all[validation_idx]
    y_test = y_all[test_idx]

    model = create_vqc_classifier(
        feature_dimension=N_COMPONENTS,
        reps=VQC_REPS,
        maxiter=VQC_MAXITER,
        shots=SHOTS,
        seed=SEED,
    )
    train_diagnostics = fit_vqc(model, x_train_balanced, y_train_balanced)
    vqc_validation = predict_vqc(model, x_validation)
    vqc_test = predict_vqc(model, x_test)

    classical = SVC(kernel="rbf", C=1.0, gamma="scale", class_weight="balanced")
    classical_started = time.perf_counter()
    classical.fit(x_train_balanced, y_train_balanced)
    classical_runtime = time.perf_counter() - classical_started
    classical_validation_labels = classical.predict(x_validation)
    classical_test_labels = classical.predict(x_test)
    classical_validation_scores = classical.decision_function(x_validation)
    classical_test_scores = classical.decision_function(x_test)

    vqc_predictions = {"validation": vqc_validation, "test": vqc_test}
    split_data = {
        "validation": (y_validation, validation_idx),
        "test": (y_test, test_idx),
    }
    metrics = {"vqc": {}, "classical_rbf_svm": {}}
    for split, (truth, indices) in split_data.items():
        vqc_result = vqc_predictions[split]
        vqc_prob = np.asarray(vqc_result["probabilities"], dtype=float)[:, 1]
        vqc_labels = np.asarray(vqc_result["predictions"], dtype=int)
        if split == "validation":
            classical_labels, classical_scores = classical_validation_labels, classical_validation_scores
        else:
            classical_labels, classical_scores = classical_test_labels, classical_test_scores
        metrics["vqc"][split] = _metrics(truth, vqc_labels, vqc_prob)
        metrics["classical_rbf_svm"][split] = _metrics(truth, classical_labels, classical_scores)

    OUTPUT_DIR.mkdir(parents=True)
    membership_path = OUTPUT_DIR / "split_membership.csv"
    with membership_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=[
            "source_row_index", "molecule_chembl_ids", "canonical_smiles", "murcko_scaffold",
            "original_partition", "label", "median_pIC50", "measurement_count", "label_reason", "selected_for_training",
        ])
        writer.writeheader()
        selected_set = set(selected_train.tolist())
        for record in records:
            writer.writerow({
                "source_row_index": record["index"],
                "molecule_chembl_ids": record["molecule_chembl_ids"],
                "canonical_smiles": record["smiles"],
                "murcko_scaffold": record["scaffold"],
                "original_partition": record["split"],
                "label": "active" if record["label"] == 1 else "inactive" if record["label"] == 0 else "excluded",
                "median_pIC50": record["median_pIC50"],
                "measurement_count": record["measurement_count"],
                "label_reason": record["label_reason"],
                "selected_for_training": record["index"] in selected_set,
            })

    prediction_path = OUTPUT_DIR / "heldout_predictions.csv"
    with prediction_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=[
            "partition", "source_row_index", "molecule_chembl_ids", "canonical_smiles", "murcko_scaffold",
            "label", "vqc_prediction", "vqc_probability_active", "classical_rbf_svm_prediction", "classical_rbf_svm_score",
        ])
        writer.writeheader()
        for split, (_, indices) in split_data.items():
            vqc_pred = vqc_predictions[split]
            cls_labels = classical_validation_labels if split == "validation" else classical_test_labels
            cls_scores = classical_validation_scores if split == "validation" else classical_test_scores
            for j, index in enumerate(indices):
                record = records[int(index)]
                writer.writerow({
                    "partition": split,
                    "source_row_index": int(index),
                    "molecule_chembl_ids": record["molecule_chembl_ids"],
                    "canonical_smiles": record["smiles"],
                    "murcko_scaffold": record["scaffold"],
                    "label": "active" if y_all[index] == 1 else "inactive",
                    "vqc_prediction": "active" if vqc_pred["predictions"][j] == 1 else "inactive",
                    "vqc_probability_active": float(vqc_pred["probabilities"][j][1]),
                    "classical_rbf_svm_prediction": "active" if cls_labels[j] == 1 else "inactive",
                    "classical_rbf_svm_score": float(cls_scores[j]),
                })

    package_versions = {
        "python": platform.python_version(),
        "numpy": np.__version__,
        "scikit_learn": sklearn.__version__,
        "rdkit": rdkit.__version__,
        "qiskit": qiskit.__version__,
        "qiskit_machine_learning": qiskit_machine_learning.__version__,
    }
    result = {
        "experiment": "EGFR threshold-labeled scaffold-disjoint VQC classification prototype",
        "status": "completed",
        "dataset": {
            "source": "benchmark_reports/egfr_regression/curated_compounds.csv",
            "origin_note": "Heuristically curated ChEMBL biochemical IC50 cohort; labels are derived from aggregated pIC50 ranges, not an independent prospective endpoint.",
            "label_definition": {
                "active": f"pIC50_min >= {ACTIVE_MIN}",
                "inactive": f"pIC50_max <= {INACTIVE_MAX}",
                "excluded": "All borderline or discordant measurement ranges, plus invalid/blank SMILES.",
                "interpretation": "Conservative threshold-based activity class proxy; not clinical efficacy or target engagement.",
            },
            "original_partition_labeled_counts": {
                split: {
                    "active": int(np.sum(y_all[indices] == 1)),
                    "inactive": int(np.sum(y_all[indices] == 0)),
                }
                for split, indices in partition_indices.items()
            },
            "balanced_training_subset_per_class": int(n_train),
            "ambiguous_or_invalid_exclusions": excluded_counts,
        },
        "evaluation": {
            "seed": SEED,
            "split_source": "Existing train/validation/test split in fingerprints_and_targets.npz; documented as Murcko scaffold-disjoint.",
            "scaffold_overlap": {"train_validation": 0, "train_test": 0, "validation_test": 0},
            "labeled_partition_counts": {split: int(len(indices)) for split, indices in partition_indices.items()},
            "preprocessing": {
                "input": "2048-bit Morgan fingerprints, radius 2",
                "reduction": f"TruncatedSVD({N_COMPONENTS}) fitted on labeled training rows only",
                "scaling": "StandardScaler then MinMaxScaler to [0, pi], both fitted on labeled training rows only",
                "same_feature_transform_for_models": True,
            },
            "metrics": metrics,
        },
        "vqc": {
            "implementation": "Qiskit Machine Learning VQC; genuine trainable variational circuit classifier",
            "feature_map": f"ZZFeatureMap({N_COMPONENTS}, reps={VQC_REPS}, linear entanglement)",
            "trainable_ansatz": f"RealAmplitudes({N_COMPONENTS}, reps={VQC_REPS}, linear entanglement)",
            "trainable_parameters": int(model.ansatz.num_parameters),
            "loss": "cross_entropy",
            "optimizer": f"COBYLA(maxiter={VQC_MAXITER})",
            "sampler": f"StatevectorSampler({SHOTS} shots; classical simulation, not quantum hardware)",
            "fit": train_diagnostics,
            "optimizer_objective_history": train_diagnostics["objective_history"],
        },
        "classical_baseline": {
            "model": "sklearn SVC(kernel='rbf', C=1.0, gamma='scale', class_weight='balanced')",
            "training_rows": int(len(selected_train)),
            "runtime_seconds": round(classical_runtime, 6),
        },
        "package_versions": package_versions,
        "artifacts": {
            "split_membership": str(membership_path.relative_to(ROOT)),
            "heldout_predictions": str(prediction_path.relative_to(ROOT)),
        },
        "limitations": [
            "Small prototype; VQC optimizer settings were fixed, not tuned on validation data.",
            "Threshold-derived classes come from a heuristic curated biochemical cohort; label noise and assay heterogeneity remain.",
            "The train subset is class-balanced, whereas held-out partitions retain their natural class ratios.",
            "The circuit runs on a classical statevector sampler and does not demonstrate quantum advantage.",
        ],
    }
    (OUTPUT_DIR / "results.json").write_text(
        json.dumps(result, indent=2, default=lambda value: value.item() if isinstance(value, np.generic) else str(value)),
        encoding="utf-8",
    )
    return result


if __name__ == "__main__":
    print(json.dumps(run_experiment(), indent=2))
