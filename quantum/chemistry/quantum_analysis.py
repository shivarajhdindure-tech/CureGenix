from quantum.chemistry.smiles_adapter import smiles_to_geometry
from quantum.chemistry.molecule import build_molecular_problem
from quantum.chemistry.active_space import reduce_to_active_space
from quantum.chemistry.hamiltonian import build_qubit_hamiltonian
from quantum.algorithms.vqe import run_vqe


def analyze_smiles(
    smiles: str,
    charge: int = 0,
    spin: int = 0,
    basis: str = "sto3g",
    maxiter: int = 50,
):
    """
    Run quantum analysis on a molecule represented by SMILES.

    Prototype workflow:
        SMILES
        -> RDKit 3D geometry
        -> PySCF
        -> HOMO/LUMO active space
        -> Jordan-Wigner Hamiltonian
        -> VQE

    Returns quantum-derived molecular descriptors.
    """

    if not smiles:
        raise ValueError("SMILES cannot be empty")

    # ---------------------------------------------------------
    # 1. SMILES -> 3D geometry
    # ---------------------------------------------------------

    geometry = smiles_to_geometry(smiles)

    # ---------------------------------------------------------
    # 2. Build full molecular problem
    # ---------------------------------------------------------

    problem = build_molecular_problem(
        atom=geometry,
        basis=basis,
        charge=charge,
        spin=spin,
    )

    orbital_energies = problem.orbital_energies

    num_spatial_orbitals = problem.num_spatial_orbitals

    # ---------------------------------------------------------
    # 3. Select HOMO/LUMO active space
    # ---------------------------------------------------------

    alpha_electrons, beta_electrons = problem.num_particles

    total_electrons = alpha_electrons + beta_electrons

    occupied_orbitals = total_electrons // 2

    homo_index = occupied_orbitals - 1
    lumo_index = homo_index + 1

    if lumo_index >= num_spatial_orbitals:
        raise ValueError(
            "LUMO orbital is outside the available orbital range."
        )

    active_orbitals = [homo_index, lumo_index]

    # ---------------------------------------------------------
    # 4. Reduce to active space
    # ---------------------------------------------------------

    active_problem = reduce_to_active_space(
        problem,
        num_electrons=2,
        num_spatial_orbitals=2,
        active_orbitals=active_orbitals,
    )

    # ---------------------------------------------------------
    # 5. Build qubit Hamiltonian
    # ---------------------------------------------------------

    qubit_hamiltonian = build_qubit_hamiltonian(
        active_problem
    )

    # ---------------------------------------------------------
    # 6. Run VQE
    # ---------------------------------------------------------

    vqe_result = run_vqe(
        qubit_hamiltonian,
        num_qubits=qubit_hamiltonian.num_qubits,
        maxiter=maxiter,
    )

    # ---------------------------------------------------------
    # 7. Quantum-derived descriptors
    # ---------------------------------------------------------

    homo_energy = float(orbital_energies[homo_index])
    lumo_energy = float(orbital_energies[lumo_index])

    homo_lumo_gap = lumo_energy - homo_energy

    return {
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

        "homo_lumo_gap_hartree": homo_lumo_gap,

        "hamiltonian": {
            "qubits": qubit_hamiltonian.num_qubits,
            "pauli_terms": len(qubit_hamiltonian),
            "mapping": "Jordan-Wigner",
        },

        "vqe": {
            "electronic_energy_hartree": vqe_result[
                "electronic_energy"
            ],
            "optimizer": vqe_result["optimizer"],
            "ansatz": vqe_result["ansatz"],
            "max_iterations": maxiter,
        },
    }