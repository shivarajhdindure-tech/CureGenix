"""Reproducible H2O/STO-3G reference, active-space VQE, and opt-in QPU tools.

The active space is the four spatial orbitals consisting of HOMO-1, HOMO,
LUMO, and LUMO+1 (indices [3, 4, 5, 6] for minimal-basis water). The three
lower orbitals are frozen and contain six electrons. This compact 4e/4o
valence-space experiment is a prototype, not a chemically complete water
calculation. VQE uses UCCSD with (2 alpha, 2 beta) particles to stay in the
intended active electron/spin sector.
"""

from __future__ import annotations

import importlib.metadata
import math
import os
import time
import json
import re
from typing import Any


MOLECULE = "H2O"
BASIS = "sto-3g"
ACTIVE_ELECTRONS = 4
ACTIVE_SPATIAL_ORBITALS = 4
DEFAULT_OH_BOND_ANGSTROM = 0.9572
DEFAULT_HOH_ANGLE_DEGREES = 104.5
MAX_STATEVECTOR_QUBITS = 10
MAX_STATEVECTOR_RESPONSE_BYTES = 512 * 1024


def water_configuration(
    oh_bond_length_angstrom: float = DEFAULT_OH_BOND_ANGSTROM,
    hoh_angle_degrees: float = DEFAULT_HOH_ANGLE_DEGREES,
) -> dict[str, Any]:
    """Return deterministic, planar, C2v-like water coordinates in Angstrom."""
    bond = float(oh_bond_length_angstrom)
    angle = float(hoh_angle_degrees)
    if not math.isfinite(bond) or not 0.5 <= bond <= 2.0:
        raise ValueError("O-H bond length must be finite and between 0.5 and 2.0 Angstrom.")
    if not math.isfinite(angle) or not 60.0 <= angle <= 180.0:
        raise ValueError("H-O-H angle must be finite and between 60 and 180 degrees.")

    half_angle = math.radians(angle / 2.0)
    x = bond * math.sin(half_angle)
    z = bond * math.cos(half_angle)
    atoms = [
        {"element": "O", "x": 0.0, "y": 0.0, "z": 0.0},
        {"element": "H", "x": x, "y": 0.0, "z": z},
        {"element": "H", "x": -x, "y": 0.0, "z": z},
    ]
    atom_string = "; ".join(
        f"{atom['element']} {atom['x']:.12f} {atom['y']:.12f} {atom['z']:.12f}"
        for atom in atoms
    )
    return {
        "molecule": MOLECULE,
        "formula": "H2O",
        "charge": 0,
        "spin": 0,
        "spin_multiplicity": 1,
        "basis": BASIS,
        "coordinate_units": "Angstrom",
        "geometry_method": "symmetric planar equilibrium-like geometry; configurable O-H length and H-O-H angle",
        "oh_bond_length_angstrom": bond,
        "hoh_angle_degrees": angle,
        "atoms": atoms,
        "atom_string": atom_string,
    }


def _version(package: str) -> str | None:
    try:
        return importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError:
        return None


def _timed(stage_diagnostics: dict, name: str, function, *args, **kwargs):
    started = time.perf_counter()
    try:
        value = function(*args, **kwargs)
    except Exception:
        stage_diagnostics[name] = {
            "status": "failed",
            "elapsed_seconds": round(time.perf_counter() - started, 6),
        }
        raise
    stage_diagnostics[name] = {
        "status": "completed",
        "elapsed_seconds": round(time.perf_counter() - started, 6),
    }
    return value


def _pauli_terms(operator) -> list[dict[str, Any]]:
    return [
        {
            "pauli": label,
            "real": float(complex(coefficient).real),
            "imag": float(complex(coefficient).imag),
        }
        for label, coefficient in operator.to_list()
    ]


def _resource_estimates(spatial_orbitals: int, active_orbitals: int) -> dict[str, Any]:
    full_qubits = spatial_orbitals * 2
    active_qubits = active_orbitals * 2
    return {
        "method": "qubit-count and statevector dimension estimates; excludes PySCF integral/SCF memory",
        "full_system": {
            "qubits": full_qubits,
            "hilbert_dimension": 2 ** full_qubits,
            "complex128_statevector_mib": round(2 ** full_qubits * 16 / (1024 ** 2), 6),
            "closed_shell_sector_dimension": math.comb(spatial_orbitals, 5) ** 2,
        },
        "active_space": {
            "qubits": active_qubits,
            "hilbert_dimension": 2 ** active_qubits,
            "complex128_statevector_mib": round(2 ** active_qubits * 16 / (1024 ** 2), 6),
            "fixed_particle_sector_dimension": math.comb(active_orbitals, 2) ** 2,
        },
    }


