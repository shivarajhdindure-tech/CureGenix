
import pytest

from quantum.algorithms.vqe import create_vqe, run_vqe


def test_create_vqe_uses_default_initialization():
    vqe = create_vqe(num_qubits=2, maxiter=5)

    expected = [
        0.1 * ((i % 5) - 2)
        for i in range(vqe.ansatz.num_parameters)
    ]

    assert list(vqe.initial_point) == expected


def test_create_vqe_accepts_custom_initialization():
    # Two qubits are needed for the CZ entanglement.
    ansatz = create_vqe(num_qubits=2, maxiter=5).ansatz
    initial_point = [0.2] * ansatz.num_parameters

    vqe = create_vqe(
        num_qubits=2,
        maxiter=5,
        initial_point=initial_point,
    )

    assert list(vqe.initial_point) == initial_point


def test_create_vqe_rejects_wrong_parameter_count():
    with pytest.raises(ValueError, match="Expected"):
        create_vqe(
            num_qubits=2,
            maxiter=5,
            initial_point=[0.1],
        )


def test_create_vqe_does_not_mutate_custom_initialization():
    initial_point = [0.2] * create_vqe(
        num_qubits=2,
        maxiter=5,
    ).ansatz.num_parameters
    original = initial_point.copy()

    create_vqe(
        num_qubits=2,
        maxiter=5,
        initial_point=initial_point,
    )

    assert initial_point == original
