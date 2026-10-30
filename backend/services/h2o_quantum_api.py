"""Opt-in API for separate H2O classical, simulator, and fixed-parameter QPU runs."""

import json
import re
import uuid
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from quantum.chemistry.h2o_experiment import (
    _resource_estimates,
    validate_h2o_statevector_record,
    water_configuration,
)
from quantum.chemistry.runtime_mitigation import build_estimator_runtime_options

from backend.services.wsl_quantum_adapter import (
    WSLCalculationError,
    WSLQuantumError,
    WSLTimeoutError,
    wsl_quantum_adapter,
)


router = APIRouter(prefix="/api/quantum-chemistry/h2o", tags=["H2O quantum chemistry"])
RESULTS_DIR = Path(__file__).resolve().parents[2] / "experiments" / "h2o_results"
_RECORD_ID = re.compile(r"^(classical|simulator)-[0-9a-f]{32}$")
DEFAULT_H2O_SIMULATOR_TIMEOUT_SECONDS = 3600


class ClassicalRequest(BaseModel):
    oh_bond_length_angstrom: float = Field(default=0.9572, ge=0.5, le=2.0, allow_inf_nan=False)
    hoh_angle_degrees: float = Field(default=104.5, ge=60.0, le=180.0, allow_inf_nan=False)


class SimulatorRequest(BaseModel):
    classical_record_id: str
    maxiter: int = Field(default=50, ge=1, le=500)
    timeout_seconds: int = Field(default=DEFAULT_H2O_SIMULATOR_TIMEOUT_SECONDS, ge=1, le=14400)


class RuntimeMitigationRequest(BaseModel):
    profile: Literal["runtime_default", "raw", "readout_mitigated", "custom"] = "runtime_default"
    readout_mitigation: bool | None = None
    gate_twirling: bool | None = None
    measurement_twirling: bool | None = None
    dynamical_decoupling: bool | None = None
    zne_mitigation: bool | None = None
    pec_mitigation: bool | None = None
    num_randomizations: int | None = Field(default=None, ge=1, le=10000)
    shots_per_randomization: int | None = Field(default=None, ge=1, le=1000000)
    measure_noise_learning_randomizations: int | None = Field(default=None, ge=1, le=10000)


class HardwareRequest(BaseModel):
    simulator_record_id: str
    backend_name: str = Field(min_length=1, max_length=80)
    precision: float = Field(default=0.05, ge=0.001, le=0.2, allow_inf_nan=False)
    confirm_submission: bool = False
    mitigation_config: RuntimeMitigationRequest = Field(default_factory=RuntimeMitigationRequest)


@router.get("/preflight")
def h2o_preflight():
    """Return configuration and simple qubit/statevector estimates without running chemistry."""
    return {
        "molecule": water_configuration(),
        "electron_count": 10,
        "spatial_orbitals_sto3g_expected": 7,
        "full_hamiltonian": {
            "pauli_term_count": None,
            "status": "not_generated",
            "note": "Measured by full mapping during the classical reference; not predicted by this endpoint.",
        },
        "active_space": {
            "selection": "HOMO-1, HOMO, LUMO, LUMO+1",
            "active_orbital_indices_zero_based": [3, 4, 5, 6],
            "frozen_orbital_indices_zero_based": [0, 1, 2],
            "active_electrons": 4,
            "active_spatial_orbitals": 4,
            "active_particles_alpha_beta": [2, 2],
        },
        "resource_estimates": _resource_estimates(7, 4),
        "warning": "Qubit/statevector estimates do not predict PySCF memory or runtime.",
    }


@router.get("/environment")
def h2o_environment_status():
    """Return safe WSL readiness feedback without paths, stderr, or configuration values."""
    try:
        ready, _diagnostic = wsl_quantum_adapter.is_available()
    except Exception:
        ready = False
    if ready:
        return {"status": "ready", "ready": True, "message": "WSL chemistry environment is ready."}
    return {
        "status": "unavailable",
        "ready": False,
        "message": "WSL chemistry environment is unavailable. Check the backend's WSL configuration and logs.",
    }


def _read_record(record_id: str) -> dict:
    if not _RECORD_ID.fullmatch(record_id or ""):
        raise HTTPException(status_code=422, detail="Invalid experiment record ID.")
    path = RESULTS_DIR / f"{record_id}.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Experiment record was not found.") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=500, detail="Experiment record could not be read.") from exc
    return value


