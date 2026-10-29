"""Read-only API for the saved, held-out EGFR VQC experiment."""

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException


router = APIRouter(prefix="/api/vqc", tags=["Variational Quantum Classifier"])
RESULT_PATH = (
    Path(__file__).resolve().parents[2]
    / "benchmark_reports"
    / "egfr_regression"
    / "vqc_same_day_final"
    / "results.json"
)


@router.get("/egfr")
def get_egfr_vqc_result():
    """Return only the saved completed training artifact; never trains on request."""
    if not RESULT_PATH.is_file():
        raise HTTPException(status_code=404, detail="No completed EGFR VQC run is available.")
    try:
        result = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=500, detail="Saved EGFR VQC result could not be read.") from exc
    if result.get("status") != "completed":
        raise HTTPException(status_code=409, detail="Saved EGFR VQC result is not complete.")
    return result
