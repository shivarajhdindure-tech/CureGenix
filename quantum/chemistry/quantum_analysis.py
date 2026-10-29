
import os
import time

from quantum.chemistry.smiles_adapter import smiles_to_geometry
from quantum.chemistry.molecule import build_molecular_problem
from quantum.chemistry.active_space import reduce_to_active_space
from quantum.chemistry.hamiltonian import build_qubit_hamiltonian, interpret_vqe_energy
from quantum.algorithms.vqe import run_vqe
from backend.services.quantum_resource_policy import assess_smiles_resources


def analyze_smiles(
    smiles: str,
    charge: int = 0,
    spin: int = 0,
    basis: str = "sto3g",
    maxiter: int = 50,
    benchmark: bool = False,
):
    """
    Analyze a molecule using a VQE-based active-space workflow.

    Exact diagonalization is optional and intended for small benchmarks.
    HOMO/LUMO values are classical PySCF orbital energies.
    """

    if not smiles:
        raise ValueError("SMILES cannot be empty")

    eligibility = assess_smiles_resources(
        smiles, basis=basis, maxiter=maxiter, charge=charge, benchmark=benchmark
    )
    if eligibility.get("status") == "skipped_resource_limit":
        return {
            "status": "skipped_resource_limit",
            "message": "Quantum calculation skipped by the configured resource eligibility policy.",
            "resource_eligibility": eligibility,
        }
    if eligibility.get("status") == "invalid_input":
        raise ValueError("Invalid SMILES: molecular resource preflight could not parse the structure.")
    if eligibility.get("status") != "eligible":
        raise RuntimeError("Quantum resource policy could not be evaluated: " + "; ".join(eligibility.get("reasons", [])))

    # 1. SMILES -> 3D geometry
    geometry = smiles_to_geometry(smiles)

    # 2. Check execution environment (local PySCF vs WSL adapter)
    use_wsl = os.getenv("CUREGENIX_QUANTUM_BACKEND", "").lower() == "wsl"
    if not use_wsl:
        try:
            import pyscf  # noqa: F401

            has_local_pyscf = True
        except Exception:
            has_local_pyscf = False
        use_wsl = not has_local_pyscf

    if use_wsl:
        from backend.services.wsl_quantum_adapter import wsl_quantum_adapter

        return wsl_quantum_adapter.analyze_geometry(
            atom=geometry,
            basis=basis,
            charge=charge,
            spin=spin,
            maxiter=maxiter,
            benchmark=benchmark,
        )

    # 2b. Build molecular problem locally if PySCF is available
    problem = build_molecular_problem(
        atom=geometry,
        basis=basis,
        charge=charge,
        spin=spin,
    )

    orbital_energies = problem.orbital_energies
    num_spatial_orbitals = problem.num_spatial_orbitals

    # 3. Select HOMO/LUMO orbitals
    alpha_electrons, beta_electrons = problem.num_particles
    total_electrons = alpha_electrons + beta_electrons
    occupied_orbitals = total_electrons // 2

    homo_index = occupied_orbitals - 1
    lumo_index = homo_index + 1

    if homo_index < 0 or lumo_index >= num_spatial_orbitals:
        raise ValueError(
            "HOMO/LUMO orbitals are outside the available orbital range."
        )

    active_orbitals = [homo_index, lumo_index]

    # 4. Reduce to active space
    active_problem = reduce_to_active_space(
        problem,
        num_electrons=2,
        num_spatial_orbitals=2,
        active_orbitals=active_orbitals,
    )

    # 5. Build qubit Hamiltonian
    qubit_hamiltonian = build_qubit_hamiltonian(active_problem)

    # 6. Run VQE and measure runtime
    vqe_start = time.perf_counter()

    vqe_result = run_vqe(
        qubit_hamiltonian,
        num_qubits=qubit_hamiltonian.num_qubits,
        maxiter=maxiter,
    )

    vqe_runtime_seconds = time.perf_counter() - vqe_start

    energy_components = interpret_vqe_energy(
        float(vqe_result["electronic_energy"]), active_problem
    )

    homo_energy = float(orbital_energies[homo_index])
    lumo_energy = float(orbital_energies[lumo_index])

    # Preserve the existing response structure.
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
            "optimizer": vqe_result["optimizer"],
            "ansatz": vqe_result["ansatz"],
            "max_iterations": maxiter,
            "runtime_seconds": vqe_runtime_seconds,
            "optimizer_success": vqe_result.get("optimizer_success"),
            "optimizer_message": vqe_result.get("optimizer_message"),
            "optimizer_status_available": vqe_result.get("optimizer_status_available", False),
        },
    }

    # 7. Optional exact reference for small-system benchmarking
    if benchmark:
        from quantum.algorithms.exact_solver import run_exact_solver

        exact_start = time.perf_counter()
        exact_result = run_exact_solver(qubit_hamiltonian)
        exact_runtime_seconds = time.perf_counter() - exact_start

        vqe_energy = float(vqe_result["electronic_energy"])
        exact_energy = exact_result["exact_energy_hartree"]
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
                relative_error * 100
                if relative_error is not None
                else None
            ),
        }

    return response