def _optimizer_outcome(optimizer_result: Any) -> dict[str, Any]:
    """Preserve explicit optimizer status; never infer it from energy or iteration counts."""
    success = getattr(optimizer_result, "success", None) if optimizer_result is not None else None
    if success is True:
        status = "success"
        available = True
    elif success is False:
        status = "unsuccessful"
        available = True
    else:
        success = None
        status = "unavailable"
        available = False

    message = getattr(optimizer_result, "message", None) if optimizer_result is not None else None
    return {
        "optimizer_status": status,
        "optimizer_status_available": available,
        "optimizer_success": success,
        "optimizer_message": str(message) if message is not None else None,
    }


def _status_reporting_slsqp(maxiter: int):
    """Create the same Qiskit SLSQP optimizer while retaining SciPy termination fields.

    Qiskit Algorithms 0.4.0's SciPyOptimizer.minimize converts SciPy's OptimizeResult
    into its own OptimizerResult but copies only x, fun, nfev, njev, and nit. The
    termination status and message are therefore otherwise lost before VQE returns.
    """
    from scipy.optimize import minimize as scipy_minimize
    from qiskit_algorithms.optimizers import SLSQP
    from qiskit_algorithms.optimizers.optimizer import OptimizerResult

    class StatusReportingSLSQP(SLSQP):
        def minimize(self, fun, x0, jac=None, bounds=None):
            if self.is_bounds_ignored:
                bounds = None
            if self.is_gradient_ignored:
                jac = None
            raw_result = scipy_minimize(
                fun=fun,
                x0=x0,
                method=self._method,
                jac=jac,
                bounds=bounds,
                options=self._options,
                **self._kwargs,
            )
            result = OptimizerResult()
            result.x = raw_result.x
            result.fun = raw_result.fun
            result.nfev = raw_result.nfev
            result.njev = raw_result.get("njev", None)
            result.nit = raw_result.get("nit", None)
            result.success = raw_result.get("success", None)
            result.message = raw_result.get("message", None)
            return result

    return StatusReportingSLSQP(maxiter=maxiter)


def _qiskit_basis_state_label(index: int, qubit_count: int) -> str:
    """Render Qiskit's statevector index with q[n-1] leftmost and q0 rightmost."""
    return format(index, f"0{qubit_count}b")


def validate_h2o_statevector_record(simulator_record: dict[str, Any]) -> list[float]:
    """Validate a completed, supported H2O simulator record without importing Qiskit."""
    if not isinstance(simulator_record, dict):
        raise ValueError("Simulator experiment record must be a JSON object.")
    execution = simulator_record.get("execution")
    if not isinstance(execution, dict) or execution.get("mode") != "simulator" or execution.get("status") != "completed":
        raise ValueError("A completed H2O simulator experiment record is required.")
    if execution.get("hardware_execution") is not False:
        raise ValueError("Statevector reconstruction accepts simulator records only.")

    molecule = simulator_record.get("molecule")
    if not isinstance(molecule, dict) or molecule.get("formula") != "H2O" or molecule.get("charge") != 0 or molecule.get("spin") != 0:
        raise ValueError("Only neutral singlet H2O records are supported.")

    active = simulator_record.get("active_space")
    expected_active = {
        "active_electrons": 4,
        "active_particles_alpha_beta": [2, 2],
        "active_spatial_orbitals": 4,
        "active_orbital_indices_zero_based": [3, 4, 5, 6],
        "frozen_orbital_indices_zero_based": [0, 1, 2],
        "mapped_qubits": 8,
    }
    if not isinstance(active, dict) or any(active.get(key) != value for key, value in expected_active.items()):
        raise ValueError("Saved active-space settings do not match the supported H2O 4e/4o model.")

    simulator = simulator_record.get("simulator")
    if not isinstance(simulator, dict):
        raise ValueError("Simulator result metadata is missing.")
    if simulator.get("mapper") != "Jordan-Wigner":
        raise ValueError("Saved simulator record does not use Jordan-Wigner mapping.")
    ansatz_description = str(simulator.get("ansatz", "")).casefold()
    if "uccsd" not in ansatz_description or "hartree-fock" not in ansatz_description:
        raise ValueError("Saved simulator record does not describe the supported UCCSD/Hartree-Fock circuit.")

    circuit = simulator.get("circuit")
    if not isinstance(circuit, dict) or circuit.get("qubits") != 8:
        raise ValueError("Saved circuit metadata does not match the supported 8-qubit H2O circuit.")
    if circuit.get("trainable_parameter_count") != 26:
        raise ValueError("Saved circuit parameter-count metadata is missing or unsupported.")

    terms = active.get("hamiltonian_terms")
    if not isinstance(terms, list) or not terms or len(terms) > 2048:
        raise ValueError("Saved active-space Hamiltonian terms are missing or exceed the supported limit.")
    for term in terms:
        if not isinstance(term, dict) or not isinstance(term.get("pauli"), str) or not re.fullmatch(r"[IXYZ]{8}", term["pauli"]):
            raise ValueError("Saved active-space Hamiltonian contains an invalid Pauli term.")
        for coefficient in (term.get("real"), term.get("imag")):
            if isinstance(coefficient, bool) or not isinstance(coefficient, (int, float)) or not math.isfinite(coefficient):
                raise ValueError("Saved active-space Hamiltonian contains an invalid coefficient.")

    parameters = simulator.get("optimized_parameters")
    if not isinstance(parameters, list) or len(parameters) != 26:
        raise ValueError("Saved optimized parameters are missing or have an unsupported length.")
    if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) for value in parameters):
        raise ValueError("Saved optimized parameters must be finite numeric values.")

    if int(circuit["qubits"]) > MAX_STATEVECTOR_QUBITS:
        raise ValueError("Circuit exceeds the configured statevector qubit limit.")
    return [float(value) for value in parameters]


