
import time

from qiskit_algorithms import VQE
from qiskit_algorithms.optimizers import SLSQP
from qiskit.circuit.library import n_local
from qiskit.primitives import StatevectorEstimator

from quantum.algorithms.exact_solver import run_exact_solver


def run_caqe(
    qubit_hamiltonian,
    maxiter=100,
    initializations=None,
    max_starts=3,
    stability_tolerance=None,
    active_space_correction=None,
    nuclear_repulsion_energy=None,
):
    """
    Experimental adaptive multi-start VQE.

    The first initialization matches the baseline VQE.
    Optional energy stability can stop additional starts,
    but does not establish closeness to the true minimum.
    """

    if max_starts < 1:
        raise ValueError("max_starts must be at least 1")

    num_qubits = qubit_hamiltonian.num_qubits

    ansatz = n_local(
        num_qubits=num_qubits,
        rotation_blocks=["ry"],
        entanglement_blocks=["cz"],
        entanglement="full",
        reps=2,
    )

    parameter_count = ansatz.num_parameters

    if initializations is None:
        initializations = [
            [0.1 * ((i % 5) - 2) for i in range(parameter_count)],
            [0.2 * ((i % 7) - 3) for i in range(parameter_count)],
            [0.05 * (i + 1) for i in range(parameter_count)],
        ]

    valid_initializations = [
        list(point)
        for point in initializations
        if len(point) == parameter_count
    ][:max_starts]

    if not valid_initializations:
        raise ValueError(
            "No valid initializations match the ansatz parameters."
        )

    runs = []
    total_runtime = 0.0
    stop_reason = "start_budget_exhausted"

    for run_index, initial_point in enumerate(
        valid_initializations, start=1
    ):
        history = []

        def callback(eval_count, parameters, energy, metadata):
            history.append({
                "evaluation": int(eval_count),
                "energy_hartree": float(energy),
            })

        vqe = VQE(
            estimator=StatevectorEstimator(),
            ansatz=ansatz,
            optimizer=SLSQP(maxiter=maxiter),
            initial_point=initial_point,
            callback=callback,
        )

        start = time.perf_counter()
        result = vqe.compute_minimum_eigenvalue(
            qubit_hamiltonian
        )
        runtime = time.perf_counter() - start
        total_runtime += runtime

        optimizer_result = result.optimizer_result

        runs.append({
            "run": run_index,
            "energy_hartree": float(result.eigenvalue.real),
            "runtime_seconds": runtime,
            "evaluations": optimizer_result.nfev,
            "gradient_evaluations": optimizer_result.njev,
            "iterations": optimizer_result.nit,
            "optimizer_success": getattr(
                optimizer_result, "success", None
            ),
            "optimizer_message": getattr(
                optimizer_result, "message", None
            ),
            "convergence_history": history,
        })

        # Stop only after at least two runs if the best energy
        # has changed by no more than the configured tolerance.
        if (
            stability_tolerance is not None
            and len(runs) >= 2
        ):
            previous_best = min(
                run["energy_hartree"] for run in runs[:-1]
            )
            current_best = min(
                run["energy_hartree"] for run in runs
            )

            if abs(previous_best - current_best) <= stability_tolerance:
                stop_reason = "best_energy_stable"
                break

    # Exact reference is for benchmark validation only.
    exact_start = time.perf_counter()
    exact = run_exact_solver(qubit_hamiltonian)
    exact_runtime = time.perf_counter() - exact_start
    exact_energy = exact["exact_energy_hartree"]

    for run in runs:
        run["absolute_error_hartree"] = abs(
            run["energy_hartree"] - exact_energy
        )

        if active_space_correction is not None:
            corrected_electronic = (
                run["energy_hartree"] + active_space_correction
            )
            run["corrected_electronic_energy_hartree"] = (
                corrected_electronic
            )

            if nuclear_repulsion_energy is not None:
                run["total_molecular_energy_hartree"] = (
                    corrected_electronic + nuclear_repulsion_energy
                )

    best_run = min(runs, key=lambda item: item["energy_hartree"])

    result_data = {
        "method": "CAQE experimental adaptive multi-start VQE",
        "num_qubits": num_qubits,
        "parameter_count": parameter_count,
        "max_starts": max_starts,
        "starts_completed": len(runs),
        "stop_reason": stop_reason,
        "total_vqe_runtime_seconds": total_runtime,
        "exact_reference_energy_hartree": exact_energy,
        "exact_reference_runtime_seconds": exact_runtime,
        "runs": runs,
        "best_run": best_run,
        "limitations": [
            "Energy stability between starts does not guarantee accuracy.",
            "Exact reference is the full qubit-space minimum.",
            "Physical particle-number and spin sector must be validated.",
            "Exact diagonalization is intended for small benchmarks.",
            "No quantum advantage is established.",
        ],
    }

    if active_space_correction is not None:
        result_data["active_space_correction_hartree"] = (
            active_space_correction
        )

    if nuclear_repulsion_energy is not None:
        result_data["nuclear_repulsion_energy_hartree"] = (
            nuclear_repulsion_energy
        )

    return result_data
