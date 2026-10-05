from quantum.chemistry.molecule import build_molecular_problem
from quantum.chemistry.active_space import reduce_to_active_space
from quantum.chemistry.hamiltonian import build_qubit_hamiltonian
from quantum.algorithms.hamiltonian_simulation import simulate_hamiltonian
from quantum.algorithms.vqe import create_vqe
from quantum.algorithms.qaoa import run_qaoa_maxcut
from quantum.chemistry.hamiltonian import (
    build_qubit_hamiltonian,
    interpret_vqe_energy,
)

def get_molecular_info(
    atom: str,
    basis: str = "sto3g",
    charge: int = 0,
    spin: int = 0,
):
    """
    Get molecular information including
    molecular orbital energies and occupations.
    """

    problem = build_molecular_problem(
        atom=atom,
        basis=basis,
        charge=charge,
        spin=spin,
    )

    # ------------------------------------------------------------
    # Molecular orbital information
    # ------------------------------------------------------------

    orbital_energies = []

    if problem.orbital_energies is not None:
        orbital_energies = [
            float(energy)
            for energy in problem.orbital_energies
        ]

    orbital_occupations = []

    if problem.orbital_occupations is not None:
        orbital_occupations = [
            float(occupation)
            for occupation in problem.orbital_occupations
        ]

    return {
        "num_particles": list(problem.num_particles),

        "num_spatial_orbitals": (
            problem.num_spatial_orbitals
        ),

        "orbital_energies": orbital_energies,

        "orbital_occupations": orbital_occupations,
    }


def select_active_space(
    atom: str,
    num_electrons: int,
    num_spatial_orbitals: int,
    basis: str = "sto3g",
    charge: int = 0,
    spin: int = 0,
    active_orbitals=None,
):
    """
    Reduce a molecular problem to an active space.
    """

    problem = build_molecular_problem(
        atom=atom,
        basis=basis,
        charge=charge,
        spin=spin,
    )

    active_problem = reduce_to_active_space(
        problem=problem,
        num_electrons=num_electrons,
        num_spatial_orbitals=num_spatial_orbitals,
        active_orbitals=active_orbitals,
    )

    return {
        "original_particles": list(problem.num_particles),
        "original_spatial_orbitals": problem.num_spatial_orbitals,
        "active_particles": list(active_problem.num_particles),
        "active_spatial_orbitals": active_problem.num_spatial_orbitals,
        "selected_orbitals": active_orbitals,
    }


def run_quantum_vqe(
    atom: str,
    num_electrons: int,
    num_spatial_orbitals: int,
    basis: str = "sto3g",
    charge: int = 0,
    spin: int = 0,
    maxiter: int = 100,
    active_orbitals=None,
):
    """
    Run VQE once on an active-space molecular Hamiltonian.

    Returns both the raw qubit-Hamiltonian energy and the
    information required for chemistry-aware interpretation.
    """

    # 1. Build molecular problem
    problem = build_molecular_problem(
        atom=atom,
        basis=basis,
        charge=charge,
        spin=spin,
    )

    # 2. Reduce to active space
    active_problem = reduce_to_active_space(
        problem=problem,
        num_electrons=num_electrons,
        num_spatial_orbitals=num_spatial_orbitals,
        active_orbitals=active_orbitals,
    )

    # 3. Build qubit Hamiltonian
    qubit_hamiltonian = build_qubit_hamiltonian(
        active_problem
    )

    num_qubits = qubit_hamiltonian.num_qubits

    # 4. Create VQE
    vqe = create_vqe(
        num_qubits=num_qubits,
        maxiter=maxiter,
    )

    # 5. Run VQE exactly once
    vqe_result = vqe.compute_minimum_eigenvalue(
        qubit_hamiltonian
    )

    raw_vqe_energy = float(
        vqe_result.eigenvalue.real
    )

    energy = interpret_vqe_energy(
    raw_vqe_energy=raw_vqe_energy,
    problem=active_problem,
    )

    # 6. Extract VQE metadata
    optimal_parameters = vqe_result.optimal_point

    nuclear_repulsion_energy = float(
        active_problem.nuclear_repulsion_energy
    )

    return {
        "molecule": atom,
        "basis": basis,

        "active_space": {
            "electrons": sum(active_problem.num_particles),
            "spatial_orbitals": active_problem.num_spatial_orbitals,
            "selected_orbitals": active_orbitals,

            "verification": {
                "requested_orbitals": active_orbitals,
                "active_particles": list(
                    active_problem.num_particles
                ),
                "active_spatial_orbitals": (
                    active_problem.num_spatial_orbitals
                ),
                "active_orbital_energies": (
                    [
                        float(energy)
                        for energy in active_problem.orbital_energies
                    ]
                    if active_problem.orbital_energies is not None
                    else []
                ),
            },
        },

        "hamiltonian": {
            "qubits": num_qubits,
            "pauli_terms": len(qubit_hamiltonian),
        },

        "vqe": {
            "electronic_energy_raw": raw_vqe_energy,
            "optimizer": "SLSQP",
            "ansatz": "n_local",
            "max_iterations": maxiter,
            "num_qubits": num_qubits,
            "optimal_parameters": optimal_parameters.tolist(),
        },

        
        "energy": energy,
        
    }

def run_hamiltonian_simulation(
    atom: str,
    num_electrons: int,
    num_spatial_orbitals: int,
    time: float = 1.0,
    basis: str = "sto3g",
    charge: int = 0,
    spin: int = 0,
):
    """
    Run Hamiltonian time evolution for a molecular
    active-space Hamiltonian.
    """

    # 1. Build molecular problem
    problem = build_molecular_problem(
        atom=atom,
        basis=basis,
        charge=charge,
        spin=spin,
    )

    # 2. Select active space
    active_problem = reduce_to_active_space(
        problem=problem,
        num_electrons=num_electrons,
        num_spatial_orbitals=num_spatial_orbitals,
    )

    # 3. Build qubit Hamiltonian
    qubit_hamiltonian = build_qubit_hamiltonian(
        active_problem
    )

    # 4. Simulate time evolution
    result = simulate_hamiltonian(
        qubit_hamiltonian=qubit_hamiltonian,
        time=time,
        num_electrons=num_electrons,
    )

    # 5. Return MCP-friendly result
    return {
        "molecule": atom,
        "basis": basis,

        "active_space": {
            "electrons": sum(active_problem.num_particles),
            "spatial_orbitals": active_problem.num_spatial_orbitals,
        },

        "hamiltonian": {
            "qubits": qubit_hamiltonian.num_qubits,
            "pauli_terms": len(qubit_hamiltonian),
        },

        "simulation": {
            "time": time,
            "initial_state": result[
                "initial_state"
            ].to_dict(),
            "probabilities": result[
                "probabilities"
            ],
        },
    }

def run_quantum_qaoa(
    num_nodes: int,
    edges: list[tuple[int, int]],
    reps: int = 1,
):
    """
    Run QAOA optimization for a MaxCut problem.
    """

    return run_qaoa_maxcut(
        num_nodes=num_nodes,
        edges=edges,
        reps=reps,
    )