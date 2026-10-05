from qiskit_algorithms import VQE
from qiskit_algorithms.optimizers import SLSQP
from qiskit.circuit.library import n_local
from qiskit.primitives import StatevectorEstimator


def create_vqe(
    num_qubits: int,
    maxiter: int = 100,
):
    """
    Create and configure the VQE solver.
    """

    ansatz = n_local(
        num_qubits=num_qubits,
        rotation_blocks=["ry"],
        entanglement_blocks=["cz"],
        entanglement="full",
        reps=2,
    )

    optimizer = SLSQP(maxiter=maxiter)

    estimator = StatevectorEstimator()

    vqe = VQE(
        estimator=estimator,
        ansatz=ansatz,
        optimizer=optimizer,
    )

    return vqe


def run_vqe(
    qubit_hamiltonian,
    num_qubits: int,
    maxiter: int = 100,
):
    """
    Run VQE and return the optimized result.
    """

    vqe = create_vqe(
        num_qubits=num_qubits,
        maxiter=maxiter,
    )

    result = vqe.compute_minimum_eigenvalue(
        qubit_hamiltonian
    )

    return {
        "electronic_energy": float(result.eigenvalue.real),
        "optimizer": "SLSQP",
        "ansatz": "n_local",
        "max_iterations": maxiter,
        "num_qubits": num_qubits,
        "raw_result": result,
        "vqe_solver": vqe,
    }