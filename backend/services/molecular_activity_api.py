"""Offline-trained EGFR activity-proxy inference for VQC and molecular QGNN."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
import time

import joblib
import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from rdkit import Chem, DataStructs
from rdkit.Chem import rdFingerprintGenerator

from quantum.algorithms.qgnn import MolecularQGNN, graph_message_passing, molecular_graph_from_mol
from quantum.algorithms.vqc import create_vqc_classifier, predict_vqc, restore_vqc_weights


router = APIRouter(prefix="/api/molecular-activity", tags=["Molecular activity proxy"])
ARTIFACT_DIR = Path(__file__).resolve().parents[2] / "benchmark_reports" / "egfr_regression" / "vqc_qgnn_same_day_v3"
RESULT_PATH = ARTIFACT_DIR / "results.json"
VQC_PATH = ARTIFACT_DIR / "vqc_model.joblib"
QGNN_PATH = ARTIFACT_DIR / "qgnn_model.joblib"
MORGAN = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
ENDPOINT = "EGFR retrospective biochemical activity-proxy classification"


class SmilesRequest(BaseModel):
    smiles: str = Field(min_length=1, max_length=5000)


@lru_cache(maxsize=1)
def _load_vqc_bundle():
    if not VQC_PATH.is_file():
        raise FileNotFoundError("No offline-trained VQC artifact is installed")
    return joblib.load(VQC_PATH)


@lru_cache(maxsize=1)
def _load_qgnn_bundle():
    if not QGNN_PATH.is_file():
        raise FileNotFoundError("No offline-trained QGNN artifact is installed")
    return joblib.load(QGNN_PATH)


def _not_trained(model_id: str, reason: str) -> dict:
    return {"status": "not_trained", "model_id": model_id, "endpoint": ENDPOINT, "reason": reason}


def _failed(model_id: str, started: float, exc: Exception) -> dict:
    return {
        "status": "failed", "model_id": model_id, "endpoint": ENDPOINT,
        "runtime_seconds": round(time.perf_counter() - started, 6),
        "reason": f"{type(exc).__name__}: {exc}",
    }


def predict_for_smiles(smiles: str) -> dict:
    """Validate once, then independently run whatever offline models are available."""
    molecule = Chem.MolFromSmiles(smiles)
    if molecule is None:
        raise ValueError("Invalid SMILES")
    canonical = Chem.MolToSmiles(molecule, canonical=True)
    models = {}

    started = time.perf_counter()
    try:
        bundle = _load_vqc_bundle()
        fp = MORGAN.GetFingerprint(molecule)
        values = np.zeros((1, 2048), dtype=np.float32)
        DataStructs.ConvertToNumpyArray(fp, values[0])
        reduced = bundle["svd"].transform(values)
        scaled = bundle["angle_scaler"].transform(bundle["standard_scaler"].transform(reduced))
        config = bundle["config"]
        model = create_vqc_classifier(**config)
        restore_vqc_weights(model, bundle["vqc_weights"])
        result = predict_vqc(model, scaled)
        probability = float(result["probabilities"][0][1])
        models["vqc"] = {
            "status": "success", "model_id": bundle["model_id"], "endpoint": ENDPOINT,
            "prediction": "active_proxy" if probability >= 0.5 else "inactive_proxy",
            "probability_active": probability, "probability_calibrated": False,
            "runtime_seconds": round(time.perf_counter() - started, 6),
        }
    except FileNotFoundError as exc:
        models["vqc"] = _not_trained("egfr-vqc-zz-real-amplitudes-v1", str(exc))
    except Exception as exc:  # independent path; QGNN must still be attempted
        models["vqc"] = _failed("egfr-vqc-zz-real-amplitudes-v1", started, exc)

    started = time.perf_counter()
    try:
        bundle = _load_qgnn_bundle()
        graph = molecular_graph_from_mol(molecule)
        graph_vector = graph_message_passing(graph).reshape(1, -1)
        reduced = bundle["graph_svd"].transform(graph_vector)
        scaled = bundle["graph_angle_scaler"].transform(
            bundle["graph_standard_scaler"].transform(reduced)
        )
        config = bundle["config"]
        model = MolecularQGNN(**config)
        model.weights = np.asarray(bundle["qgnn_weights"], dtype=float)
        probability = float(model.predict_proba(scaled)[0, 1])
        models["qgnn"] = {
            "status": "success", "model_id": bundle["model_id"], "endpoint": ENDPOINT,
            "prediction": "active_proxy" if probability >= 0.5 else "inactive_proxy",
            "probability_active": probability, "probability_calibrated": False,
            "runtime_seconds": round(time.perf_counter() - started, 6),
        }
    except FileNotFoundError as exc:
        models["qgnn"] = _not_trained("egfr-qgnn-message-passing-pqc-v1", str(exc))
    except Exception as exc:
        models["qgnn"] = _failed("egfr-qgnn-message-passing-pqc-v1", started, exc)

    models["classical_rbf_svm"] = {
        "status": "evaluation_only",
        "model_id": "egfr-classical-rbf-svm-v1",
        "endpoint": ENDPOINT,
        "reason": "Included as the held-out comparison baseline; no saved single-molecule inference estimator is available.",
    }

    return {
        "canonical_smiles": canonical,
        "endpoint": ENDPOINT,
        "disclaimer": "Retrospective threshold-derived activity proxy only; not experimental activity, binding affinity, efficacy, or safety. Model outputs are uncalibrated.",
        "models": models,
    }


@router.post("/predict")
def predict_molecular_activity(request: SmilesRequest):
    try:
        return predict_for_smiles(request.smiles)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/egfr")
def get_egfr_activity_experiment():
    """Return saved evaluation metadata only; never train during an API request."""
    if not RESULT_PATH.is_file():
        raise HTTPException(status_code=404, detail="No offline-trained VQC/QGNN evaluation is available.")
    try:
        payload = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=500, detail="Saved evaluation could not be read.") from exc
    if payload.get("status") != "completed":
        raise HTTPException(status_code=409, detail="Saved evaluation is incomplete.")
    return payload
