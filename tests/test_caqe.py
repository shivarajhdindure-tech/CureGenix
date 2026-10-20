
import pytest
from qiskit.quantum_info import SparsePauliOp
from types import SimpleNamespace
from unittest.mock import patch

from quantum.algorithms.caqe import run_caqe


@pytest.fixture
def hamiltonian():
    return SparsePauliOp.from_list([
        ("ZI", 0.5),
        ("IZ", 0.5),
        ("XX", 0.2),
    ])


def test_caqe_rejects_zero_starts(hamiltonian):
    with pytest.raises(ValueError, match="max_starts"):
        run_caqe(hamiltonian, max_starts=0)


def test_caqe_rejects_invalid_initialization_length(hamiltonian):
    with pytest.raises(
        ValueError,
        match="No valid initializations match the ansatz parameters",
    ):
        run_caqe(
            hamiltonian,
            initializations=[[]],
            max_starts=1,
        )

def test_caqe_selects_lowest_energy_run(hamiltonian):
    fake_results = [
        SimpleNamespace(
            eigenvalue=-0.8,
            optimizer_result=SimpleNamespace(
                nfev=10,
                njev=2,
                nit=3,
                success=True,
                message="completed",
            ),
        ),
        SimpleNamespace(
            eigenvalue=-1.0,
            optimizer_result=SimpleNamespace(
                nfev=12,
                njev=3,
                nit=4,
                success=True,
                message="completed",
            ),
        ),
    ]

    class FakeVQE:
        def __init__(self, **kwargs):
            pass

        def compute_minimum_eigenvalue(self, operator):
            return fake_results.pop(0)

    with (
        patch("quantum.algorithms.caqe.VQE", FakeVQE),
        patch(
            "quantum.algorithms.caqe.run_exact_solver",
            return_value={"exact_energy_hartree": -1.1},
        ),
    ):
        result = run_caqe(
            hamiltonian,
            max_starts=2,
            initializations=[[0.0] * 6, [0.1] * 6],
        )

    assert result["starts_completed"] == 2
    assert result["best_run"]["energy_hartree"] == -1.0
    assert result["best_run"]["absolute_error_hartree"] == pytest.approx(0.1)