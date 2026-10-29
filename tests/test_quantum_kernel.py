import numpy as np
import pytest

from backend.services.quantum_kernel import run_quantum_kernel_demo


@pytest.mark.parametrize("task", ["classification", "regression"])
def test_demo_returns_both_models(task):
    result = run_quantum_kernel_demo(
        task=task,
        landmarks=4,
        seed=42,
    )

    assert result["task"] == task
    assert result["dataset"] == "synthetic_illustration_not_drug_data"
    assert result["train_samples"] > 0
    assert result["test_samples"] > 0
    assert result["quantum_method"].startswith("ZZFeatureMap")
    assert "quantum_kernel_model" in result
    assert "classical_rbf_baseline" in result
    assert result["runtime_seconds"] >= 0


def test_landmark_kernel_is_symmetric():
    result = run_quantum_kernel_demo(
        task="classification",
        landmarks=4,
        seed=42,
    )

    matrix = np.asarray(
        result["kernel_visualization"]["landmark_kernel"]
    )

    assert matrix.shape == (4, 4)
    assert np.allclose(matrix, matrix.T, atol=1e-6)
    assert np.allclose(np.diag(matrix), 1.0, atol=0.02)


def test_repeated_run_is_reproducible():
    first = run_quantum_kernel_demo(
        task="classification",
        landmarks=3,
        seed=42,
    )
    second = run_quantum_kernel_demo(
        task="classification",
        landmarks=3,
        seed=42,
    )

    assert (
        first["quantum_kernel_model"]["predictions"]
        == second["quantum_kernel_model"]["predictions"]
    )
    assert (
        first["classical_rbf_baseline"]["predictions"]
        == second["classical_rbf_baseline"]["predictions"]
    )


@pytest.mark.parametrize("task", ["unknown", "", "classificationx"])
def test_invalid_task_is_rejected(task):
    with pytest.raises(ValueError, match="task must be"):
        run_quantum_kernel_demo(task=task)


@pytest.mark.parametrize("landmarks", [1, 7, 0, -1])
def test_invalid_landmark_count_is_rejected(landmarks):
    with pytest.raises(ValueError, match="landmarks must be"):
        run_quantum_kernel_demo(landmarks=landmarks)