def reconstruct_h2o_statevector(simulator_record: dict[str, Any]) -> dict[str, Any]:
    """Reconstruct only the saved final circuit state; this never runs VQE or an optimizer."""
    optimized_parameters = validate_h2o_statevector_record(simulator_record)

    from qiskit.quantum_info import SparsePauliOp, Statevector
    from qiskit_nature.second_q.circuit.library import HartreeFock, UCCSD
    from qiskit_nature.second_q.mappers import JordanWignerMapper

    active = simulator_record["active_space"]
    mapper = JordanWignerMapper()
    operator = SparsePauliOp.from_list([
        (term["pauli"], complex(term["real"], term["imag"]))
        for term in active["hamiltonian_terms"]
    ])
    if operator.num_qubits != 8:
        raise ValueError("Reconstructed active Hamiltonian does not have the expected 8 qubits.")

    particles = tuple(active["active_particles_alpha_beta"])
    orbitals = int(active["active_spatial_orbitals"])
    initial_state = HartreeFock(orbitals, particles, mapper)
    ansatz = UCCSD(
        num_spatial_orbitals=orbitals,
        num_particles=particles,
        qubit_mapper=mapper,
        initial_state=initial_state,
        reps=1,
    )
    if ansatz.num_qubits != 8 or ansatz.num_parameters != len(optimized_parameters):
        raise ValueError("Reconstructed circuit does not match the saved qubit or parameter configuration.")

    bound_circuit = ansatz.assign_parameters(dict(zip(list(ansatz.parameters), optimized_parameters)))
    statevector = Statevector.from_instruction(bound_circuit)
    amplitudes = statevector.data
    probabilities = statevector.probabilities()
    dimension = 2 ** ansatz.num_qubits
    if len(amplitudes) != dimension or len(probabilities) != dimension:
        raise ValueError("Reconstructed statevector has an unexpected dimension.")

    states = []
    for index, (amplitude, probability) in enumerate(zip(amplitudes, probabilities)):
        real = float(amplitude.real)
        imag = float(amplitude.imag)
        probability = float(probability)
        if not all(math.isfinite(value) for value in (real, imag, probability)):
            raise ValueError("Reconstructed statevector contains non-finite values.")
        states.append({
            "basis_state": _qiskit_basis_state_label(index, ansatz.num_qubits),
            "amplitude_real": real,
            "amplitude_imag": imag,
            "probability": probability,
        })

    norm_squared = sum(item["probability"] for item in states)
    normalization_error = abs(norm_squared - 1.0)
    payload = {
        "experiment_record_id": simulator_record["experiment_record_id"],
        "execution_type": "ideal_statevector_simulation",
        "hardware_execution": False,
        "qubit_count": int(ansatz.num_qubits),
        "statevector_dimension": dimension,
        "basis_state_bit_ordering": (
            "Statevector array index is the computational-basis integer; displayed bitstrings are q[n-1]...q[0], with q0 at the rightmost position."
        ),
        "hamiltonian": {"mapping": "Jordan-Wigner", "qubit_count": int(operator.num_qubits), "pauli_term_count": int(len(operator))},
        "ansatz": "UCCSD with Hartree-Fock initial state; bound to saved optimized parameters",
        "states": states,
        "normalization_check": {
            "probability_sum": float(norm_squared),
            "absolute_error_from_one": float(normalization_error),
            "normalized": bool(math.isclose(norm_squared, 1.0, rel_tol=0.0, abs_tol=1e-10)),
            "tolerance": 1e-10,
        },
    }
    encoded_size = len(json.dumps(payload, allow_nan=False, separators=(",", ":")).encode("utf-8"))
    if encoded_size > MAX_STATEVECTOR_RESPONSE_BYTES:
        raise ValueError("Statevector response exceeds the configured JSON size limit.")
    if not payload["normalization_check"]["normalized"]:
        raise ValueError("Reconstructed statevector failed its normalization check.")
    return payload


