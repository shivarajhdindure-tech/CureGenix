import numpy as np

from scipy.linalg import expm
from qiskit.quantum_info import Statevector


def create_hartree_fock_state(
    num_qubits: int,
    num_electrons: int,
):
    """
    Create a simple Hartree-Fock computational-basis state.

    The first `num_electrons` qubits are initialized to |1>.
    """

    if num_electrons > num_qubits:
        raise ValueError(
            "Number of electrons cannot exceed number of qubits."
        )

    bitstring = "1" * num_electrons + "0" * (
        num_qubits - num_electrons
    )

    return Statevector.from_label(bitstring)


def simulate_hamiltonian(
    qubit_hamiltonian,
    time: float = 1.0,
    initial_state=None,
    num_electrons: int | None = None,
):
    """
    Simulate quantum time evolution under a Hamiltonian.

    Uses exact matrix exponentiation:

        U(t) = exp(-iHt)

    For molecular simulations, `num_electrons` can be
    provided to automatically construct a simple
    Hartree-Fock-style initial state.
    """

    num_qubits = qubit_hamiltonian.num_qubits

    # --------------------------------------------------
    # 1. Prepare initial state
    # --------------------------------------------------

    if initial_state is None:

        if num_electrons is not None:
            initial_state = create_hartree_fock_state(
                num_qubits=num_qubits,
                num_electrons=num_electrons,
            )

        else:
            initial_state = Statevector.from_label(
                "0" * num_qubits
            )

    # --------------------------------------------------
    # 2. Convert Hamiltonian to matrix
    # --------------------------------------------------

    hamiltonian_matrix = qubit_hamiltonian.to_matrix()

    # --------------------------------------------------
    # 3. Construct evolution operator
    # --------------------------------------------------

    evolution_operator = expm(
        -1j * hamiltonian_matrix * time
    )

    # --------------------------------------------------
    # 4. Evolve state
    # --------------------------------------------------

    final_vector = (
        evolution_operator
        @ initial_state.data
    )

    evolved_state = Statevector(final_vector)

    # --------------------------------------------------
    # 5. Measurement probabilities
    # --------------------------------------------------

    probabilities = evolved_state.probabilities_dict()

    probabilities = {
        str(state): float(
            np.real(probability)
        )
        for state, probability in probabilities.items()
    }

    return {
        "num_qubits": num_qubits,
        "time": time,
        "initial_state": initial_state,
        "final_state": evolved_state,
        "probabilities": probabilities,
    }