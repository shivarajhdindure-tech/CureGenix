
from qiskit_algorithms import VQE
from qiskit_algorithms.optimizers import SLSQP
from qiskit.circuit.library import n_local
from qiskit.primitives import StatevectorEstimator


def create_vqe(
    num_qubits: int,
    maxiter: int = 100,
    initial_point=None,
):
    ansatz = n_local(
        num_qubits=num_qubits,
        rotation_blocks=["ry"],
        entanglement_blocks=["cz"],
        entanglement="full",
        reps=2,
    )

    optimizer = SLSQP(maxiter=maxiter)
    estimator = StatevectorEstimator()

    # Preserve the existing deterministic default.
    if initial_point is None:
        initial_point = [
            0.1 * ((i % 5) - 2)
            for i in range(ansatz.num_parameters)
        ]

    if len(initial_point) != ansatz.num_parameters:
        raise ValueError(
            f"Expected {ansatz.num_parameters} initial parameters, "
            f"received {len(initial_point)}."
        )

    return VQE(
        estimator=estimator,
        ansatz=ansatz,
        optimizer=optimizer,
        initial_point=list(initial_point),
    )


def run_vqe(
    qubit_hamiltonian,
    num_qubits: int,
    maxiter: int = 100,
    initial_point=None,
):
    """Run VQE with an optional custom initial parameter vector."""

    vqe = create_vqe(
        num_qubits=num_qubits,
        maxiter=maxiter,
        initial_point=initial_point,
    )

    result = vqe.compute_minimum_eigenvalue(qubit_hamiltonian)

    optimizer_result = result.optimizer_result

    return {
        "electronic_energy": float(result.eigenvalue.real),
        "optimizer": "SLSQP",
        "ansatz": "n_local",
        "max_iterations": maxiter,
        "num_qubits": num_qubits,
        "evaluations": getattr(optimizer_result, "nfev", None),
        "iterations": getattr(optimizer_result, "nit", None),
        "optimizer_success": getattr(optimizer_result, "success", None),
        "optimizer_message": str(getattr(optimizer_result, "message", "")),
        "optimizer_status_available": (
            hasattr(optimizer_result, "success")
            or hasattr(optimizer_result, "message")
        ),
        "raw_result": result,
        "vqe_solver": vqe,
    }
