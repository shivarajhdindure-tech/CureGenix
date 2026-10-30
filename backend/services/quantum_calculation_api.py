"""Explicit asynchronous molecular VQE jobs for candidate Evidence Passports."""

from __future__ import annotations

import hashlib
import json
import logging
import re
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger("curegenix.quantum.jobs")
router = APIRouter(prefix="/api/quantum-calculations", tags=["Molecular quantum calculations"])
RESULTS_DIR = Path(__file__).resolve().parents[2] / "experiments" / "molecular_calculations"
JOB_ID_PATTERN = re.compile(r"^molecular-[0-9a-f]{32}$")

_lock = threading.RLock()
_jobs: dict[str, dict[str, Any]] = {}
_active_fingerprints: dict[str, str] = {}


class QuantumCalculationRequest(BaseModel):
    candidate_id: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_.-]+$")
    smiles: str = Field(min_length=1, max_length=2000)
    basis: str = Field(default="sto3g", min_length=1, max_length=40)
    maxiter: int = Field(default=50, ge=1, le=1000)
    charge: int = Field(default=0, ge=-10, le=10)
    spin: int = Field(default=0, ge=0, le=10)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _job_path(job_id: str) -> Path:
    if not JOB_ID_PATTERN.fullmatch(job_id or ""):
        raise HTTPException(status_code=422, detail="Invalid quantum calculation job ID.")
    return RESULTS_DIR / f"{job_id}.json"


def _persist(job: dict[str, Any]) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    path = _job_path(job["job_id"])
    temporary = path.with_suffix(f".{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("x", encoding="utf-8") as handle:
            json.dump(job, handle, indent=2, allow_nan=False)
            handle.write("\n")
        # Job IDs are unique; atomic replacement only updates this job's record.
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def _safe_failure(exc: Exception) -> dict[str, Any]:
    from backend.services.wsl_quantum_adapter import (
        WSLResourceError, WSLServiceError, WSLTimeoutError,
    )

    if isinstance(exc, WSLTimeoutError):
        message = "The chemistry calculation exceeded its configured timeout. Check backend diagnostics before retrying."
    elif isinstance(exc, WSLResourceError):
        message = "The chemistry worker was terminated, possibly by memory pressure. The calculation was not retried; check backend diagnostics."
    elif isinstance(exc, WSLServiceError):
        message = "The WSL chemistry service could not start after its bounded retry. Check WSL readiness and backend diagnostics."
    else:
        message = "The chemistry calculation failed. Review the backend log entry for its diagnostic details."
    return {
        "status": "failed",
        "message": message,
        "error_type": type(exc).__name__,
        "failed_stage": getattr(exc, "failed_stage", None),
        "stage_diagnostics": getattr(exc, "stage_diagnostics", {}),
    }


def _execute_job(job_id: str) -> None:
    with _lock:
        job = _jobs.get(job_id)
        if not job or job["status"] != "queued":
            return
        job["status"] = "running"
        job["started_at"] = _utc_now()

    started = time.perf_counter()
    try:
        with _lock:
            _persist(job)
        logger.info("Quantum job %s started for candidate %s (molecule preparation and resource preflight).", job_id, job["candidate_id"])
        from quantum.chemistry.quantum_analysis import analyze_smiles

        result = analyze_smiles(
            smiles=job["smiles"], basis=job["basis"], maxiter=job["maxiter"],
            charge=job["charge"], spin=job["spin"],
        )
        result_status = result.get("status")
        if result_status == "success":
            terminal_status = "completed"
        elif result_status == "skipped_resource_limit":
            terminal_status = "skipped"
        else:
            raise RuntimeError("Chemistry pipeline returned without a recognized terminal status.")
        result.setdefault("elapsed_seconds", round(time.perf_counter() - started, 3))
        stages = result.get("stage_diagnostics", {})
        if isinstance(stages, dict):
            for stage_name, details in stages.items():
                if isinstance(details, dict):
                    logger.info("Quantum job %s stage %s: %s (%.3fs).", job_id, stage_name, details.get("status", "unknown"), float(details.get("elapsed_seconds", 0)))
        with _lock:
            job.update({"status": terminal_status, "result": result, "finished_at": _utc_now(),
                        "elapsed_seconds": round(time.perf_counter() - started, 3)})
            _persist(job)
        logger.info("Quantum job %s ended with status=%s after %.3fs.", job_id, terminal_status, job["elapsed_seconds"])
    except Exception as exc:
        elapsed = round(time.perf_counter() - started, 3)
        outcome = _safe_failure(exc)
        with _lock:
            job.update({"status": "failed", "result": outcome, "finished_at": _utc_now(), "elapsed_seconds": elapsed})
            _persist(job)
        logger.exception("Quantum job %s failed after %.3fs (%s).", job_id, elapsed, type(exc).__name__)
    finally:
        fingerprint = job.get("request_fingerprint")
        with _lock:
            if fingerprint and _active_fingerprints.get(fingerprint) == job_id:
                _active_fingerprints.pop(fingerprint, None)


@router.post("", status_code=202)
def submit_quantum_calculation(request: QuantumCalculationRequest, background_tasks: BackgroundTasks):
    """Queue one explicit calculation; no work runs when this endpoint is not called."""
    # A candidate cannot be submitted again while its calculation is active,
    # even if a caller changes a non-identity calculation option meanwhile.
    fingerprint = hashlib.sha256(f"{request.candidate_id}\0{request.smiles}".encode()).hexdigest()
    with _lock:
        existing_id = _active_fingerprints.get(fingerprint)
        if existing_id:
            existing = _jobs.get(existing_id)
            if existing and existing.get("status") in {"queued", "running"}:
                return {"job_id": existing_id, "status": existing["status"], "duplicate": True}
        job_id = f"molecular-{uuid.uuid4().hex}"
        job = {
            "job_id": job_id, "experiment_record_id": job_id, "candidate_id": request.candidate_id,
            "smiles": request.smiles, "input_sha256": hashlib.sha256(request.smiles.encode()).hexdigest(),
            "basis": request.basis, "maxiter": request.maxiter, "charge": request.charge,
            "spin": request.spin, "status": "queued", "submitted_at": _utc_now(),
            "request_fingerprint": fingerprint,
        }
        _persist(job)
        _jobs[job_id] = job
        _active_fingerprints[fingerprint] = job_id
    background_tasks.add_task(_execute_job, job_id)
    logger.info("Quantum job %s queued for explicit candidate request.", job_id)
    return {"job_id": job_id, "status": "queued", "duplicate": False}


@router.get("/{job_id}")
def get_quantum_calculation(job_id: str):
    """Return the real persisted lifecycle state and any terminal result."""
    path = _job_path(job_id)
    with _lock:
        job = _jobs.get(job_id)
        if job is not None:
            return {key: value for key, value in job.items() if key != "request_fingerprint"}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Quantum calculation job was not found.") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=500, detail="Quantum calculation record could not be read.") from exc
    return {key: item for key, item in value.items() if key != "request_fingerprint"}
