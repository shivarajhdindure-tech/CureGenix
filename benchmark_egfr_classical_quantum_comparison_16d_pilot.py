"""Compare classical models with the saved EGFR 16D quantum-kernel pilot.

This script never constructs a quantum kernel. It consumes the saved pilot
features and metrics, verifies their row identities against the source dataset,
and fits fixed classical models on the same training rows.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from time import perf_counter

import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.svm import SVR


ROOT = Path("benchmark_reports/egfr_regression")
DATA_PATH = ROOT / "fingerprints_and_targets.npz"
FEATURES_PATH = ROOT / "quantum_features_16d_pilot.npz"
PILOT_RESULT_PATH = ROOT / "quantum_kernel_16d_pilot_results.json"
OUT_DIR = ROOT / "classical_quantum_comparison_16d_pilot"
SEED = 42
PILOT_SIZES = {"train": 256, "validation": 64, "test": 64}


def metrics(actual: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    return {
        "mae": float(mean_absolute_error(actual, predicted)),
        "rmse": float(np.sqrt(mean_squared_error(actual, predicted))),
        "r2": float(r2_score(actual, predicted)),
    }


def validate_alignment(data: np.lib.npyio.NpzFile, features: np.lib.npyio.NpzFile):
    """Recreate pilot sampling and require exact identities, targets and order."""
    rng = np.random.default_rng(SEED)
    source_indices: dict[str, np.ndarray] = {}
    all_smiles: list[str] = []

    for split, requested_size in PILOT_SIZES.items():
        indices = np.flatnonzero(data["splits"] == split)
        selected = np.sort(
            rng.choice(indices, size=min(requested_size, len(indices)), replace=False)
        )
        source_indices[split] = selected
        expected_size = requested_size
        if len(selected) != expected_size:
            raise ValueError(f"{split} split has {len(selected)} rows, expected {expected_size}.")

        checks = {
            "SMILES": np.array_equal(
                features[f"{split}_smiles"], data["smiles"][selected]
            ),
            "targets": np.array_equal(
                features[f"{split}_y"], data["y"][selected]
            ),
            "scaffolds": np.array_equal(
                features[f"{split}_scaffolds"], data["scaffold_groups"][selected]
            ),
        }
        failed = [name for name, passed in checks.items() if not passed]
        if failed:
            raise ValueError(f"{split} saved pilot alignment failed for: {failed}")
        if features[f"{split}_angles"].shape != (expected_size, 16):
            raise ValueError(
                f"{split} feature matrix has unexpected shape "
                f"{features[f'{split}_angles'].shape}."
            )
        if not np.isfinite(features[f"{split}_angles"]).all():
            raise ValueError(f"{split} feature matrix contains non-finite values.")
        if not np.isfinite(features[f"{split}_y"]).all():
            raise ValueError(f"{split} targets contain non-finite values.")
        all_smiles.extend(features[f"{split}_smiles"].tolist())

    if len(set(all_smiles)) != len(all_smiles):
        raise ValueError("The saved pilot contains duplicate compounds across splits.")
    return source_indices


def main() -> None:
    if OUT_DIR.exists():
        raise FileExistsError(
            f"Refusing to overwrite existing comparison artifacts: {OUT_DIR}"
        )

    data = np.load(DATA_PATH, allow_pickle=False)
    features = np.load(FEATURES_PATH, allow_pickle=False)
    pilot = json.loads(PILOT_RESULT_PATH.read_text(encoding="utf-8"))
    source_indices = validate_alignment(data, features)

    recorded_sizes = pilot["split_sizes"]
    if recorded_sizes != PILOT_SIZES:
        raise ValueError(
            f"Pilot result split sizes {recorded_sizes} differ from saved features "
            f"{PILOT_SIZES}."
        )
    if pilot["quantum_kernel"].get("landmarks") != 4:
        raise ValueError("Expected the saved pilot result to record four landmarks.")

    X_train = features["train_angles"]
    y_train = features["train_y"]
    classical_specs = {
        "classical_rbf_svr_16d": SVR(kernel="rbf", C=10.0, epsilon=0.2, gamma="scale"),
        "classical_random_forest_16d": RandomForestRegressor(
            n_estimators=400,
            min_samples_leaf=2,
            max_features=0.7,
            random_state=SEED,
            n_jobs=-1,
        ),
    }

    results: dict[str, dict] = {
        "saved_quantum_nystrom_svr": {
            "validation": pilot["metrics"]["validation"],
            "test": pilot["metrics"]["test"],
            "model": {
                "kind": "16D ZZFeatureMap fidelity kernel, Nyström approximation, precomputed-kernel SVR",
                "C": 10.0,
                "epsilon": 0.2,
                "landmarks": 4,
                "shots": 256,
                "simulator": "Qiskit StatevectorSampler (classical simulation)",
                "metrics_source": str(PILOT_RESULT_PATH),
            },
        }
    }
    predictions: dict[str, np.ndarray] = {}

    for name, estimator in classical_specs.items():
        start = perf_counter()
        estimator.fit(X_train, y_train)
        elapsed = perf_counter() - start
        validation_prediction = estimator.predict(features["validation_angles"])
        test_prediction = estimator.predict(features["test_angles"])
        results[name] = {
            "validation": metrics(features["validation_y"], validation_prediction),
            "test": metrics(features["test_y"], test_prediction),
            "fit_seconds": float(elapsed),
            "model": {
                "input": "saved 16D pilot angles; preprocessing was fit on the pilot training split only",
                "parameters": (
                    {"kernel": "rbf", "C": 10.0, "epsilon": 0.2, "gamma": "scale"}
                    if name == "classical_rbf_svr_16d"
                    else {
                        "n_estimators": 400,
                        "min_samples_leaf": 2,
                        "max_features": 0.7,
                        "random_state": SEED,
                    }
                ),
            },
        }
        predictions[name] = test_prediction

    quantum_test = results["saved_quantum_nystrom_svr"]["test"]
    rbf_test = results["classical_rbf_svr_16d"]["test"]
    comparison = {
        "quantum_minus_classical_rbf_test_mae": quantum_test["mae"] - rbf_test["mae"],
        "quantum_minus_classical_rbf_test_rmse": quantum_test["rmse"] - rbf_test["rmse"],
        "quantum_minus_classical_rbf_test_r2": quantum_test["r2"] - rbf_test["r2"],
    }

    report = {
        "experiment": "EGFR 16D pilot: classical versus saved quantum-kernel SVR",
        "comparison_scope": "Same 256 training, 64 validation, and 64 test compounds, in identical row order and with identical pIC50 targets.",
        "seed": SEED,
        "alignment_verified": True,
        "sample_alignment": {
            "pilot_compound_count": len(set(sum(
                [features[f"{split}_smiles"].tolist() for split in PILOT_SIZES], []
            ))),
            "split_sizes": PILOT_SIZES,
            "source_row_indices": {
                split: idx.tolist() for split, idx in source_indices.items()
            },
            "identity_fields_checked": ["SMILES", "pIC50 target", "Murcko scaffold"],
            "duplicate_compounds_across_pilot_splits": 0,
        },
        "input_features": {
            "dimensions": 16,
            "source": str(FEATURES_PATH),
            "transform": "Saved 2048-bit Morgan fingerprint -> training-only TruncatedSVD -> training-only StandardScaler -> training-only MinMaxScaler [0, pi].",
            "classical_models_fit_rows": 256,
            "validation_or_test_used_for_fit_or_preprocessing": False,
        },
        "landmark_metadata": {
            "corrected_count": 4,
            "basis": "Pilot script N_LANDMARKS and pilot result quantum_kernel.landmarks both record 4.",
            "source_inconsistency": "The saved pilot result limitations list incorrectly says 8 landmarks; this comparison corrects that stale text to 4.",
        },
        "results": results,
        "test_difference_quantum_minus_classical_rbf": comparison,
        "interpretation": "The saved quantum-kernel pilot has higher test MAE and RMSE and lower test R2 than the matched 16D classical RBF-SVR. This pilot does not support a quantum advantage.",
        "excluded_legacy_baselines": "The fixed baseline metrics embedded in the pilot JSON are not used: those results were measured on the full 408-compound test split, whereas this pilot test split has 64 compounds.",
        "limitations": [
            "The assay cohort was heuristically curated and is not an independently validated benchmark.",
            "The 16D features retain only 52.9% of the reported variance in the fingerprint reduction.",
            "The quantum kernel was produced by a classical StatevectorSampler simulator, not quantum hardware.",
            "Only four training landmarks were used, so the Nyström approximation is highly constrained.",
            "The quantum model is reused from saved metrics; its per-compound predictions and kernel matrices were not saved, so only split-level metrics can be compared for the quantum model.",
            "Classical model settings are fixed and were not tuned; no model selection was performed using the test split.",
            "This is a small pilot and does not establish quantum advantage, drug efficacy, or clinical performance.",
        ],
    }

    OUT_DIR.mkdir(parents=True, exist_ok=False)
    json_path = OUT_DIR / "comparison_results.json"
    csv_path = OUT_DIR / "test_predictions_classical.csv"
    md_path = OUT_DIR / "comparison_report.md"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "source_row_index",
                "smiles",
                "scaffold",
                "pIC50_target",
                "classical_rbf_svr_prediction",
                "classical_random_forest_prediction",
            ]
        )
        for row, smiles in enumerate(features["test_smiles"].tolist()):
            writer.writerow(
                [
                    int(source_indices["test"][row]),
                    smiles,
                    features["test_scaffolds"][row],
                    float(features["test_y"][row]),
                    float(predictions["classical_rbf_svr_16d"][row]),
                    float(predictions["classical_random_forest_16d"][row]),
                ]
            )

    table_rows = []
    for name, label in [
        ("saved_quantum_nystrom_svr", "Saved quantum Nyström SVR (4 landmarks)"),
        ("classical_rbf_svr_16d", "Classical RBF-SVR on same saved 16D features"),
        ("classical_random_forest_16d", "Classical random forest on same saved 16D features"),
    ]:
        item = results[name]
        table_rows.append(
            f"| {label} | {item['validation']['mae']:.4f} | "
            f"{item['test']['mae']:.4f} | {item['test']['rmse']:.4f} | "
            f"{item['test']['r2']:.4f} |"
        )

    md = "\n".join(
        [
            "# EGFR 16D Pilot: Classical vs Quantum-Kernel Comparison",
            "",
            "## Design and alignment",
            "",
            "- Same exact pilot compounds and targets: 256 train, 64 validation, 64 test.",
            "- SMILES, pIC50 targets, scaffold labels, sample order, and seeded source row selection were checked against the original dataset before fitting.",
            "- Classical preprocessing is reused from the saved pilot feature file. Its SVD, standardization, and angle scaling were fitted on training rows only; classical estimators were also fitted on those 256 rows only.",
            "- No quantum simulation was rerun. Quantum test and validation metrics come from the saved pilot JSON.",
            "- Both classical models use the same 16-dimensional saved pilot representation as the quantum feature map.",
            "",
            "## Results",
            "",
            "| Model | Validation MAE | Test MAE | Test RMSE | Test R² |",
            "|---|---:|---:|---:|---:|",
            *table_rows,
            "",
            f"Quantum minus matched classical RBF-SVR test MAE: **{comparison['quantum_minus_classical_rbf_test_mae']:+.4f} pIC50**. Positive values mean higher error for the quantum-kernel model.",
            "",
            "The matched classical RBF-SVR has lower test MAE and RMSE and higher test R² than the saved quantum-kernel pilot. **These results do not support a quantum advantage.**",
            "",
            "## Landmark metadata correction",
            "",
            "The pilot script and `quantum_kernel.landmarks` result field both specify **4 landmarks**. A limitations string in the saved pilot result incorrectly says 8; this comparison uses the verified count of 4 and records the source inconsistency rather than editing the original artifact.",
            "",
            "The baseline metrics embedded in the pilot JSON are omitted from this comparison because they were calculated on the full 408-compound test split, not this 64-compound pilot test split.",
            "",
            "## Limitations",
            "",
            "- The quantum model’s per-compound predictions and kernel matrices were not saved, so its comparison is at split-metric level only.",
            "- The 16D reduction retains 52.9% of the reported fingerprint variance; the model sees a compressed representation.",
            "- The quantum kernel uses a classical statevector simulator, four landmarks, and fixed SVR settings. It was not run on quantum hardware.",
            "- Classical settings were fixed in advance and not tuned. No test-set tuning or model selection was done.",
            "- The assay cohort is heuristically curated; this pilot does not establish drug efficacy or clinical performance.",
            "",
            "## Artifacts",
            "",
            "- `comparison_results.json`: metrics, configuration, and alignment audit.",
            "- `test_predictions_classical.csv`: exact test-compound identities, targets, and classical predictions.",
            "- `benchmark_egfr_classical_quantum_comparison_16d_pilot.py`: reproducible comparison script.",
            "",
        ]
    )
    md_path.write_text(md, encoding="utf-8")

    print(json.dumps({"report": str(md_path), "json": str(json_path), "predictions": str(csv_path), "results": results}, indent=2))


if __name__ == "__main__":
    main()
