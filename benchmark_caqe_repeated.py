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


def mean_std(values):
    mean = statistics.mean(values)
    std = statistics.stdev(values) if len(values) > 1 else 0.0
    return mean, std


# Build the water Hamiltonian once so every trial uses the same problem.
geometry = smiles_to_geometry("O")

problem = build_molecular_problem(
    atom=geometry,
    basis="sto3g",
    charge=0,
    spin=0,
)

alpha, beta = problem.num_particles
occupied_orbitals = (alpha + beta) // 2

active_problem = reduce_to_active_space(
    problem,
    num_electrons=2,
    num_spatial_orbitals=2,
    active_orbitals=[
        occupied_orbitals - 1,
        occupied_orbitals,
    ],
)

hamiltonian = build_qubit_hamiltonian(active_problem)

# Compute the exact reference once, outside the timed trial measurements.
reference = run_exact_solver(hamiltonian)
exact_energy = reference["exact_energy_hartree"]

baseline_results = []
caqe_results = []

print(f"Water benchmark: {hamiltonian.num_qubits} qubits")
print(f"Exact qubit-space reference: {exact_energy:.12f} Hartree")
print(f"Trials per method: {TRIALS}")
print("Note: runtimes are local simulator timings, not quantum hardware results.")

for trial in range(1, TRIALS + 1):
    print(f"\nTrial {trial}/{TRIALS}")

    # Baseline VQE
    start = time.perf_counter()
    baseline = run_vqe(
        hamiltonian,
        num_qubits=hamiltonian.num_qubits,
        maxiter=MAXITER,
    )
    baseline_runtime = time.perf_counter() - start

    baseline_energy = float(baseline["electronic_energy"])
    baseline_results.append({
        "energy": baseline_energy,
        "error": abs(baseline_energy - exact_energy),
        "runtime": baseline_runtime,
    })

    print(
        f"Baseline: error={baseline_results[-1]['error']:.6e} Ha, "
        f"runtime={baseline_runtime:.3f}s"
    )

    # CAQE: fixed number of starts, no early stopping.
    adaptive = run_caqe(
        hamiltonian,
        maxiter=MAXITER,
        max_starts=CAQE_STARTS,
        stability_tolerance=None,
        active_space_correction=float(
            active_problem.hamiltonian.constants[
                "ActiveSpaceTransformer"
            ]
        ),
        nuclear_repulsion_energy=float(
            active_problem.hamiltonian.constants[
                "nuclear_repulsion_energy"
            ]
        ),
    )

    best = adaptive["best_run"]
    caqe_results.append({
        "energy": best["energy_hartree"],
        "error": abs(best["energy_hartree"] - exact_energy),
        "runtime": adaptive["total_vqe_runtime_seconds"],
        "evaluations": sum(
            run["evaluations"] for run in adaptive["runs"]
        ),
        "starts": adaptive["starts_completed"],
    })

    print(
        f"CAQE:    error={caqe_results[-1]['error']:.6e} Ha, "
        f"runtime={caqe_results[-1]['runtime']:.3f}s, "
        f"evaluations={caqe_results[-1]['evaluations']}"
    )


def summarize(label, results):
    errors = [r["error"] for r in results]
    runtimes = [r["runtime"] for r in results]

    error_mean, error_std = mean_std(errors)
    time_mean, time_std = mean_std(runtimes)

    print(f"\n{label}")
    print(f"  Error mean ± SD: {error_mean:.6e} ± {error_std:.6e} Ha")
    print(f"  Runtime mean ± SD: {time_mean:.3f} ± {time_std:.3f} s")

    if "evaluations" in results[0]:
        evals = [r["evaluations"] for r in results]
        eval_mean, eval_std = mean_std(evals)
        print(f"  Evaluations mean ± SD: {eval_mean:.1f} ± {eval_std:.1f}")


print("\n========== REPEATED BENCHMARK SUMMARY ==========")
summarize("Baseline VQE", baseline_results)
summarize("CAQE (best of fixed multi-start budget)", caqe_results)

baseline_error = statistics.mean(r["error"] for r in baseline_results)
caqe_error = statistics.mean(r["error"] for r in caqe_results)
baseline_time = statistics.mean(r["runtime"] for r in baseline_results)
caqе_time = statistics.mean(r["runtime"] for r in caqe_results)

if baseline_error > 0:
    improvement = (baseline_error - caqe_error) / baseline_error * 100
    print(f"\nMean error reduction vs baseline: {improvement:.2f}%")
else:
    print("\nBaseline mean error is zero; percentage reduction is undefined.")

if baseline_time > 0:
    print(f"Mean runtime ratio (CAQE / baseline): {caqе_time / baseline_time:.2f}x")

print(
    "\nInterpretation: this compares optimizer outcomes on one fixed, "
    "small simulated Hamiltonian. It does not demonstrate quantum advantage "
    "or drug-discovery performance."
)
