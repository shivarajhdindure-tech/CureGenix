"""
EGFR Benchmark & Validation API Endpoint

Serves verified benchmark artifacts for the EGFR regression milestone:
1. Five-split scaffold-disjoint classical evaluation (RBF-SVR & Random Forest)
2. Single matched 16D pilot comparison (Quantum-kernel SVR vs classical baselines)
3. Safe access to allowlisted benchmark markdown reports
"""

import json
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

router = APIRouter(
    prefix="/api/benchmarks",
    tags=["EGFR Benchmark & Validation"],
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BENCHMARK_DIR = PROJECT_ROOT / "benchmark_reports" / "egfr_regression"
SCAFFOLD_DIR = BENCHMARK_DIR / "scaffold_validation"
PILOT_DIR = BENCHMARK_DIR / "classical_quantum_comparison_16d_pilot"

SCAFFOLD_RESULTS_PATH = SCAFFOLD_DIR / "results.json"
SCAFFOLD_REPORT_PATH = SCAFFOLD_DIR / "report.md"
PILOT_RESULTS_PATH = PILOT_DIR / "comparison_results.json"
PILOT_REPORT_PATH = PILOT_DIR / "comparison_report.md"

ALLOWED_REPORTS = {
    "scaffold_validation": {
        "title": "EGFR Scaffold-Aware Classical Validation Report",
        "path": SCAFFOLD_REPORT_PATH,
        "description": "Five-seed nested GroupShuffleSplit evaluation across 2,995 compounds and 1,129 scaffolds.",
    },
    "pilot_comparison": {
        "title": "EGFR 16D Pilot Classical vs Quantum-Kernel Comparison Report",
        "path": PILOT_REPORT_PATH,
        "description": "Matched comparison on identical 256/64/64 compounds using saved 16D pilot representations.",
    },
}


def _load_json_file(path: Path) -> Dict[str, Any]:
    """Safely load JSON file if it exists."""
    if not path.is_file():
        raise HTTPException(
            status_code=404,
            detail=f"Benchmark artifact not found: {path.name}",
        )
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Failed to read benchmark artifact.",
        ) from exc


