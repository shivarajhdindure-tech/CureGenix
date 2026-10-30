"""Small, reproducible Aer validation of one-qubit readout mitigation.

This is a synthetic simulator diagnostic only. It does not use IBM Runtime,
VQE, credentials, or hardware and makes no claim about QPU performance.
"""

from __future__ import annotations

import json
import math
from importlib.metadata import version
from typing import Any

import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, ReadoutError


def _validate_probability(value: float, name: str) -> float:
    value = float(value)
    if not math.isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be finite and in [0, 1].")
    return value


def _counts(backend: AerSimulator, circuit: QuantumCircuit, shots: int, seed: int) -> dict[str, int]:
    compiled = transpile(circuit, backend, seed_transpiler=seed)
    result = backend.run(compiled, shots=shots, seed_simulator=seed).result()
    return {key.replace(" ", ""): int(value) for key, value in result.get_counts().items()}


def _z_estimates(
    counts: dict[str, int], calibration_p_1_given_0: float, calibration_p_0_given_1: float,
) -> tuple[float, float, float]:
    """Return raw Z, inverse-calibrated Z, and conditional sampling SE."""
    shots = sum(counts.values())
    if shots < 2:
        raise ValueError("At least two shots are required to estimate uncertainty.")
    observed = np.array([counts.get("0", 0), counts.get("1", 0)], dtype=float) / shots
    # Columns are prepared states; rows are measured states.
    confusion = np.array([
        [1.0 - calibration_p_1_given_0, calibration_p_0_given_1],
        [calibration_p_1_given_0, 1.0 - calibration_p_0_given_1],
    ])
    if abs(float(np.linalg.det(confusion))) < 1e-12:
        raise ValueError("Readout calibration matrix is singular.")
    inverse = np.linalg.inv(confusion)
    z = np.array([1.0, -1.0])
    corrected_per_outcome = z @ inverse
    raw_values = np.array([1.0, -1.0])
    raw_mean = float(raw_values @ observed)
    corrected_mean = float(corrected_per_outcome @ observed)

    def sample_se(values: np.ndarray, mean: float) -> float:
        sum_squares = sum(
            counts.get(str(index), 0) * (float(values[index]) - mean) ** 2
            for index in (0, 1)
        )
        return math.sqrt(sum_squares / (shots - 1) / shots)

    return raw_mean, corrected_mean, sample_se(corrected_per_outcome, corrected_mean)


def _evaluate(
    *, shots: int, seed: int, actual_p_1_given_0: float,
    actual_p_0_given_1: float, calibration_p_1_given_0: float,
    calibration_p_0_given_1: float,
) -> dict[str, Any]:
    noise = NoiseModel()
    noise.add_all_qubit_readout_error(ReadoutError([
        [1.0 - actual_p_1_given_0, actual_p_1_given_0],
        [actual_p_0_given_1, 1.0 - actual_p_0_given_1],
    ]))
    circuit = QuantumCircuit(1, 1)
    circuit.x(0)  # Prepare |1>; measure Pauli Z.
    circuit.measure(0, 0)
    backend = AerSimulator(noise_model=noise)
    measured = _counts(backend, circuit, shots, seed)
    raw, mitigated, mitigated_se = _z_estimates(
        measured, calibration_p_1_given_0, calibration_p_0_given_1,
    )
    raw_se = math.sqrt(max(0.0, 1.0 - raw * raw) / shots)
    return {
        "ideal_expectation_z": -1.0,
        "counts": measured,
        "raw_unmitigated": {"expectation_z": raw, "standard_error": raw_se},
        "readout_mitigated": {
            "expectation_z": mitigated,
            "standard_error_conditional_on_calibration": mitigated_se,
            "method": "inverse of the declared 2x2 readout assignment matrix",
        },
        "absolute_error_from_ideal": {
            "raw": abs(raw + 1.0),
            "readout_mitigated": abs(mitigated + 1.0),
        },
    }


def run_readout_mitigation_validation(shots: int = 8192, seed: int = 20261030) -> dict[str, Any]:
    """Compare ideal, noisy, and readout-corrected Z estimates in seeded Aer runs."""
    if not isinstance(shots, int) or isinstance(shots, bool) or shots < 2:
        raise ValueError("shots must be an integer of at least 2.")
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise ValueError("seed must be an integer.")

    p_1_given_0 = _validate_probability(0.05, "p(1|0)")
    p_0_given_1 = _validate_probability(0.20, "p(0|1)")
    calibrated = _evaluate(
        shots=shots, seed=seed,
        actual_p_1_given_0=p_1_given_0, actual_p_0_given_1=p_0_given_1,
        calibration_p_1_given_0=p_1_given_0, calibration_p_0_given_1=p_0_given_1,
    )

    # Deliberate calibration mismatch: actual readout is ideal, but correction
    # assumes symmetric 10% assignment errors. This is a counterexample, not a
    # proposed calibration procedure.
    mismatch = _evaluate(
        shots=shots, seed=seed + 1,
        actual_p_1_given_0=0.0, actual_p_0_given_1=0.0,
        calibration_p_1_given_0=0.10, calibration_p_0_given_1=0.10,
    )
    return {
        "schema_version": 1,
        "execution_type": "local_noisy_simulation",
        "simulator": "Qiskit Aer AerSimulator",
        "qiskit_versions": {
            "qiskit": version("qiskit"),
            "qiskit_aer": version("qiskit-aer"),
        },
        "seed": seed,
        "shots_per_scenario": shots,
        "measurement_setup": {
            "qubits": 1,
            "prepared_state": "|1>",
            "observable": "Pauli Z",
            "bit_convention": "measured 0 maps to +1; measured 1 maps to -1",
            "ideal_expectation_z": -1.0,
        },
        "controlled_readout_noise": {
            "assumption": "independent assignment errors; p(measure 1 | prepare 0)=0.05; p(measure 0 | prepare 1)=0.20",
            "calibration": "exact synthetic assignment matrix matching the configured simulator noise",
            **calibrated,
        },
        "calibration_mismatch_counterexample": {
            "assumption": "actual readout is ideal; mitigation incorrectly assumes symmetric 10% assignment errors",
            "calibration": "intentionally mismatched synthetic assignment matrix",
            **mismatch,
        },
        "limitations": [
            "Synthetic one-qubit readout noise only; no gate, crosstalk, drift, or hardware noise model.",
            "Mitigated standard error is conditional on the supplied calibration matrix and excludes calibration-estimation uncertainty.",
            "No VQE, IBM Runtime, credentials, or hardware jobs are used.",
        ],
    }


if __name__ == "__main__":
    print(json.dumps(run_readout_mitigation_validation(), indent=2, allow_nan=False))
