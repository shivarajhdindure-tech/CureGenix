"""
WSL Quantum Calculation Worker

Standalone execution worker that runs inside the Linux WSL virtual environment
(~/curegenix-quantum/.venv) where PySCF and Qiskit Nature are installed.

Communicates with the Windows host via structured JSON over stdin / stdout.
Never writes non-JSON text to stdout.
"""

import sys
import os
import json
import time
import traceback
from typing import Any, Dict
# Ensure repository root is on sys.path when running inside WSL
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.services.quantum_resource_policy import assess_geometry_resources


def _run_smoke_test(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run a minimal H2 PySCF calculation to verify PySCF convergence.
    """
    import pyscf
    from pyscf import gto, scf

    basis = payload.get("basis", "sto-3g")
    atom = payload.get("atom", "H 0.0 0.0 0.0; H 0.0 0.0 0.74")

    mol = gto.Mole()
    mol.atom = atom
    mol.basis = basis
    mol.verbose = 0
    mol.build()

    mf = scf.RHF(mol)
    mf.verbose = 0
    scf_energy = mf.kernel()

    converged = bool(getattr(mf, "converged", True))

    return {
        "status": "success",
        "action": "smoke_test",
        "pyscf_version": getattr(pyscf, "__version__", "unknown"),
        "basis": basis,
        "scf_energy_hartree": float(scf_energy),
        "converged": converged,
    }


def _run_timed_stage(stage: str, diagnostics: dict, function, *args, **kwargs):
    """Run a worker stage and retain bounded timing/status metadata on failure."""
    started = time.perf_counter()
    try:
        value = function(*args, **kwargs)
    except Exception as exc:
        diagnostics[stage] = {"status": "failed", "elapsed_seconds": round(time.perf_counter() - started, 3)}
        exc.worker_stage = stage
        exc.stage_diagnostics = dict(diagnostics)
        raise
    diagnostics[stage] = {"status": "completed", "elapsed_seconds": round(time.perf_counter() - started, 3)}
    return value


def _run_molecular_analysis(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute full electronic structure + active space + VQE calculation.
    Reuses existing CureGenix quantum modules.
    """
    total_start = time.perf_counter()
    atom = payload.get("atom")
    if not atom or not isinstance(atom, str):
        raise ValueError("Missing or invalid 'atom' geometry string.")

    basis = payload.get("basis", "sto3g")
    charge = int(payload.get("charge", 0))
    spin = int(payload.get("spin", 0))
    maxiter = int(payload.get("maxiter", 50))
    benchmark = bool(payload.get("benchmark", False))

    if maxiter < 1 or maxiter > 1000:
        raise ValueError(f"maxiter must be between 1 and 1000 (got {maxiter})")

    preflight_start = time.perf_counter()
    eligibility = assess_geometry_resources(
        atom, basis=basis, maxiter=maxiter, charge=charge, benchmark=benchmark
    )
    preflight_seconds = round(time.perf_counter() - preflight_start, 3)
    if eligibility.get("status") == "skipped_resource_limit":
        reasons = eligibility.get("reasons", [])
        return {
            "status": "skipped_resource_limit",
            "action": "analyze_molecule",
            "result": {
                "status": "skipped_resource_limit",
                "message": "Quantum calculation skipped before PySCF setup: " + "; ".join(reasons) + " Use a smaller supported molecule or a separately resource-validated environment; this policy is not overridden by manual retry.",
                "resource_eligibility": eligibility,
                "stage_diagnostics": {
                    "resource_preflight": {"status": "completed", "elapsed_seconds": preflight_seconds},
                    "total_elapsed_seconds": preflight_seconds,
                },
            },
        }
    if eligibility.get("status") == "invalid_input":
        raise ValueError("Malformed molecular geometry; resource preflight could not be evaluated.")
    if eligibility.get("status") != "eligible":
        raise ValueError("Quantum resource policy error: " + "; ".join(eligibility.get("reasons", [])))

    from quantum.chemistry.molecule import build_molecular_problem
    from quantum.chemistry.active_space import reduce_to_active_space
    from quantum.chemistry.hamiltonian import build_qubit_hamiltonian, interpret_vqe_energy
    from quantum.algorithms.vqe import run_vqe

    stage_diagnostics = {
        "resource_preflight": {"status": "completed", "elapsed_seconds": preflight_seconds},
    }

    # 1. Build molecular problem via PySCFDriver in Qiskit Nature
    problem = _run_timed_stage("pyscf_driver", stage_diagnostics, build_molecular_problem,
        atom=atom,
        basis=basis,
        charge=charge,
        spin=spin,
    )

    orbital_energies = problem.orbital_energies
    num_spatial_orbitals = problem.num_spatial_orbitals

    # 2. Select HOMO/LUMO orbitals
    alpha_electrons, beta_electrons = problem.num_particles
    total_electrons = alpha_electrons + beta_electrons
    occupied_orbitals = total_electrons // 2

    homo_index = occupied_orbitals - 1
    lumo_index = homo_index + 1

    if homo_index < 0 or lumo_index >= num_spatial_orbitals:
        raise ValueError(
            f"HOMO/LUMO indices ({homo_index}, {lumo_index}) outside available "
            f"orbital range (0..{num_spatial_orbitals - 1})."
        )

    active_orbitals = [homo_index, lumo_index]

    # 3. Active-space reduction
    active_problem = _run_timed_stage("active_space_reduction", stage_diagnostics, reduce_to_active_space,
        problem,
        num_electrons=2,
        num_spatial_orbitals=2,
        active_orbitals=active_orbitals,
    )

    # 4. Qubit Hamiltonian mapping
    qubit_hamiltonian = _run_timed_stage(
        "hamiltonian_mapping", stage_diagnostics, build_qubit_hamiltonian, active_problem
    )

    # 5. VQE execution
    vqe_result = _run_timed_stage(
        "vqe", stage_diagnostics, run_vqe,
        qubit_hamiltonian,
        num_qubits=qubit_hamiltonian.num_qubits,
        maxiter=maxiter,
    )
    vqe_runtime_seconds = stage_diagnostics["vqe"]["elapsed_seconds"]
    energy_components = interpret_vqe_energy(
        float(vqe_result["electronic_energy"]), active_problem
    )

    homo_energy = float(orbital_energies[homo_index])
    lumo_energy = float(orbital_energies[lumo_index])

    response = {
        "status": "success",
        "method": "VQE",
        "basis": basis,
        "charge": charge,
        "spin": spin,
        "active_space": {
            "electrons": 2,
            "spatial_orbitals": 2,
            "selected_orbitals": active_orbitals,
            "selection_method": "HOMO-LUMO",
        },
        "molecular_system": {
            "total_electrons": total_electrons,
            "spatial_orbitals": num_spatial_orbitals,
            "spin_orbitals": num_spatial_orbitals * 2,
        },
        "homo": {
            "orbital": homo_index,
            "energy_hartree": homo_energy,
        },
        "lumo": {
            "orbital": lumo_index,
            "energy_hartree": lumo_energy,
        },
        "homo_lumo_gap_hartree": lumo_energy - homo_energy,
        "hamiltonian": {
            "qubits": qubit_hamiltonian.num_qubits,
            "pauli_terms": len(qubit_hamiltonian),
            "mapping": "Jordan-Wigner",
        },
        "vqe": {
            "electronic_energy_hartree": energy_components["electronic_energy"],
            "raw_active_space_energy_hartree": energy_components["raw_active_space_energy"],
            "total_molecular_energy_hartree": energy_components["total_molecular_energy"],
            "active_space_correction_hartree": energy_components["active_space_correction"],
            "nuclear_repulsion_energy_hartree": energy_components["nuclear_repulsion_energy"],
            "optimizer": vqe_result.get("optimizer", "SLSQP"),
            "ansatz": vqe_result.get("ansatz", "n_local"),
            "max_iterations": maxiter,
            "runtime_seconds": float(vqe_runtime_seconds),
            "optimizer_success": vqe_result.get("optimizer_success"),
            "optimizer_message": vqe_result.get("optimizer_message"),
            "optimizer_status_available": vqe_result.get("optimizer_status_available", False),
        },
        "stage_diagnostics": stage_diagnostics,
    }

    # 6. Optional exact reference solver
    if benchmark:
        from quantum.algorithms.exact_solver import run_exact_solver

        exact_result = _run_timed_stage(
            "exact_reference", stage_diagnostics, run_exact_solver, qubit_hamiltonian
        )
        exact_runtime_seconds = stage_diagnostics["exact_reference"]["elapsed_seconds"]

        vqe_energy = float(vqe_result["electronic_energy"])
        exact_energy = float(exact_result["exact_energy_hartree"])
        absolute_error = abs(vqe_energy - exact_energy)
        relative_error = (
            absolute_error / abs(exact_energy)
            if abs(exact_energy) > 1e-12
            else None
        )

        response["exact_reference"] = {
            "energy_hartree": exact_energy,
            "electronic_energy_hartree": exact_energy + energy_components["active_space_correction"],
            "total_molecular_energy_hartree": exact_energy + energy_components["active_space_correction"] + energy_components["nuclear_repulsion_energy"],
            "method": "Full-Hamiltonian exact diagonalization",
            "runtime_seconds": exact_runtime_seconds,
            "interpretation": (
                "Minimum eigenvalue of the qubit Hamiltonian; "
                "physical particle-number and spin sector not independently verified."
            ),
        }
        response["benchmark"] = {
            "absolute_error_hartree": absolute_error,
            "relative_error": relative_error,
            "relative_error_percent": (
                relative_error * 100 if relative_error is not None else None
            ),
        }

    stage_diagnostics["total_elapsed_seconds"] = round(time.perf_counter() - total_start, 3)
    return {
        "status": "success",
        "action": "analyze_molecule",
        "result": response,
    }


def _run_h2o_classical(payload: Dict[str, Any]) -> Dict[str, Any]:
    from quantum.chemistry.h2o_experiment import run_h2o_classical_reference, water_configuration

    configuration = payload.get("configuration") or water_configuration(
        payload.get("oh_bond_length_angstrom", 0.9572),
        payload.get("hoh_angle_degrees", 104.5),
    )
    record = run_h2o_classical_reference(configuration)
    return {"status": "success", "action": "h2o_classical_reference", "result": record}


def _run_h2o_simulator(payload: Dict[str, Any]) -> Dict[str, Any]:
    from quantum.chemistry.h2o_experiment import run_h2o_simulator

    record = run_h2o_simulator(payload["classical_record"], int(payload.get("maxiter", 50)))
    return {"status": "success", "action": "h2o_simulator", "result": record}


def _run_h2o_statevector(payload: Dict[str, Any]) -> Dict[str, Any]:
    from quantum.chemistry.h2o_experiment import reconstruct_h2o_statevector

    result = reconstruct_h2o_statevector(payload["simulator_record"])
    return {"status": "success", "action": "h2o_statevector", "result": result}


def _run_h2o_hardware(payload: Dict[str, Any]) -> Dict[str, Any]:
    from quantum.chemistry.h2o_experiment import run_h2o_hardware_evaluation

    result = run_h2o_hardware_evaluation(
        payload["simulator_record"],
        payload["backend_name"],
        float(payload.get("precision", 0.05)),
        payload.get("confirm_submission") is True,
        payload.get("mitigation_config"),
    )
    return {"status": "success", "action": "h2o_hardware_evaluation", "result": result}


def main():
    # Save original stdout and redirect any spurious logging/prints to stderr
    real_stdout = sys.stdout
    sys.stdout = sys.stderr

    response_payload = None

    try:
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            raise ValueError("No input JSON received on stdin.")

        data = json.loads(raw_input)
        if not isinstance(data, dict):
            raise ValueError("Input JSON must be an object/dict.")

        action = data.get("action", "analyze_molecule")

        if action == "smoke_test":
            response_payload = _run_smoke_test(data)
        elif action == "analyze_molecule":
            response_payload = _run_molecular_analysis(data)
        elif action == "h2o_classical_reference":
            response_payload = _run_h2o_classical(data)
        elif action == "h2o_simulator":
            response_payload = _run_h2o_simulator(data)
        elif action == "h2o_statevector":
            response_payload = _run_h2o_statevector(data)
        elif action == "h2o_hardware_evaluation":
            response_payload = _run_h2o_hardware(data)
        else:
            raise ValueError(f"Unknown action: '{action}'.")

    except Exception as exc:
        response_payload = {
            "status": "error",
            "error_type": type(exc).__name__,
            "error_message": str(exc),
            "failed_stage": getattr(exc, "worker_stage", None),
            "stage_diagnostics": getattr(exc, "stage_diagnostics", {}),
            "traceback": traceback.format_exc()[-6000:],
        }

    finally:
        # Write clean JSON exclusively to real stdout
        output_json = json.dumps(response_payload)
        real_stdout.write(output_json + "\n")
        real_stdout.flush()


if __name__ == "__main__":
    main()
