"""Repeated scaffold-aware validation for EGFR classical activity models.

The script recomputes non-isomeric RDKit Murcko scaffolds from curated SMILES,
validates them against the saved scaffold labels, and evaluates Random Forest
and RBF-SVR over repeated GroupShuffleSplit partitions. Quantum kernels are
not constructed or evaluated here.
"""

from __future__ import annotations

import csv
import json
import platform
import statistics
import time
from pathlib import Path
from typing import Any

import numpy as np
import scipy
import sklearn
from rdkit import Chem, rdBase
from rdkit.Chem.Scaffolds import MurckoScaffold
from sklearn.decomposition import TruncatedSVD
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupShuffleSplit
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVR


ROOT = Path("benchmark_reports/egfr_regression")
DATA_PATH = ROOT / "fingerprints_and_targets.npz"
CURATED_PATH = ROOT / "curated_compounds.csv"
PILOT_FEATURES_PATH = ROOT / "quantum_features_16d_pilot.npz"
PILOT_RESULT_PATH = ROOT / "quantum_kernel_16d_pilot_results.json"
LEGACY_COMPARISON_PATH = ROOT / "classical_quantum_comparison_16d_pilot" / "comparison_results.json"
OUT_DIR = ROOT / "scaffold_validation"

SEEDS = (11, 23, 42, 87, 101)
TEST_GROUP_FRACTION = 0.20
VALIDATION_FRACTION_OF_REMAINDER = 0.25
SVR_SVD_COMPONENTS = 128
SVR_C_VALUES = (1.0, 10.0, 100.0)
SVR_EPSILON = 0.2
RF_MIN_SAMPLES_LEAF = (2, 4)
RF_N_ESTIMATORS = 200
RF_MAX_FEATURES = 0.7


def compute_murcko_group(smiles: str) -> str | None:
    """Return the dataset's canonical non-isomeric Murcko scaffold label."""
    if not smiles.strip():
        return None
    molecule = Chem.MolFromSmiles(smiles)
    if molecule is None:
        return None
    scaffold = MurckoScaffold.GetScaffoldForMol(molecule)
    if scaffold.GetNumAtoms() == 0:
        return "ACYCLIC::"
    return Chem.MolToSmiles(scaffold, canonical=True, isomericSmiles=False)


