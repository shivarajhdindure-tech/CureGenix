from qiskit_nature.second_q.mappers import JordanWignerMapper


def build_qubit_hamiltonian(problem):
    fermionic_hamiltonian = problem.hamiltonian.second_q_op()

    mapper = JordanWignerMapper()

    qubit_hamiltonian = mapper.map(
        fermionic_hamiltonian
    )

    return qubit_hamiltonian


def interpret_vqe_energy(
    raw_vqe_energy: float,
    problem,
):
    """
    Convert the raw active-space Hamiltonian eigenvalue
    into a chemically interpreted molecular energy.

    The ActiveSpaceTransformer contributes a constant
    correction which must be added to the active-space
    Hamiltonian eigenvalue.
    """

    constants = problem.hamiltonian.constants

    nuclear_repulsion = float(
        constants.get(
            "nuclear_repulsion_energy",
            0.0,
        )
    )

    active_space_constant = float(
        constants.get(
            "ActiveSpaceTransformer",
            0.0,
        )
    )

    electronic_energy = (
        raw_vqe_energy
        + active_space_constant
    )

    total_energy = (
        electronic_energy
        + nuclear_repulsion
    )

    return {
        "raw_active_space_energy": raw_vqe_energy,

        "active_space_correction": active_space_constant,

        "electronic_energy": electronic_energy,

        "nuclear_repulsion_energy": nuclear_repulsion,

        "total_molecular_energy": total_energy,
    }