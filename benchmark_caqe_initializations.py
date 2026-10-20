import random
import statistics
import time

from quantum.chemistry.smiles_adapter import smiles_to_geometry
from quantum.chemistry.molecule import build_molecular_problem
from quantum.chemistry.active_space import reduce_to_active_space
from quantum.chemistry.hamiltonian import build_qubit_hamiltonian
from quantum.algorithms.vqe import run_vqe
from quantum.algorithms.caqe import run_caqe
from quantum.algorithms.exact_solver import run_exact_solver


TRIALS = 5
MAXITER = 50
CAQE_STARTS = 3
SEED_BASE = 2026


def mean_sd(values):
    mean = statistics.mean(values)
    sd = statistics.stdev(values) if len(values) > 1 else 0.0
    return mean, sd


# Build one fixed water Hamiltonian.
geometry = smiles_to_geometry("O")
problem = build_molecular_problem(
    atom=geometry,
    basis="sto3g",
    charge=0,
    spin=0,
)

alpha, beta = problem.num_particles
occupied = (alpha + beta) // 2

active_problem = reduce_to_active_space(
    problem,
    num_electrons=2,
    num_spatial_orbitals=2,
    active_orbitals=[occupied - 1, occupied],
)

hamiltonian = build_qubit_hamiltonian(active_problem)
num_qubits = hamiltonian.num_qubits

# Determine ansatz parameter count using the same ansatz structure as CAQE.
from qiskit.circuit.library import n_local

ansatz = n_local(
    num_qubits=num_qubits,
    rotation_blocks=["ry"],
    entanglement_blocks=["cz"],
    entanglement="full",
    reps=2,
)
parameter_count = ansatz.num_parameters

reference = run_exact_solver(hamiltonian)
exact_energy = reference["exact_energy_hartree"]

correction = float(
    active_problem.hamiltonian.constants["ActiveSpaceTransformer"]
)
nuclear_repulsion = float(
    active_problem.hamiltonian.constants["nuclear_repulsion_energy"]
)

baseline_results = []
caqe_results = []

print(f"Water Hamiltonian: {num_qubits} qubits")
print(f"Ansatz parameters: {parameter_count}")
print(f"Exact qubit-space reference: {exact_energy:.12f} Ha")
print(f"Trials: {TRIALS}; CAQE starts per trial: {CAQE_STARTS}")
print("Initializations use deterministic but distinct seeds.")
print("These are simulator experiments, not quantum hardware runs.")

for trial in range(TRIALS):
    seed = SEED_BASE + trial
    rng = random.Random(seed)

    # Distinct, reproducible parameter vectors for every trial.
    initializations = [
        [rng.uniform(-3.14159, 3.14159) for _ in range(parameter_count)]
        for _ in range(CAQE_STARTS)
    ]

    print(f"\n--- Trial {trial + 1}/{TRIALS}, seed={seed} ---")

    # Baseline uses the first initialization from this trial.
    start = time.perf_counter()
    baseline = run_vqe(
        hamiltonian,
        num_qubits=num_qubits,
        maxiter=MAXITER,
        initial_point=initializations[0],
    )
    baseline_runtime = time.perf_counter() - start

    baseline_energy = float(baseline["electronic_energy"])
    baseline_error = abs(baseline_energy - exact_energy)

    baseline_results.append({
        "trial": trial + 1,
        "seed": seed,
        "energy": baseline_energy,
        "error": baseline_error,
        "runtime": baseline_runtime,
    })

    # CAQE uses the same first start plus two additional starts.
    start = time.perf_counter()
    adaptive = run_caqe(
        hamiltonian,
        maxiter=MAXITER,
        initializations=initializations,
        max_starts=CAQE_STARTS,
        stability_tolerance=None,
        active_space_correction=correction,
        nuclear_repulsion_energy=nuclear_repulsion,
    )
    caqe_runtime = adaptive["total_vqe_runtime_seconds"]

    best = adaptive["best_run"]
    caqe_error = abs(best["energy_hartree"] - exact_energy)

    caqe_results.append({
        "trial": trial + 1,
        "seed": seed,
        "energy": best["energy_hartree"],
        "error": caqe_error,
        "runtime": caqe_runtime,
        "evaluations": sum(
            run["evaluations"] for run in adaptive["runs"]
        ),
        "starts": adaptive["starts_completed"],
    })

    print(
        f"Baseline: error={baseline_error:.6e} Ha, "
        f"runtime={baseline_runtime:.3f}s"
    )
    print(
        f"CAQE:     error={caqe_error:.6e} Ha, "
        f"runtime={caqe_runtime:.3f}s, "
        f"evaluations={caqe_results[-1]['evaluations']}"
    )


def summarize(label, rows):
    errors = [row["error"] for row in rows]
    runtimes = [row["runtime"] for row in rows]
    error_mean, error_sd = mean_sd(errors)
    runtime_mean, runtime_sd = mean_sd(runtimes)

    print(f"\n{label}")
    print(f"  Error mean ± SD: {error_mean:.6e} ± {error_sd:.6e} Ha")
    print(f"  Runtime mean ± SD: {runtime_mean:.3f} ± {runtime_sd:.3f} s")

    if "evaluations" in rows[0]:
        values = [row["evaluations"] for row in rows]
        value_mean, value_sd = mean_sd(values)
        print(
            f"  Evaluations mean ± SD: "
            f"{value_mean:.1f} ± {value_sd:.1f}"
        )


print("\n========== INITIALIZATION ROBUSTNESS SUMMARY ==========")
summarize("Baseline VQE", baseline_results)
summarize("CAQE", caqe_results)

baseline_mean_error = statistics.mean(r["error"] for r in baseline_results)
caqe_mean_error = statistics.mean(r["error"] for r in caqe_results)

caqe_wins = sum(
    c["error"] < b["error"]
    for b, c in zip(baseline_results, caqe_results)
)

print(f"CAQE lower-error trials: {caqe_wins}/{TRIALS}")

if baseline_mean_error > 0:
    reduction = (
        (baseline_mean_error - caqe_mean_error)
        / baseline_mean_error
        * 100
    )
    print(f"\nMean error reduction vs baseline: {reduction:.2f}%")

print(f"CAQE lower-error trials: {baseline_wins}/{TRIALS}")

print("\nPer-trial comparison:")
for baseline, caqe in zip(baseline_results, caqe_results):
    print(
        f"Trial {baseline['trial']}: "
        f"baseline_error={baseline['error']:.6e}, "
        f"CAQE_error={caqe['error']:.6e}, "
        f"CAQE_wins={caqe['error'] < baseline['error']}"
    )

print(
    "\nCaveat: this tests optimizer initialization sensitivity on one small "
    "simulated Hamiltonian. The exact reference is the full qubit-space "
    "minimum; physical particle-number and spin-sector validity must be "
    "checked separately. No quantum advantage is established."
)