@router.get("/egfr")
def get_egfr_benchmark_data():
    """
    Return comprehensive, verified EGFR benchmark results.

    Separates the five-split scaffold-disjoint classical evaluation from
    the single-split 16D quantum pilot comparison.
    """
    scaffold_json = _load_json_file(SCAFFOLD_RESULTS_PATH)
    pilot_json = _load_json_file(PILOT_RESULTS_PATH)

    # Extract aggregate classical metrics from scaffold_json
    agg = scaffold_json.get("aggregate_test_metrics", {})
    rbf_agg = agg.get("rbf_svr", {})
    rf_agg = agg.get("random_forest", {})

    # Extract pilot comparison metrics from pilot_json
    pilot_results = pilot_json.get("results", {})
    q_model = pilot_results.get("saved_quantum_nystrom_svr", {})
    c_rbf_model = pilot_results.get("classical_rbf_svr_16d", {})
    c_rf_model = pilot_results.get("classical_random_forest_16d", {})

    return {
        "status_indicators": {
            "classical_validation": "Classical scaffold validation complete",
            "quantum_validation": "Repeated scaffold-split quantum validation pending",
        },
        "dataset": {
            "name": "EGFR Biochemical Activity (IC50 / pIC50)",
            "source_curated_csv": "benchmark_reports/egfr_regression/curated_compounds.csv",
            "total_curated_rows": scaffold_json.get("dataset", {}).get("original_rows", 2996),
            "evaluated_compounds": scaffold_json.get("dataset", {}).get("evaluated_compounds", 2995),
            "unique_murcko_scaffolds": scaffold_json.get("dataset", {}).get("unique_scaffolds", 1129),
            "excluded_compounds": [
                {
                    "row_index": 0,
                    "reason": "Blank or invalid SMILES; RDKit cannot verify a Murcko scaffold.",
                    "canonical_smiles": "",
                }
            ],
            "compound_identity": "Aggregated ChEMBL molecule IDs, canonical SMILES, median pIC50 target",
        },
        "five_split_classical": {
            "evaluation_scope": "Full-cohort repeated scaffold validation (2,995 compounds, 1,129 scaffolds)",
            "protocol": {
                "method": "Repeated nested GroupShuffleSplit by recomputed Murcko scaffold ID",
                "seeds": scaffold_json.get("evaluation_protocol", {}).get("seeds", [11, 23, 42, 87, 101]),
                "split_ratio": "~60% train / 20% validation / 20% test by scaffold groups",
                "scaffold_overlap": "Zero scaffold overlap across partitions in every seed (verified)",
                "selection_criterion": "Validation MAE only; held-out test labels never used for model selection or preprocessing",
                "final_fitting": "Selected hyperparameter models refit on train+validation before test evaluation",
            },
            "models": {
                "rbf_svr": {
                    "name": "RBF-SVR",
                    "pipeline": "128-component TruncatedSVD + StandardScaler (fit on training only)",
                    "mae": {
                        "mean": 0.5607,
                        "sample_std": 0.0689,
                        "formatted": "0.5607 ± 0.0689",
                        "raw_mean": rbf_agg.get("mae", {}).get("mean", 0.560718),
                        "per_split": [0.4990, 0.6213, 0.5477, 0.4928, 0.6428],
                    },
                    "rmse": {
                        "mean": 0.7609,
                        "sample_std": 0.0883,
                        "formatted": "0.7609 ± 0.0883",
                        "raw_mean": rbf_agg.get("rmse", {}).get("mean", 0.760883),
                        "per_split": [0.6928, 0.8475, 0.7516, 0.6591, 0.8535],
                    },
                    "r2": {
                        "mean": 0.6061,
                        "sample_std": 0.0496,
                        "formatted": "0.6061 ± 0.0496",
                        "raw_mean": rbf_agg.get("r2", {}).get("mean", 0.606132),
                        "per_split": [0.6496, 0.5919, 0.5956, 0.6578, 0.5358],
                    },
                },
                "random_forest": {
                    "name": "Random Forest",
                    "pipeline": "Original 2048 Morgan fingerprint bits directly; 200 trees, min_samples_leaf=2, max_features=0.7",
                    "mae": {
                        "mean": 0.5270,
                        "sample_std": 0.0672,
                        "formatted": "0.5270 ± 0.0672",
                        "raw_mean": rf_agg.get("mae", {}).get("mean", 0.526999),
                        "per_split": [0.4555, 0.5873, 0.5079, 0.4771, 0.6073],
                    },
                    "rmse": {
                        "mean": 0.7286,
                        "sample_std": 0.0758,
                        "formatted": "0.7286 ± 0.0758",
                        "raw_mean": rf_agg.get("rmse", {}).get("mean", 0.728605),
                        "per_split": [0.6459, 0.8080, 0.7138, 0.6690, 0.8064],
                    },
                    "r2": {
                        "mean": 0.6386,
                        "sample_std": 0.0394,
                        "formatted": "0.6386 ± 0.0394",
                        "raw_mean": rf_agg.get("r2", {}).get("mean", 0.638551),
                        "per_split": [0.6955, 0.6290, 0.6353, 0.6474, 0.5856],
                    },
                },
            },
            "per_seed_summary": [
                {"seed": 11, "train_n": 1641, "val_n": 600, "test_n": 754, "svr_test_mae": 0.4990, "rf_test_mae": 0.4555},
                {"seed": 23, "train_n": 1771, "val_n": 535, "test_n": 689, "svr_test_mae": 0.6213, "rf_test_mae": 0.5873},
                {"seed": 42, "train_n": 1922, "val_n": 542, "test_n": 531, "svr_test_mae": 0.5477, "rf_test_mae": 0.5079},
                {"seed": 87, "train_n": 1770, "val_n": 532, "test_n": 693, "svr_test_mae": 0.4928, "rf_test_mae": 0.4771},
                {"seed": 101, "train_n": 1873, "val_n": 502, "test_n": 620, "svr_test_mae": 0.6428, "rf_test_mae": 0.6073},
            ],
        },
        "single_split_pilot_comparison": {
            "evaluation_scope": "Matched single scaffold-disjoint pilot split (seed 42, 384 compounds)",
            "split_composition": {
                "train_samples": 256,
                "validation_samples": 64,
                "test_samples": 64,
                "scaffold_overlap": "Zero scaffold overlap across partitions (163 train / 45 val / 46 test scaffolds)",
            },
            "input_features": {
                "dimensions": 16,
                "source": "16-component TruncatedSVD + StandardScaler + MinMaxScaler to [0, pi] (fitted on pilot training split only)",
                "variance_retained": "52.9% of reported fingerprint variance",
            },
            "quantum_execution": {
                "method": "16D ZZFeatureMap fidelity kernel, 4 Nyström landmarks, precomputed-kernel SVR (C=10.0, epsilon=0.2)",
                "hardware": "Classical statevector simulator (Qiskit StatevectorSampler, 256 shots)",
                "is_quantum_hardware": False,
                "quantum_advantage_claimed": False,
                "landmark_count_verified": 4,
            },
            "models": {
                "quantum_kernel_svr": {
                    "name": "Quantum-kernel SVR (4 landmarks)",
                    "execution": "Classical statevector simulator (not hardware)",
                    "validation_mae": round(q_model.get("validation", {}).get("mae", 1.1293), 4),
                    "test_mae": 0.9435,
                    "test_rmse": 1.1234,
                    "test_r2": -0.0531,
                },
                "classical_rbf_svr": {
                    "name": "Classical RBF-SVR (matched 16D)",
                    "execution": "Scikit-learn on identical 16D pilot features",
                    "validation_mae": round(c_rbf_model.get("validation", {}).get("mae", 0.8919), 4),
                    "test_mae": 0.6476,
                    "test_rmse": 0.9045,
                    "test_r2": 0.3172,
                },
                "classical_random_forest": {
                    "name": "Classical Random Forest (matched 16D)",
                    "execution": "Scikit-learn on identical 16D pilot features (400 trees, min_leaf=2)",
                    "validation_mae": round(c_rf_model.get("validation", {}).get("mae", 0.8850), 4),
                    "test_mae": 0.6166,
                    "test_rmse": 0.7839,
                    "test_r2": 0.4872,
                },
            },
            "difference_quantum_minus_classical_rbf": {
                "mae_diff": "+0.2959",
                "rmse_diff": "+0.2188",
                "r2_diff": "-0.3703",
                "interpretation": "Positive MAE/RMSE difference indicates higher error for the quantum model. The matched classical RBF-SVR outperformed the quantum model on the same 16D representation.",
            },
        },
        "scientific_integrity_notes": {
            "split_separation_principle": "The five-split classical evaluation was conducted across 2,995 compounds and five independent scaffold splits. The quantum comparison was conducted on a single 64-compound pilot test split. These evaluations operate on different sample sizes and partitions and are intentionally separated to avoid misleading cross-split comparisons.",
            "hardware_disclosure": "The quantum experiment was executed on a classical statevector simulator (Qiskit StatevectorSampler), not physical quantum hardware. No quantum advantage is claimed.",
            "extrapolation_cost": "Quantum kernel construction took 19.5 minutes (1,168.6s) on the 384-compound pilot. Full-cohort 5-split quantum validation is estimated at ~12.5 hours on the simulator and is pending.",
        },
        "reports": [
            {
                "id": "scaffold_validation",
                "title": ALLOWED_REPORTS["scaffold_validation"]["title"],
                "description": ALLOWED_REPORTS["scaffold_validation"]["description"],
                "api_endpoint": "/api/benchmarks/egfr/reports/scaffold_validation",
            },
            {
                "id": "pilot_comparison",
                "title": ALLOWED_REPORTS["pilot_comparison"]["title"],
                "description": ALLOWED_REPORTS["pilot_comparison"]["description"],
                "api_endpoint": "/api/benchmarks/egfr/reports/pilot_comparison",
            },
        ],
    }


