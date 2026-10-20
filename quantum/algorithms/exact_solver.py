
from qiskit_algorithms import NumPyMinimumEigensolver


def run_exact_solver(qubit_hamiltonian):
    """
    Compute the exact minimum eigenvalue of the
    same qubit Hamiltonian used by VQE.

    Suitable for small Hamiltonians.
    """

    solver = NumPyMinimumEigensolver()

    result = solver.compute_minimum_eigenvalue(
        qubit_hamiltonian
    )

    return {
        "exact_energy_hartree": float(
            result.eigenvalue.real
        ),
        "method": "Exact Diagonalization",
        "num_qubits": qubit_hamiltonian.num_qubits,
    }