def run_h2o_classical_reference(configuration: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build H2O references and full/active qubit Hamiltonians using WSL PySCF."""
    from pyscf import ao2mo, fci, gto, mcscf, scf
    from qiskit_nature.second_q.drivers import PySCFDriver
    from qiskit_nature.second_q.mappers import JordanWignerMapper
    from quantum.chemistry.active_space import reduce_to_active_space
    from quantum.chemistry.hamiltonian import build_qubit_hamiltonian

    config = configuration or water_configuration()
    if config.get("formula") != "H2O" or config.get("charge") != 0 or config.get("spin") != 0:
        raise ValueError("This experiment supports neutral singlet H2O only.")
    atom_string = config["atom_string"]
    stage_diagnostics: dict[str, Any] = {}

    def build_pyscf_rhf():
        molecule = gto.M(
            atom=atom_string,
            basis=config["basis"],
            charge=config["charge"],
            spin=config["spin"],
            unit="Angstrom",
            verbose=0,
        )
        mean_field = scf.RHF(molecule)
        mean_field.verbose = 0
        total = float(mean_field.kernel())
        if not mean_field.converged:
            raise RuntimeError("PySCF RHF did not converge for H2O.")
        return molecule, mean_field, total

    molecule, mean_field, rhf_total = _timed(stage_diagnostics, "pyscf_rhf", build_pyscf_rhf)
    spatial_orbitals = int(mean_field.mo_coeff.shape[1])
    electron_count = int(molecule.nelectron)
    if electron_count != 10 or spatial_orbitals != 7:
        raise RuntimeError(
            f"Unexpected H2O/STO-3G system size: {electron_count} electrons, "
            f"{spatial_orbitals} spatial orbitals."
        )

    resource_estimates = _resource_estimates(spatial_orbitals, ACTIVE_SPATIAL_ORBITALS)
    resource_estimates["full_system"]["estimated_pauli_terms"] = None
    resource_estimates["full_system"]["pauli_terms_note"] = "Measured after full Jordan-Wigner mapping and reported in full_system; not estimated here."

    def full_space_fci():
        h1 = mean_field.mo_coeff.T @ mean_field.get_hcore() @ mean_field.mo_coeff
        eri = ao2mo.kernel(molecule, mean_field.mo_coeff)
        solver = fci.FCI(molecule, mean_field.mo_coeff)
        electronic, _ = solver.kernel(
            h1, eri, spatial_orbitals, molecule.nelec, ecore=0.0
        )
        electronic = float(electronic)
        nuclear = float(molecule.energy_nuc())
        return {
            "status": "completed",
            "method": "PySCF full-space FCI in the closed-shell (5 alpha, 5 beta) sector",
            "electronic_energy_hartree": electronic,
            "nuclear_repulsion_energy_hartree": nuclear,
            "total_energy_hartree": electronic + nuclear,
            "same_hamiltonian_as_rhf": True,
        }

    def build_qiskit_problem():
        return PySCFDriver(
            atom=atom_string,
            basis=config["basis"],
            charge=config["charge"],
            spin=config["spin"],
        ).run()

    problem = _timed(stage_diagnostics, "qiskit_nature_pyscf_driver", build_qiskit_problem)
    full_operator = _timed(
        stage_diagnostics,
        "full_hamiltonian_jordan_wigner_mapping",
        build_qubit_hamiltonian,
        problem,
    )
    resource_estimates["full_system"]["mapped_qubits"] = int(full_operator.num_qubits)
    resource_estimates["full_system"]["pauli_terms"] = len(full_operator)

    # Determine the full Hamiltonian resources before attempting the exact
    # determinant-space diagonalization.
    try:
        full_fci = _timed(stage_diagnostics, "full_space_fci", full_space_fci)
    except Exception as exc:
        # Full-space FCI is supplementary; the selected active-space exact
        # reference below remains required for the simulator comparison.
        full_fci = {
            "status": "unavailable",
            "error_type": type(exc).__name__,
            "reason": "PySCF full-space FCI failed; RHF and active-space stages continue.",
        }

    occupied = electron_count // 2
    active_orbitals = list(range(occupied - 2, occupied + 2))
    frozen_orbitals = [index for index in range(spatial_orbitals) if index not in active_orbitals]
    if active_orbitals != [3, 4, 5, 6] or frozen_orbitals != [0, 1, 2]:
        raise RuntimeError("H2O active-space selection does not match the documented HOMO-1..LUMO+1 policy.")

    active_problem = _timed(
        stage_diagnostics,
        "active_space_reduction",
        reduce_to_active_space,
        problem,
        num_electrons=ACTIVE_ELECTRONS,
        num_spatial_orbitals=ACTIVE_SPATIAL_ORBITALS,
        active_orbitals=active_orbitals,
    )
    particles = tuple(int(value) for value in active_problem.num_particles)
    if particles != (2, 2) or int(active_problem.num_spatial_orbitals) != ACTIVE_SPATIAL_ORBITALS:
        raise RuntimeError(
            f"Active-space transformer changed the intended singlet sector: particles={particles}, "
            f"orbitals={active_problem.num_spatial_orbitals}."
        )
    active_operator = _timed(
        stage_diagnostics,
        "active_hamiltonian_jordan_wigner_mapping",
        build_qubit_hamiltonian,
        active_problem,
    )

    def active_space_exact():
        cas = mcscf.CASCI(mean_field, ACTIVE_SPATIAL_ORBITALS, (2, 2))
        sorted_mos = mcscf.sort_mo(
            cas,
            mean_field.mo_coeff,
            [index + 1 for index in active_orbitals],
            base=1,
        )
        total_energy = float(cas.kernel(sorted_mos)[0])
        nuclear = float(molecule.energy_nuc())
        active_constants = active_problem.hamiltonian.constants
        correction = float(active_constants.get("ActiveSpaceTransformer", 0.0))
        return {
            "status": "completed",
            "method": "PySCF CASCI exact diagonalization in the selected 4e/4o (2 alpha, 2 beta) sector",
            "electronic_energy_hartree": total_energy - nuclear,
            "total_energy_hartree": total_energy,
            "nuclear_repulsion_energy_hartree": nuclear,
            "active_space_constant_hartree": correction,
            "hamiltonian_scope": "selected active-space Hamiltonian with frozen-orbital contributions",
        }

    exact_active = _timed(stage_diagnostics, "active_space_exact_diagonalization", active_space_exact)
    nuclear = float(molecule.energy_nuc())
    rhf_electronic = rhf_total - nuclear
    rhf_reference = {
        "status": "completed",
        "method": "PySCF restricted Hartree-Fock",
        "converged": bool(mean_field.converged),
        "electronic_energy_hartree": rhf_electronic,
        "nuclear_repulsion_energy_hartree": nuclear,
        "total_energy_hartree": rhf_total,
        "same_hamiltonian_as_full_space_fci": full_fci.get("status") == "completed",
    }
    full_terms = _pauli_terms(full_operator)
    active_terms = _pauli_terms(active_operator)
    return {
        "schema_version": 1,
        "molecule": config,
        "software_versions": {
            "python": __import__("sys").version.split()[0],
            "pyscf": _version("pyscf"),
            "qiskit": _version("qiskit"),
            "qiskit_nature": _version("qiskit-nature"),
            "qiskit_algorithms": _version("qiskit-algorithms"),
            "qiskit_ibm_runtime": _version("qiskit-ibm-runtime"),
        },
        "execution": {"mode": "classical_reference", "status": "completed", "hardware_execution": False},
        "references": {"rhf": rhf_reference, "full_space_fci": full_fci},
        "full_system": {
            "electron_count": electron_count,
            "charge": int(config["charge"]),
            "spin": int(config["spin"]),
            "spin_multiplicity": int(config["spin_multiplicity"]),
            "spatial_orbitals": spatial_orbitals,
            "spin_orbitals": spatial_orbitals * 2,
            "mapped_qubits": int(full_operator.num_qubits),
            "pauli_term_count": len(full_operator),
            "hamiltonian_terms": full_terms,
        },
        "active_space": {
            "selection": "HOMO-1, HOMO, LUMO, LUMO+1 from the RHF orbital ordering",
            "justification": "Compact valence-active prototype; excludes the three lowest doubly occupied orbitals, including the oxygen 1s core. Not a chemically complete water model.",
            "active_orbital_indices_zero_based": active_orbitals,
            "frozen_orbital_indices_zero_based": frozen_orbitals,
            "frozen_electron_count": 6,
            "active_electrons": ACTIVE_ELECTRONS,
            "active_particles_alpha_beta": list(particles),
            "active_spatial_orbitals": ACTIVE_SPATIAL_ORBITALS,
            "spin_orbitals": ACTIVE_SPATIAL_ORBITALS * 2,
            "charge": int(config["charge"]),
            "spin": int(config["spin"]),
            "mapped_qubits": int(active_operator.num_qubits),
            "pauli_term_count": len(active_operator),
            "hamiltonian_terms": active_terms,
            "exact_reference": exact_active,
        },
        "resource_estimates": resource_estimates,
        "stage_diagnostics": stage_diagnostics,
        "warnings": [
            "Full-space RHF/FCI and active-space energies are different references; only compare VQE with the active-space exact reference.",
            "The configured active space is a compact exploratory model and omits frozen valence correlation.",
            "Statevector estimates do not model PySCF memory use or IBM hardware noise.",
        ],
    }


def run_h2o_simulator(classical_record: dict[str, Any], maxiter: int = 50) -> dict[str, Any]:
    """Run UCCSD VQE with a local StatevectorEstimator on a saved active H2O Hamiltonian."""
    if classical_record.get("execution", {}).get("mode") != "classical_reference":
        raise ValueError("Simulator mode requires a completed H2O classical-reference record.")
    if classical_record.get("execution", {}).get("status") != "completed":
        raise ValueError("Simulator mode requires a successful classical-reference record.")
    if not isinstance(maxiter, int) or maxiter < 1 or maxiter > 500:
        raise ValueError("maxiter must be an integer between 1 and 500.")

    import numpy as np
    from qiskit import transpile
    from qiskit.primitives import StatevectorEstimator
    from qiskit_algorithms import VQE
    from qiskit_nature.second_q.circuit.library import HartreeFock, UCCSD
    from qiskit_nature.second_q.mappers import JordanWignerMapper
    from qiskit.quantum_info import SparsePauliOp

    experiment_started = time.perf_counter()
    stage_diagnostics: dict[str, Any] = {}
    active = classical_record["active_space"]
    terms = [(item["pauli"], complex(item["real"], item["imag"])) for item in active["hamiltonian_terms"]]
    operator = SparsePauliOp.from_list(terms)
    mapper = JordanWignerMapper()
    particles = tuple(active["active_particles_alpha_beta"])
    orbitals = int(active["active_spatial_orbitals"])
    ansatz_started = time.perf_counter()
    initial_state = HartreeFock(orbitals, particles, mapper)
    ansatz = UCCSD(
        num_spatial_orbitals=orbitals,
        num_particles=particles,
        qubit_mapper=mapper,
        initial_state=initial_state,
        reps=1,
    )
    stage_diagnostics["ansatz_construction"] = {
        "status": "completed", "elapsed_seconds": round(time.perf_counter() - ansatz_started, 6)
    }
    compile_started = time.perf_counter()
    compiled_ansatz = transpile(ansatz, basis_gates=["u", "cx"], optimization_level=0)
    stage_diagnostics["circuit_transpilation_for_gate_accounting"] = {
        "status": "completed", "elapsed_seconds": round(time.perf_counter() - compile_started, 6)
    }
    initial_point = np.zeros(ansatz.num_parameters, dtype=float)
    vqe = VQE(
        estimator=StatevectorEstimator(),
        ansatz=ansatz,
        optimizer=_status_reporting_slsqp(maxiter),
        initial_point=initial_point,
    )
    started = time.perf_counter()
    result = vqe.compute_minimum_eigenvalue(operator)
    elapsed = time.perf_counter() - started
    raw_energy = float(result.eigenvalue.real)
    active_constant = float(active["exact_reference"]["active_space_constant_hartree"])
    nuclear = float(active["exact_reference"]["nuclear_repulsion_energy_hartree"])
    electronic = raw_energy + active_constant
    total = electronic + nuclear
    optimizer_result = getattr(result, "optimizer_result", None)
    optimizer_outcome = _optimizer_outcome(optimizer_result)
    ansatz_ops = {str(name): int(count) for name, count in compiled_ansatz.count_ops().items()}
    optimized_parameters = np.asarray(result.optimal_point, dtype=float).tolist()
    exact_total = float(active["exact_reference"]["total_energy_hartree"])
    exact_electronic = float(active["exact_reference"]["electronic_energy_hartree"])
    return {
        **classical_record,
        "execution": {"mode": "simulator", "status": "completed", "hardware_execution": False},
        "stage_diagnostics": {
            **classical_record.get("stage_diagnostics", {}),
            **stage_diagnostics,
            "vqe_optimization": {"status": "completed", "elapsed_seconds": round(elapsed, 6)},
            "total_simulator_elapsed_seconds": round(time.perf_counter() - experiment_started, 6),
        },
        "simulator": {
            "name": "Qiskit StatevectorEstimator",
            "method": "VQE",
            "mapper": "Jordan-Wigner",
            "ansatz": "UCCSD with Hartree-Fock initial state; particle- and spin-conserving (2 alpha, 2 beta)",
            "optimizer": "SLSQP",
            "max_iterations": maxiter,
            **optimizer_outcome,
            "iterations": getattr(optimizer_result, "nit", None),
            "evaluations": getattr(optimizer_result, "nfev", None),
            "runtime_seconds": round(elapsed, 6),
            "energy_hartree": raw_energy,
            "electronic_energy_hartree": electronic,
            "total_energy_hartree": total,
            "active_space_constant_hartree": active_constant,
            "nuclear_repulsion_energy_hartree": nuclear,
            "circuit": {
                "qubits": int(ansatz.num_qubits),
                "depth": int(compiled_ansatz.depth()),
                "gate_count": int(sum(ansatz_ops.values())),
                "gate_counts": ansatz_ops,
                "gate_basis": ["u", "cx"],
                "transpile_optimization_level": 0,
                "trainable_parameter_count": int(ansatz.num_parameters),
            },
            "optimized_parameters": optimized_parameters,
            "active_space_exact_total_energy_hartree": exact_total,
            "active_space_exact_electronic_energy_hartree": exact_electronic,
            "difference_from_same_active_space_exact_hartree": total - exact_total,
            "absolute_difference_from_same_active_space_exact_hartree": abs(total - exact_total),
            "comparison_scope": "VQE total energy compared only with CASCI exact total energy from this same frozen-core active-space model.",
        },
    }


def run_h2o_hardware_evaluation(
    simulator_record: dict[str, Any],
    backend_name: str,
    precision: float,
    confirm_submission: bool,
    mitigation_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Evaluate saved simulator-optimized UCCSD parameters once on IBM Runtime."""
    if confirm_submission is not True:
        return {"status": "not_submitted", "reason": "Explicit hardware-submission confirmation is required."}
    if simulator_record.get("execution", {}).get("mode") != "simulator" or simulator_record.get("execution", {}).get("status") != "completed":
        raise ValueError("Hardware evaluation requires a completed simulator record.")
    if not backend_name or len(backend_name) > 80:
        raise ValueError("A valid IBM backend name is required.")
    if not math.isfinite(float(precision)) or not 0.001 <= float(precision) <= 0.2:
        raise ValueError("precision must be between 0.001 and 0.2.")

    token = os.getenv("QISKIT_IBM_TOKEN")
    instance = os.getenv("QISKIT_IBM_INSTANCE")
    if not token or not instance:
        return {
            "status": "not_configured",
            "reason": "IBM Runtime credentials and instance are not configured in the WSL environment.",
        }
    try:
        from qiskit_ibm_runtime import EstimatorV2, QiskitRuntimeService
    except ImportError:
        return {"status": "dependency_missing", "reason": "qiskit-ibm-runtime is not installed in the WSL calculation environment."}

    from qiskit.quantum_info import SparsePauliOp
    from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
    from qiskit_nature.second_q.circuit.library import HartreeFock, UCCSD
    from qiskit_nature.second_q.mappers import JordanWignerMapper
    from quantum.chemistry.runtime_mitigation import execute_estimator_with_provenance

    active = simulator_record["active_space"]
    simulator = simulator_record["simulator"]
    mapper = JordanWignerMapper()
    particles = tuple(active["active_particles_alpha_beta"])
    orbitals = int(active["active_spatial_orbitals"])
    initial_state = HartreeFock(orbitals, particles, mapper)
    ansatz = UCCSD(
        num_spatial_orbitals=orbitals,
        num_particles=particles,
        qubit_mapper=mapper,
        initial_state=initial_state,
        reps=1,
    )
    parameters = list(ansatz.parameters)
    values = simulator["optimized_parameters"]
    if len(parameters) != len(values):
        raise ValueError("Saved VQE parameters do not match the reconstructed UCCSD circuit.")
    bound = ansatz.assign_parameters(dict(zip(parameters, values)))
    operator = SparsePauliOp.from_list([
        (item["pauli"], complex(item["real"], item["imag"]))
        for item in active["hamiltonian_terms"]
    ])
    active_constant = float(active["exact_reference"]["active_space_constant_hartree"])
    nuclear_repulsion = float(active["exact_reference"]["nuclear_repulsion_energy_hartree"])

    try:
        service = QiskitRuntimeService(
            channel=os.getenv("QISKIT_IBM_CHANNEL", "ibm_quantum_platform"),
            token=token,
            instance=instance,
        )
        backend = service.backend(backend_name)
        backend_status = backend.status()
        if not backend_status.operational:
            return {
                "status": "backend_unavailable",
                "backend": backend_name,
                "reason": "Selected backend is not operational.",
            }
        pass_manager = generate_preset_pass_manager(backend=backend, optimization_level=1)
        isa_circuit = pass_manager.run(bound)
        isa_operator = operator.apply_layout(isa_circuit.layout)
        estimator_run = execute_estimator_with_provenance(
            EstimatorV2,
            backend,
            [(isa_circuit, isa_operator)],
            float(precision),
            mitigation_config,
            circuit=isa_circuit,
            observable=isa_operator,
        )
        job = estimator_run["job"]
        pub = estimator_run["pub_result"]
        evs = float(pub.data.evs)
        stds = float(pub.data.stds)
        status = job.status()
        runtime_provenance = estimator_run["provenance"]
        return {
            "status": "completed",
            "execution_type": "hardware_evaluation_of_fixed_simulator_optimized_parameters",
            "backend": str(backend.name),
            "job_id": estimator_run["job_id"],
            "precision": float(precision),
            "raw_active_space_energy_hartree": evs,
            "active_space_constant_hartree": active_constant,
            "electronic_energy_hartree": evs + active_constant,
            "nuclear_repulsion_energy_hartree": nuclear_repulsion,
            "total_molecular_energy_hartree": evs + active_constant + nuclear_repulsion,
            "standard_error_hartree": stds,
            "queue_or_execution_status": str(status),
            "result_metadata": {
                "shots": getattr(pub.metadata, "get", lambda *_: None)("shots"),
                "target_precision": getattr(pub.metadata, "get", lambda *_: None)("target_precision"),
            },
            "runtime_provenance": runtime_provenance,
            "circuit_qubits": int(isa_circuit.num_qubits),
            "circuit_depth": int(isa_circuit.depth()),
            "simulator_energy_hartree": float(simulator["energy_hartree"]),
            "difference_from_simulator_hartree": evs - float(simulator["energy_hartree"]),
            "warning": "Parameters were optimized on a local statevector simulator; this is not hardware-optimized VQE.",
        }
    except Exception as exc:
        # Avoid returning exception text, which can contain service/config details.
        failed = {
            "status": "failed",
            "backend": backend_name,
            "error_type": getattr(exc, "error_type", type(exc).__name__),
            "reason": "IBM Runtime evaluation failed; consult protected service logs.",
        }
        provenance = getattr(exc, "provenance", None)
        if isinstance(provenance, dict):
            failed["runtime_provenance"] = provenance
        return failed