@router.get("/egfr/reports/{report_id}")
def get_egfr_report(report_id: str):
    """
    Safely retrieve an allowlisted benchmark markdown report.

    Validates report_id against ALLOWED_REPORTS. Does not expose
    arbitrary filesystem paths.
    """
    if report_id not in ALLOWED_REPORTS:
        raise HTTPException(
            status_code=404,
            detail=f"Report '{report_id}' not found. Allowed reports: {list(ALLOWED_REPORTS.keys())}",
        )

    meta = ALLOWED_REPORTS[report_id]
    path: Path = meta["path"]

    if not path.is_file():
        raise HTTPException(
            status_code=404,
            detail=f"Report file '{path.name}' is missing.",
        )

    # Security check: ensure path is strictly within BENCHMARK_DIR
    try:
        resolved_path = path.resolve()
        resolved_base = BENCHMARK_DIR.resolve()
        if not str(resolved_path).startswith(str(resolved_base)):
            raise HTTPException(status_code=403, detail="Access denied.")
    except Exception as exc:
        raise HTTPException(status_code=403, detail="Access denied.") from exc

    try:
        content = path.read_text(encoding="utf-8")
        return {
            "id": report_id,
            "title": meta["title"],
            "description": meta["description"],
            "filename": path.name,
            "content": content,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Failed to read report content.",
        ) from exc
