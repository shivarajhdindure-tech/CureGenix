"""Reproducible two-class variational quantum classifier helpers.

The feature map encodes values supplied by a training-only preprocessing
pipeline. RealAmplitudes owns trainable circuit parameters; Qiskit Machine
Learning optimizes them against cross-entropy labels using a sampler.
"""

from __future__ import annotations

import time

import numpy as np
from qiskit.circuit.library import real_amplitudes, zz_feature_map
from qiskit.primitives import StatevectorSampler
from qiskit_algorithms.optimizers import SciPyOptimizer
from qiskit_algorithms.optimizers import COBYLA
from qiskit_algorithms.optimizers import OptimizerResult
from qiskit_machine_learning.algorithms.classifiers import VQC


def create_vqc_classifier(
    feature_dimension: int = 4,
    reps: int = 1,
    maxiter: int = 20,
    shots: int = 256,
    seed: int = 42,
) -> VQC:
    """Create a seeded VQC with a fixed feature map and trainable ansatz."""
    if not isinstance(feature_dimension, int) or feature_dimension < 2:
        raise ValueError("feature_dimension must be an integer >= 2")
    if not isinstance(reps, int) or reps < 1:
        raise ValueError("reps must be a positive integer")
    if not isinstance(maxiter, int) or maxiter < 1:
        raise ValueError("maxiter must be a positive integer")
    if not isinstance(shots, int) or shots < 1:
        raise ValueError("shots must be a positive integer")
    if not isinstance(seed, int) or seed < 0:
        raise ValueError("seed must be a non-negative integer")

    feature_map = zz_feature_map(
        feature_dimension=feature_dimension,
        reps=reps,
        entanglement="linear",
    )
    ansatz = real_amplitudes(
        num_qubits=feature_dimension,
        reps=reps,
        entanglement="linear",
    )
    initial_point = np.random.default_rng(seed).uniform(
        -np.pi, np.pi, size=ansatz.num_parameters
    )
    return VQC(
        feature_map=feature_map,
        ansatz=ansatz,
        loss="cross_entropy",
        optimizer=COBYLA(maxiter=maxiter),
        sampler=StatevectorSampler(default_shots=shots, seed=seed),
        initial_point=initial_point,
    )


def fit_vqc(model: VQC, features, labels) -> dict:
    """Fit a binary VQC and return bounded runtime/loss diagnostics."""
    x = np.asarray(features, dtype=float)
    y = np.asarray(labels)
    if x.ndim != 2 or x.shape[0] < 2 or not np.isfinite(x).all():
        raise ValueError("features must be a finite 2D array with at least two rows")
    if x.shape[1] != model.num_qubits:
        raise ValueError(f"features must have {model.num_qubits} columns")
    if y.ndim != 1 or len(y) != len(x):
        raise ValueError("labels must be a 1D array aligned with features")
    classes = np.unique(y)
    if len(classes) != 2:
        raise ValueError("VQC requires exactly two classes in the training data")

    objective_history = []
    optimizer = model.optimizer
    if isinstance(optimizer, SciPyOptimizer):
        # Qiskit ML stores the callback internally; COBYLA does not expose an
        # iteration callback, so its result's final cross-entropy is recorded.
        model._callback = lambda parameters, loss: objective_history.append(float(loss))
    started = time.perf_counter()
    model.fit(x, y)
    elapsed = time.perf_counter() - started
    optimizer_result = model.fit_result
    return {
        "status": "success",
        "runtime_seconds": round(elapsed, 6),
        "training_samples": int(len(x)),
        "feature_dimension": int(x.shape[1]),
        "class_labels": classes.tolist(),
        "objective_evaluations": int(getattr(optimizer_result, "nfev", 0) or 0),
        "final_training_loss": (
            float(optimizer_result.fun)
            if getattr(optimizer_result, "fun", None) is not None
            else None
        ),
        "objective_history": objective_history,
        "optimizer_iterations": (
            int(optimizer_result.nit) if getattr(optimizer_result, "nit", None) is not None else None
        ),
        "optimizer_evaluations": (
            int(optimizer_result.nfev) if getattr(optimizer_result, "nfev", None) is not None else None
        ),
        "optimizer_objective": (
            float(optimizer_result.fun)
            if getattr(optimizer_result, "fun", None) is not None
            else None
        ),
        "optimizer_status_available": (
            hasattr(optimizer_result, "success")
            or hasattr(optimizer_result, "message")
        ),
        "optimizer_success": getattr(optimizer_result, "success", None),
    }


def predict_vqc(model: VQC, features) -> dict:
    """Return class labels and sampler-derived class probabilities."""
    x = np.asarray(features, dtype=float)
    if x.ndim != 2 or not np.isfinite(x).all():
        raise ValueError("features must be a finite 2D array")
    if x.shape[1] != model.num_qubits:
        raise ValueError(f"features must have {model.num_qubits} columns")
    probabilities = np.asarray(model.predict_proba(x), dtype=float)
    if probabilities.ndim != 2 or probabilities.shape[0] != len(x):
        raise RuntimeError("VQC returned probabilities with an invalid shape")
    labels = np.asarray(model.predict(x))
    if labels.ndim == 2:
        labels = np.argmax(labels, axis=1)
    else:
        labels = labels.reshape(-1)
    if len(labels) != len(x):
        raise RuntimeError("VQC returned predictions with an invalid shape")
    return {
        "predictions": labels.tolist(),
        "probabilities": probabilities.tolist(),
    }


def restore_vqc_weights(model: VQC, weights) -> VQC:
    """Restore learned parameters without fitting or serializing Qiskit closures."""
    values = np.asarray(weights, dtype=float)
    expected = int(model.ansatz.num_parameters)
    if values.shape != (expected,) or not np.isfinite(values).all():
        raise ValueError(f"Expected {expected} finite trained VQC weights")
    result = OptimizerResult()
    result.x = values
    model._fit_result = result
    model._num_classes = 2
    model._neural_network.set_interpret(model.interpret, 2)
    return model