def _save_record(record: dict, prefix: str) -> dict:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    record_id = f"{prefix}-{uuid.uuid4().hex}"
    record["experiment_record_id"] = record_id
    path = RESULTS_DIR / f"{record_id}.json"
    record["saved_record"] = str(path.relative_to(RESULTS_DIR.parents[1]))
    # Exclusive creation avoids replacing any pre-existing experiment record.
    with path.open("x", encoding="utf-8") as output:
        json.dump(record, output, indent=2, allow_nan=False)
        output.write("\n")
    return record


def _run_or_http_error(operation):
    try:
        return operation()
    except WSLTimeoutError as exc:
        timeout_seconds = getattr(exc, "timeout_seconds", None)
        elapsed_seconds = getattr(exc, "elapsed_seconds", None)
        raise HTTPException(
            status_code=504,
            detail={
                "status": "timed_out",
                "error_type": type(exc).__name__,
                "message": "The WSL calculation exceeded its configured timeout. No result record was saved; check backend logs before retrying.",
                "timeout_seconds": timeout_seconds,
                "elapsed_seconds": elapsed_seconds,
            },
        ) from exc
    except WSLQuantumError as exc:
        raise HTTPException(
            status_code=503,
            detail={"status": "unavailable_or_failed", "error_type": type(exc).__name__,
                    "message": "WSL quantum calculation could not be completed."},
        ) from exc


@router.post("/classical")
def run_classical_reference(request: ClassicalRequest):
    """Run RHF/full and active-space references plus Hamiltonian resource audit."""
    result = _run_or_http_error(lambda: wsl_quantum_adapter.run_h2o_classical_reference(
        request.oh_bond_length_angstrom, request.hoh_angle_degrees
    ))
    return _save_record(result, "classical")


@router.post("/simulator")
def run_simulator(request: SimulatorRequest):
    reference = _read_record(request.classical_record_id)
    if reference.get("execution", {}).get("mode") != "classical_reference":
        raise HTTPException(status_code=422, detail="Record is not a completed H2O classical reference.")
    result = _run_or_http_error(lambda: wsl_quantum_adapter.run_h2o_simulator(
        reference, request.maxiter, timeout=request.timeout_seconds
    ))
    return _save_record(result, "simulator")


@router.get("/statevector/{record_id}")
def get_h2o_statevector(record_id: str):
    """Return an ephemeral final statevector reconstructed from a saved completed run."""
    record = _read_record(record_id)
    if record.get("experiment_record_id") != record_id:
        raise HTTPException(status_code=422, detail="Experiment record identity does not match the requested ID.")
    try:
        validate_h2o_statevector_record(record)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    response = _run_or_http_error(lambda: wsl_quantum_adapter.reconstruct_h2o_statevector(record))
    if response.get("experiment_record_id") != record_id or response.get("execution_type") != "ideal_statevector_simulation":
        raise HTTPException(status_code=502, detail="Statevector worker returned an unexpected response.")
    return response


@router.post("/hardware")
def evaluate_hardware(request: HardwareRequest):
    """Explicit fixed-parameter IBM Runtime evaluation; never called implicitly."""
    if request.confirm_submission is not True:
        raise HTTPException(status_code=400, detail="Set confirm_submission=true to explicitly request a hardware job.")
    mitigation_config = request.mitigation_config.model_dump(exclude_none=True)
    try:
        build_estimator_runtime_options(mitigation_config)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    simulator = _read_record(request.simulator_record_id)
    if simulator.get("execution", {}).get("mode") != "simulator":
        raise HTTPException(status_code=422, detail="Record is not a completed H2O simulator experiment.")
    result = _run_or_http_error(lambda: wsl_quantum_adapter.run_h2o_hardware_evaluation(
        simulator, request.backend_name, request.precision, confirm_submission=True,
        mitigation_config=mitigation_config,
    ))
    result["molecule"] = simulator.get("molecule")
    result["execution"] = {
        "mode": "hardware_evaluation_of_fixed_simulator_optimized_parameters",
        "status": result.get("status"),
        "hardware_execution": result.get("status") == "completed",
    }
    return _save_record(result, "hardware")
