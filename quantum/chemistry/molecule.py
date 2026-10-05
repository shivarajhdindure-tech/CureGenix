from qiskit_nature.units import DistanceUnit
from qiskit_nature.second_q.drivers import PySCFDriver


def build_molecular_problem(
    atom: str,
    basis: str = "sto3g",
    charge: int = 0,
    spin: int = 0,
    unit=DistanceUnit.ANGSTROM,
):
    """
    Build an electronic-structure problem using PySCF.

    Parameters
    ----------
    atom : str
        Molecular geometry.

    basis : str
        Basis set used for the calculation.

    charge : int
        Total molecular charge.

    spin : int
        Spin value used by PySCF/Qiskit Nature.

    unit :
        Distance unit for molecular coordinates.

    Returns
    -------
    ElectronicStructureProblem
        Qiskit Nature molecular problem.
    """

    driver = PySCFDriver(
        atom=atom,
        basis=basis,
        charge=charge,
        spin=spin,
        unit=unit,
    )

    problem = driver.run()

    return problem