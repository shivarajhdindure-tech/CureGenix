from qiskit_nature.second_q.transformers import ActiveSpaceTransformer


def reduce_to_active_space(
    problem,
    num_electrons: int,
    num_spatial_orbitals: int,
    active_orbitals=None,
):
    """
    Reduce a molecular electronic-structure problem
    to a selected active space.

    Parameters
    ----------
    problem :
        Qiskit Nature electronic-structure problem.

    num_electrons : int
        Number of active electrons.

    num_spatial_orbitals : int
        Number of active spatial orbitals.

    active_orbitals : list[int] | None
        Indices of the spatial orbitals to retain.

    Returns
    -------
    ElectronicStructureProblem
        Active-space reduced problem.
    """

    transformer = ActiveSpaceTransformer(
        num_electrons=num_electrons,
        num_spatial_orbitals=num_spatial_orbitals,
        active_orbitals=active_orbitals,
    )

    active_problem = transformer.transform(problem)

    return active_problem