def calculate_metrics(actual: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    return {
        "mae": float(mean_absolute_error(actual, predicted)),
        "rmse": float(np.sqrt(mean_squared_error(actual, predicted))),
        "r2": float(r2_score(actual, predicted)),
    }


def grouped_split(
    row_indices: np.ndarray,
    targets: np.ndarray,
    groups: np.ndarray,
    seed: int,
) -> dict[str, np.ndarray]:
    """Split groups into about 60/20/20 train/validation/test by group count."""
    outer = GroupShuffleSplit(
        n_splits=1, test_size=TEST_GROUP_FRACTION, random_state=seed
    )
    trainval_positions, test_positions = next(
        outer.split(row_indices, targets[row_indices], groups[row_indices])
    )
    trainval_indices = row_indices[trainval_positions]
    test_indices = row_indices[test_positions]

    inner = GroupShuffleSplit(
        n_splits=1,
        test_size=VALIDATION_FRACTION_OF_REMAINDER,
        random_state=seed + 10_000,
    )
    train_positions, validation_positions = next(
        inner.split(
            trainval_indices,
            targets[trainval_indices],
            groups[trainval_indices],
        )
    )
    split = {
        "train": trainval_indices[train_positions],
        "validation": trainval_indices[validation_positions],
        "test": test_indices,
    }
    assert_split_integrity(split, groups)
    return split


def assert_split_integrity(
    split: dict[str, np.ndarray], groups: np.ndarray
) -> None:
    names = ("train", "validation", "test")
    for i, left_name in enumerate(names):
        left = split[left_name]
        if len(np.unique(left)) != len(left):
            raise ValueError(f"Duplicate compound row in {left_name}.")
        left_groups = set(groups[left].tolist())
        for right_name in names[i + 1 :]:
            right = split[right_name]
            if np.intersect1d(left, right).size:
                raise ValueError(f"Compound rows overlap: {left_name}/{right_name}.")
            if left_groups.intersection(groups[right].tolist()):
                raise ValueError(f"Scaffold overlap: {left_name}/{right_name}.")


def fit_svr_preprocessing(
    X: np.ndarray, fit_indices: np.ndarray, transform_indices: np.ndarray, seed: int
) -> tuple[np.ndarray, np.ndarray, float]:
    reducer = TruncatedSVD(
        n_components=SVR_SVD_COMPONENTS, random_state=seed, n_iter=7
    )
    fit_reduced = reducer.fit_transform(X[fit_indices])
    scaler = StandardScaler()
    fit_scaled = scaler.fit_transform(fit_reduced)
    transform_scaled = scaler.transform(reducer.transform(X[transform_indices]))
    return fit_scaled, transform_scaled, float(reducer.explained_variance_ratio_.sum())


def evaluate_one_split(
    seed: int,
    split: dict[str, np.ndarray],
    X: np.ndarray,
    y: np.ndarray,
    groups: np.ndarray,
) -> dict[str, Any]:
    train_idx = split["train"]
    validation_idx = split["validation"]
    test_idx = split["test"]
    fold_start = time.perf_counter()

    # SVR preprocessing is fit only on the training rows during model selection.
    X_svr_train, X_svr_validation, validation_variance = fit_svr_preprocessing(
        X, train_idx, validation_idx, seed
    )
    svr_candidates = []
    for c_value in SVR_C_VALUES:
        estimator = SVR(
            kernel="rbf", C=c_value, epsilon=SVR_EPSILON, gamma="scale"
        )
        estimator.fit(X_svr_train, y[train_idx])
        prediction = estimator.predict(X_svr_validation)
        validation_metrics = calculate_metrics(y[validation_idx], prediction)
        svr_candidates.append(
            {
                "parameters": {
                    "kernel": "rbf",
                    "C": c_value,
                    "epsilon": SVR_EPSILON,
                    "gamma": "scale",
                },
                "validation": validation_metrics,
            }
        )
    selected_svr = min(svr_candidates, key=lambda item: item["validation"]["mae"])

    rf_candidates = []
    for min_leaf in RF_MIN_SAMPLES_LEAF:
        estimator = RandomForestRegressor(
            n_estimators=RF_N_ESTIMATORS,
            min_samples_leaf=min_leaf,
            max_features=RF_MAX_FEATURES,
            random_state=seed,
            n_jobs=-1,
        )
        estimator.fit(X[train_idx], y[train_idx])
        prediction = estimator.predict(X[validation_idx])
        rf_candidates.append(
            {
                "parameters": {
                    "n_estimators": RF_N_ESTIMATORS,
                    "min_samples_leaf": min_leaf,
                    "max_features": RF_MAX_FEATURES,
                    "random_state": seed,
                },
                "validation": calculate_metrics(y[validation_idx], prediction),
            }
        )
    selected_rf = min(rf_candidates, key=lambda item: item["validation"]["mae"])

    # After validation-based selection, refit on train+validation; test remains untouched.
    trainval_idx = np.concatenate([train_idx, validation_idx])
    svr_trainval, svr_test, test_variance = fit_svr_preprocessing(
        X, trainval_idx, test_idx, seed
    )
    final_svr = SVR(
        kernel="rbf",
        C=selected_svr["parameters"]["C"],
        epsilon=SVR_EPSILON,
        gamma="scale",
    )
    final_svr.fit(svr_trainval, y[trainval_idx])
    svr_test_prediction = final_svr.predict(svr_test)

    rf_params = selected_rf["parameters"]
    final_rf = RandomForestRegressor(
        n_estimators=RF_N_ESTIMATORS,
        min_samples_leaf=rf_params["min_samples_leaf"],
        max_features=RF_MAX_FEATURES,
        random_state=seed,
        n_jobs=-1,
    )
    final_rf.fit(X[trainval_idx], y[trainval_idx])
    rf_test_prediction = final_rf.predict(X[test_idx])

    return {
        "seed": seed,
        "split_sizes": {part: int(len(split[part])) for part in split},
        "scaffold_counts": {
            part: int(len(np.unique(groups[split[part]]))) for part in split
        },
        "validation_model_selection": {
            "selection_metric": "validation MAE (minimum); test labels are not used",
            "svr_candidates": svr_candidates,
            "selected_svr_parameters": selected_svr["parameters"],
            "random_forest_candidates": rf_candidates,
            "selected_random_forest_parameters": selected_rf["parameters"],
            "selected_svr_validation_metrics": selected_svr["validation"],
            "selected_random_forest_validation_metrics": selected_rf["validation"],
        },
        "test_metrics": {
            "rbf_svr": calculate_metrics(y[test_idx], svr_test_prediction),
            "random_forest": calculate_metrics(y[test_idx], rf_test_prediction),
        },
        "svr_preprocessing": {
            "model_selection_fit_rows": int(len(train_idx)),
            "final_fit_rows": int(len(trainval_idx)),
            "components": SVR_SVD_COMPONENTS,
            "variance_explained_ratio_sum_train_only": validation_variance,
            "variance_explained_ratio_sum_train_plus_validation": test_variance,
            "scaling": "StandardScaler fitted only on corresponding fit rows",
        },
        "elapsed_seconds": float(time.perf_counter() - fold_start),
    }


def summarise_metrics(folds: list[dict[str, Any]]) -> dict[str, dict[str, dict[str, float]]]:
    summary: dict[str, dict[str, dict[str, float]]] = {}
    for model in ("rbf_svr", "random_forest"):
        summary[model] = {}
        for metric_name in ("mae", "rmse", "r2"):
            values = [fold["test_metrics"][model][metric_name] for fold in folds]
            summary[model][metric_name] = {
                "mean": float(statistics.mean(values)),
                "sample_standard_deviation": float(statistics.stdev(values)),
                "per_split": values,
            }
    return summary


def validate_dataset():
    data = np.load(DATA_PATH, allow_pickle=False)
    X, y = data["X"], data["y"]
    with CURATED_PATH.open(newline="", encoding="utf-8-sig") as handle:
        compounds = list(csv.DictReader(handle))
    if len(compounds) != len(y):
        raise ValueError("Curated CSV and fingerprint archive row counts differ.")
    for i, row in enumerate(compounds):
        if row["canonical_smiles"] != data["smiles"][i]:
            raise ValueError(f"SMILES row-order mismatch at source row {i}.")
        if row["scaffold_group"] != data["scaffold_groups"][i]:
            raise ValueError(f"Scaffold row-order mismatch at source row {i}.")
        if float(row["pIC50_median"]) != float(y[i]):
            raise ValueError(f"Target row-order mismatch at source row {i}.")

    computed_groups: list[str | None] = [
        compute_murcko_group(smiles) for smiles in data["smiles"].tolist()
    ]
    valid = np.array([group is not None for group in computed_groups], dtype=bool)
    valid_indices = np.flatnonzero(valid)
    invalid_indices = np.flatnonzero(~valid)
    computed_array = np.array(
        [computed_groups[index] for index in valid_indices], dtype=str
    )
    mismatch = computed_array != data["scaffold_groups"][valid_indices]
    if mismatch.any():
        examples = [
            {
                "source_row_index": int(valid_indices[pos]),
                "computed": str(computed_array[pos]),
                "saved": str(data["scaffold_groups"][valid_indices[pos]]),
            }
            for pos in np.flatnonzero(mismatch)[:10]
        ]
        raise ValueError(f"RDKit scaffold labels do not match saved labels: {examples}")
    if len(valid_indices) < 100 or len(np.unique(computed_array)) < 2:
        raise ValueError("Too few valid compounds or scaffold groups for validation.")
    return data, compounds, valid_indices, computed_array, invalid_indices


def legacy_quantum_audit(
    data: np.lib.npyio.NpzFile,
    valid_indices: np.ndarray,
    scaffold_groups: np.ndarray,
) -> dict[str, Any]:
    feature_file = np.load(PILOT_FEATURES_PATH, allow_pickle=False)
    pilot_result = json.loads(PILOT_RESULT_PATH.read_text(encoding="utf-8"))
    legacy_comparison = json.loads(LEGACY_COMPARISON_PATH.read_text(encoding="utf-8"))
    rng = np.random.default_rng(42)
    selected: dict[str, np.ndarray] = {}
    for split, requested in (("train", 256), ("validation", 64), ("test", 64)):
        source_split = np.flatnonzero(data["splits"] == split)
        selected[split] = np.sort(
            rng.choice(source_split, size=requested, replace=False)
        )
        if not np.array_equal(
            feature_file[f"{split}_smiles"], data["smiles"][selected[split]]
        ):
            raise ValueError(f"Legacy quantum pilot {split} identities do not align.")
        if not np.array_equal(
            feature_file[f"{split}_y"], data["y"][selected[split]]
        ):
            raise ValueError(f"Legacy quantum pilot {split} targets do not align.")
    if any(index not in set(valid_indices.tolist()) for values in selected.values() for index in values):
        raise ValueError("Legacy quantum pilot contains a compound excluded from scaffold validation.")

    pilot_groups = {
        name: set(scaffold_groups[np.searchsorted(valid_indices, indices)].tolist())
        for name, indices in selected.items()
    }
    for left, right in (("train", "validation"), ("train", "test"), ("validation", "test")):
        if pilot_groups[left] & pilot_groups[right]:
            raise ValueError(f"Legacy quantum pilot has scaffold overlap in {left}/{right}.")

    return {
        "existing_quantum_pilot_can_be_compared_on_its_original_single_split": True,
        "exact_pilot_split_sizes": {name: int(len(indices)) for name, indices in selected.items()},
        "pilot_scaffold_counts": {name: len(value) for name, value in pilot_groups.items()},
        "scaffold_overlap_across_pilot_partitions": False,
        "exact_feature_and_target_alignment_verified": True,
        "saved_quantum_metrics": pilot_result["metrics"],
        "matched_classical_metrics_from_prior_artifact": {
            name: legacy_comparison["results"][name]
            for name in ("classical_rbf_svr_16d", "classical_random_forest_16d")
        },
        "quantum_artifact_availability": {
            "aggregate_validation_and_test_metrics": True,
            "per_compound_quantum_predictions": False,
            "kernel_matrices": False,
            "saved_16d_features": True,
            "saved_feature_memberships": True,
            "saved_landmark_indices": False,
        },
        "cannot_evaluate_on_new_repeated_splits": "The feature archive contains only the old 256/64/64 random-within-original-partition subset. It has no per-compound kernel values or predictions and no transformed features for the new scaffold seeds. Each new split requires refitting SVD/scaling on its training compounds and recomputing the quantum kernel.",
        "pilot_kernel_construction_seconds": pilot_result["quantum_kernel"]["kernel_construction_seconds"],
        "estimated_full_cohort_quantum_cost_seconds_per_split": None,
        "cost_estimate_method": None,
    }


def main() -> None:
    if OUT_DIR.exists():
        raise FileExistsError(f"Refusing to overwrite existing output directory {OUT_DIR}.")
    data, compounds, valid_indices, groups, invalid_indices = validate_dataset()
    X, y = data["X"], data["y"]
    valid_groups_full = np.empty(len(y), dtype=object)
    valid_groups_full[:] = ""
    valid_groups_full[valid_indices] = groups
    row_indices = valid_indices

    folds = []
    splits_by_seed: dict[int, dict[str, np.ndarray]] = {}
    for seed in SEEDS:
        split = grouped_split(row_indices, y, valid_groups_full, seed)
        splits_by_seed[seed] = split
        folds.append(evaluate_one_split(seed, split, X, y, valid_groups_full))
        print(
            f"seed={seed} counts="
            f"{folds[-1]['split_sizes']} test_mae="
            f"SVR:{folds[-1]['test_metrics']['rbf_svr']['mae']:.4f}, "
            f"RF:{folds[-1]['test_metrics']['random_forest']['mae']:.4f}",
            flush=True,
        )

    # Verify the original fixed partition itself is scaffold-disjoint.
    original_group_sets = {
        name: set(valid_groups_full[valid_indices[data["splits"][valid_indices] == name]].tolist())
        for name in ("train", "validation", "test")
    }
    original_scaffold_overlaps = {
        f"{a}_vs_{b}": len(original_group_sets[a] & original_group_sets[b])
        for a, b in (("train", "validation"), ("train", "test"), ("validation", "test"))
    }
    if any(original_scaffold_overlaps.values()):
        raise ValueError(f"Original scaffold partition overlaps: {original_scaffold_overlaps}")

    legacy = legacy_quantum_audit(data, valid_indices, groups)
    pilot_result = json.loads(PILOT_RESULT_PATH.read_text(encoding="utf-8"))
    total_pairs_pilot = (
        pilot_result["split_sizes"]["train"]
        + pilot_result["split_sizes"]["validation"]
        + pilot_result["split_sizes"]["test"]
    ) * pilot_result["quantum_kernel"]["landmarks"] + pilot_result["quantum_kernel"]["landmarks"] ** 2
    total_pairs_full = len(valid_indices) * pilot_result["quantum_kernel"]["landmarks"] + pilot_result["quantum_kernel"]["landmarks"] ** 2
    estimate_per_full_split = (
        pilot_result["quantum_kernel"]["kernel_construction_seconds"]
        * total_pairs_full
        / total_pairs_pilot
    )
    legacy["estimated_full_cohort_quantum_cost_seconds_per_split"] = float(estimate_per_full_split)
    legacy["cost_estimate_method"] = (
        f"Linear extrapolation from {pilot_result['quantum_kernel']['kernel_construction_seconds']:.1f}s "
        f"for {total_pairs_pilot} 4-landmark sample/landmark pairs to {total_pairs_full} pairs "
        "for the full valid cohort. This is an estimate, not a measured runtime."
    )

    OUT_DIR.mkdir(parents=True, exist_ok=False)
    audit_path = OUT_DIR / "split_membership_audit.csv"
    with audit_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "seed",
                "partition",
                "source_row_index",
                "molecule_chembl_ids",
                "canonical_smiles",
                "pIC50_median",
                "murcko_scaffold_id",
            ]
        )
        for seed, split in splits_by_seed.items():
            for partition, indices in split.items():
                for index in indices:
                    row = compounds[int(index)]
                    writer.writerow(
                        [
                            seed,
                            partition,
                            int(index),
                            row["molecule_chembl_ids"],
                            row["canonical_smiles"],
                            float(y[index]),
                            valid_groups_full[index],
                        ]
                    )

    summary = summarise_metrics(folds)
    invalid_rows = [
        {
            "source_row_index": int(index),
            "molecule_chembl_ids": compounds[int(index)]["molecule_chembl_ids"],
            "canonical_smiles": compounds[int(index)]["canonical_smiles"],
            "saved_scaffold_label": compounds[int(index)]["scaffold_group"],
            "exclusion_reason": "Blank or invalid SMILES; RDKit cannot verify a Murcko scaffold.",
        }
        for index in invalid_indices
    ]
    result = {
        "experiment": "Repeated scaffold-aware EGFR activity validation",
        "dataset": {
            "source_npz": str(DATA_PATH),
            "source_curated_csv": str(CURATED_PATH),
            "original_rows": int(len(y)),
            "evaluated_compounds": int(len(valid_indices)),
            "unique_scaffolds": int(len(np.unique(groups))),
            "excluded_compounds": invalid_rows,
            "compound_identity": "Aggregated ChEMBL molecule IDs from curated_compounds.csv; canonical SMILES; pIC50_median.",
        },
        "scaffold_generation": {
            "library": "RDKit MurckoScaffold.GetScaffoldForMol",
            "smiles_parser": "RDKit Chem.MolFromSmiles",
            "canonicalization": "Chem.MolToSmiles(scaffold, canonical=True, isomericSmiles=False)",
            "acyclic_label": "ACYCLIC::",
            "verified_against_saved_scaffold_groups": True,
            "valid_row_mismatches": 0,
            "invalid_smiles_rows": int(len(invalid_indices)),
            "dataset_provenance_note": "The original scaffold-generator source file was not present in the repository; recomputation matched every parseable row exactly.",
        },
        "source_features": {
            "fingerprints": "2048-bit Morgan fingerprints, radius=2, float32 matrix in fingerprints_and_targets.npz",
            "fingerprints_and_targets_npz_arrays": {
                "X": "2996 x 2048 float32 Morgan fingerprint matrix",
                "y": "2996 float64 median pIC50 targets",
                "smiles": "2996 canonical SMILES strings; one is blank",
                "scaffold_groups": "2996 saved Murcko scaffold labels; recomputed and checked for all parseable structures",
                "splits": "2996 original train/validation/test labels",
            },
            "quantum_pilot_npz_arrays": {
                "train_angles": "256 x 16 float32",
                "validation_angles": "64 x 16 float32",
                "test_angles": "64 x 16 float32",
                "split_targets_smiles_scaffolds": "Saved for the same 256/64/64 pilot members",
                "generation": "16-component TruncatedSVD, StandardScaler, and MinMaxScaler to [0, pi], all fitted on the pilot training compounds only",
            },
            "target": "Median pIC50 from retained biochemical IC50 measurements, as described in baseline_results.json.",
            "raw_fingerprint_preprocessing_for_random_forest": "None; Morgan bits are used directly.",
            "rbf_svr_preprocessing": f"TruncatedSVD({SVR_SVD_COMPONENTS}) and StandardScaler; each fitted on current training rows only for selection and train+validation rows only for final test refit.",
        },
        "evaluation_protocol": {
            "method": "Repeated nested GroupShuffleSplit by recomputed Murcko scaffold ID.",
            "seeds": list(SEEDS),
            "test_fraction_of_groups": TEST_GROUP_FRACTION,
            "validation_fraction_of_remaining_groups": VALIDATION_FRACTION_OF_REMAINDER,
            "approximate_group_allocation": "60% train / 20% validation / 20% test; compound counts vary because groups have unequal sizes.",
            "split_integrity": "Each compound and each scaffold occurs in exactly one partition within each seed.",
            "selection_metric": "Validation MAE, separately for each model family and seed.",
            "test_labels_used_for_selection_or_preprocessing": False,
            "random_forest_search": {
                "n_estimators": RF_N_ESTIMATORS,
                "min_samples_leaf": list(RF_MIN_SAMPLES_LEAF),
                "max_features": RF_MAX_FEATURES,
            },
            "rbf_svr_search": {
                "C": list(SVR_C_VALUES),
                "epsilon": SVR_EPSILON,
                "gamma": "scale",
                "input_components": SVR_SVD_COMPONENTS,
            },
            "split_membership_file": str(audit_path),
        },
        "package_versions": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "scikit_learn": sklearn.__version__,
            "rdkit": rdBase.rdkitVersion,
        },
        "original_partition_scaffold_overlap_counts": original_scaffold_overlaps,
        "per_split_results": folds,
        "aggregate_test_metrics": summary,
        "quantum_comparability": legacy,
        "limitations": [
            "Only five scaffold split seeds were evaluated; this is a modest repeated holdout, not an external prospective validation.",
            "The assay cohort was heuristically curated, and scaffold-separated testing is a distribution-shift challenge.",
            "The one blank-SMILES compound cannot be scaffold-verified and was excluded rather than assigned an artificial scaffold.",
            "GroupShuffleSplit targets fractions of scaffold groups, not exact compound fractions; large groups change sample counts.",
            "The RBF-SVR uses a 128D training-only SVD representation; Random Forest uses the full 2048 Morgan bits, so the two classical model pipelines are model-specific.",
            "Existing quantum metrics are directly comparable only on their original single 256/64/64 scaffold-disjoint pilot split; no quantum results exist for the five new splits.",
            "No quantum simulation was run in this task.",
        ],
    }
    (OUT_DIR / "results.json").write_text(json.dumps(result, indent=2), encoding="utf-8")

    lines = [
        "# EGFR Scaffold-Aware Classical Validation",
        "",
        "## Dataset and scaffold audit",
        "",
        f"- {len(y)} curated rows were present; {len(valid_indices)} were evaluated across {len(np.unique(groups))} recomputed Murcko scaffolds.",
        f"- {len(invalid_indices)} row(s) were excluded because the SMILES was blank or invalid, so RDKit could not verify a Murcko scaffold. The excluded identity and reason are recorded in `results.json`.",
        "- RDKit non-isomeric canonical Murcko scaffold IDs matched all parseable saved group labels exactly (0 mismatches). The repository did not contain the original generator source, so this independent recomputation is the provenance verification.",
        "- Compound identities and targets are carried from the curated CSV in `split_membership_audit.csv`; a row can represent multiple aggregated ChEMBL molecule IDs.",
        "- The source archive contains 2048-bit Morgan fingerprints, pIC50 targets, SMILES, saved scaffold groups, and original split labels. The old quantum feature archive contains only 16D train/validation/test angle arrays plus matching targets, SMILES, and scaffold labels for its 256/64/64 pilot; it was generated by training-only TruncatedSVD, StandardScaler, and MinMaxScaler to [0, pi].",
        "",
        "## Repeated scaffold validation",
        "",
        f"Five deterministic seeds were used: {', '.join(str(seed) for seed in SEEDS)}. `GroupShuffleSplit` held out approximately 20% of scaffold groups for test, then 25% of the remaining groups for validation. This yields approximately 60/20/20 by scaffold group; compound counts vary with scaffold sizes.",
        "",
        "Within every seed, group membership and source row indices were checked for train/validation/test separation. Model selection used validation MAE only. Test labels were not used for model selection or preprocessing. Selected models were refit on train+validation before test evaluation.",
        "",
        f"RBF-SVR uses a {SVR_SVD_COMPONENTS}-component TruncatedSVD and StandardScaler fitted only on training rows during selection, then refitted on train+validation. Random Forest uses the original 2048 Morgan bits.",
        "",
        "### Test metrics across seeds (mean ± sample SD)",
        "",
        "| Model | MAE | RMSE | R² |",
        "|---|---:|---:|---:|",
    ]
    for model, label in (("rbf_svr", "RBF-SVR"), ("random_forest", "Random Forest")):
        metrics_summary = summary[model]
        lines.append(
            f"| {label} | {metrics_summary['mae']['mean']:.4f} ± {metrics_summary['mae']['sample_standard_deviation']:.4f} | "
            f"{metrics_summary['rmse']['mean']:.4f} ± {metrics_summary['rmse']['sample_standard_deviation']:.4f} | "
            f"{metrics_summary['r2']['mean']:.4f} ± {metrics_summary['r2']['sample_standard_deviation']:.4f} |"
        )
    lines.extend(["", "### Per-seed outcomes", "", "| Seed | Train n / groups | Validation n / groups | Test n / groups | Selected SVR C | Selected RF min leaf | SVR test MAE | RF test MAE |", "|---:|---:|---:|---:|---:|---:|---:|---:|"])
    for fold in folds:
        counts = fold["split_sizes"]
        groups_count = fold["scaffold_counts"]
        lines.append(
            f"| {fold['seed']} | {counts['train']} / {groups_count['train']} | "
            f"{counts['validation']} / {groups_count['validation']} | {counts['test']} / {groups_count['test']} | "
            f"{fold['validation_model_selection']['selected_svr_parameters']['C']:g} | "
            f"{fold['validation_model_selection']['selected_random_forest_parameters']['min_samples_leaf']} | "
            f"{fold['test_metrics']['rbf_svr']['mae']:.4f} | {fold['test_metrics']['random_forest']['mae']:.4f} |"
        )
    lines.extend(
        [
            "",
            "## Quantum comparability",
            "",
            "The existing quantum pilot can be compared fairly on its original single scaffold-disjoint split: its saved SMILES and targets exactly match 256/64/64 source rows, and recomputed scaffold IDs show no overlap among those partitions. The existing matched single-split comparison is available in `classical_quantum_comparison_16d_pilot/comparison_report.md`.",
            "",
            "It cannot be scored on the five new repeated splits from existing artifacts. Those artifacts contain only the old pilot’s 16D features and aggregate metrics; there are no quantum per-compound predictions or kernel matrices, and each new split requires a new training-only SVD/scaler fit and quantum-kernel computation.",
            "",
            f"The old 384-compound pilot recorded {pilot_result['quantum_kernel']['kernel_construction_seconds']:.1f}s for kernel construction with four landmarks. A linear evaluated-pair extrapolation estimates about {estimate_per_full_split / 3600:.2f} hours per full-cohort split (about {estimate_per_full_split * len(SEEDS) / 3600:.1f} hours for five). This is a rough unmeasured estimate; no quantum work was run.",
            "",
            "Smallest next quantum experiment: run one preselected scaffold-disjoint 256/64/64 sample with four training landmarks, fit the same 16D preprocessing on its 256 training compounds only, save per-compound predictions and kernel artifacts, then compare against classical models on those exact rows. The prior pilot shows this scale took about 19.5 minutes for kernel construction, but that historical time is not a guarantee. Robust comparison across the five full-cohort folds would require recomputing the quantum model for each fold and could take many hours.",
            "",
            "## Limitations",
            "",
            "- Five repeated holdouts provide a limited estimate of split variability; no independent external dataset was used.",
            "- The EGFR biochemical cohort was heuristically curated and is not a clinical endpoint.",
            "- Large scaffold groups cause compound counts to vary across group-based partitions.",
            "- RBF-SVR and Random Forest use different model-appropriate feature pipelines; both avoid held-out test leakage.",
            "- Existing quantum results support only the original matched split; they do not establish a quantum advantage on repeated scaffold validation.",
            "",
            "## Artifacts",
            "",
            "- `results.json`: data provenance, seeds, package versions, per-split and aggregate metrics, and quantum comparability audit.",
            "- `split_membership_audit.csv`: compound IDs, SMILES, target, scaffold ID, and partition for every seed.",
            "- `benchmark_egfr_scaffold_validation.py`: reproducible evaluation script.",
            "",
        ]
    )
    (OUT_DIR / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Saved report: {OUT_DIR / 'report.md'}")
    print(f"Saved results: {OUT_DIR / 'results.json'}")
    print(f"Saved split audit: {audit_path}")


if __name__ == "__main__":
    main()
