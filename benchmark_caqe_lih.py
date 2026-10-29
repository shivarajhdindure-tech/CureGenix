
import random
import statistics
import time

from qiskit.circuit.library import n_local

from quantum.chemistry.molecule import build_molecular_problem
from quantum.chemistry.active_space import reduce_to_active_space
from quantum.chemistry.hamiltonian import build_qubit_hamiltonian
from quantum.algorithms.vqe import run_vqe
from quantum.algorithms.caqe import run_caqe
from quantum.algorithms.exact_solver import run_exact_solver


TRIALS = 5
MAXITER = 50
CAQE_STARTS = 3
SEED_BASE = 2030

# LiH geometry in Angstrom.
GEOMETRY = (
    "Li 0.000000 0.000000 0.000000; "
    "H 0.000000 0.000000 1.600000"
)


def mean_sd(values):
    mean = statistics.mean(values)
    sd = statistics.stdev(values) if len(values) > 1 else 0.0
    return mean, sd


# Build the molecular problem.
problem = build_molecular_problem(
    atom=GEOMETRY,
    basis="sto3g",
    charge=0,
    spin=0,
)

alpha, beta = problem.num_particles
occupied = (alpha + beta) // 2

# Same active space as the validated diagnostic.
active_problem = reduce_to_active_space(
    problem,
    num_electrons=2,
    num_spatial_orbitals=2,
    active_orbitals=[occupied - 1, occupied],
)

hamiltonian = build_qubit_hamiltonian(active_problem)
num_qubits = hamiltonian.num_qubits

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

print("========== LiH CAQE BENCHMARK ==========")
print("Basis: STO-3G")
print("Geometry: Li-H distance 1.6 Angstrom")
print("Original alpha/beta electrons:", problem.num_particles)
print("Active alpha/beta electrons:", active_problem.num_particles)
print("Active spatial orbitals:", active_problem.num_spatial_orbitals)
print("Qubits:", num_qubits)
print("Ansatz parameters:", parameter_count)
print(f"Exact qubit-space reference: {exact_energy:.12f} Ha")
print(f"Trials: {TRIALS}; CAQE starts per trial: {CAQE_STARTS}")
print("Simulator experiment only; no quantum hardware execution.")

for trial in range(TRIALS):
    seed = SEED_BASE + trial
    rng = random.Random(seed)

    initializations = [
        [rng.uniform(-3.14159, 3.14159) for _ in range(parameter_count)]
        for _ in range(CAQE_STARTS)
    ]

    # Baseline uses the same first start used by CAQE.
    start = time.perf_counter()
    baseline = run_vqe(
        hamiltonian,
        num_qubits=num_qubits,
        maxiter=MAXITER,
        initial_point=initializations[0],
    )
    baseline_runtime = time.perf_counter() - start

    baseline_energy = baseline["electronic_energy"]
    baseline_error = abs(baseline_energy - exact_energy)

    baseline_results.append({
        "trial": trial + 1,
        "error": baseline_error,
        "runtime": baseline_runtime,
        "evaluations": baseline["evaluations"],
    })

    adaptive = run_caqe(
        hamiltonian,
        maxiter=MAXITER,
        initializations=initializations,
        max_starts=CAQE_STARTS,
        stability_tolerance=None,
        active_space_correction=correction,
        nuclear_repulsion_energy=nuclear_repulsion,
    )

    # CAQE reports summed optimizer runtime, excluding exact diagonalization.
    caqe_runtime = adaptive["total_vqe_runtime_seconds"]
    best = adaptive["best_run"]
    caqe_error = abs(best["energy_hartree"] - exact_energy)

    caqe_results.append({
        "trial": trial + 1,
        "error": caqe_error,
        "runtime": caqe_runtime,
        "evaluations": sum(
            run["evaluations"] for run in adaptive["runs"]
        ),
        "starts": adaptive["starts_completed"],
        "total_energy": best.get("total_molecular_energy_hartree"),
    })

    print(f"\nTrial {trial + 1}, seed={seed}")
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
    error_mean, error_sd = mean_sd([r["error"] for r in rows])
    runtime_mean, runtime_sd = mean_sd([r["runtime"] for r in rows])
    eval_mean, eval_sd = mean_sd([r["evaluations"] for r in rows])

    print(f"\n{label}")
    print(f"Mean absolute error: {error_mean:.6e} ± {error_sd:.6e} Ha")
    print(f"Mean runtime: {runtime_mean:.3f} ± {runtime_sd:.3f} s")
    print(f"Mean evaluations: {eval_mean:.1f} ± {eval_sd:.1f}")


print("\n========== SUMMARY ==========")
summarize("Baseline VQE", baseline_results)
summarize("CAQE", caqe_results)

baseline_mean_error = statistics.mean(r["error"] for r in baseline_results)
caqe_mean_error = statistics.mean(r["error"] for r in caqe_results)

wins = sum(
    c["error"] < b["error"]
    for b, c in zip(baseline_results, caqe_results)
)
ties = sum(
    c["error"] == b["error"]
    for b, c in zip(baseline_results, caqe_results)
)

if baseline_mean_error > 0:
    reduction = (
        (baseline_mean_error - caqe_mean_error)
        / baseline_mean_error
        * 100
    )
    print(f"\nMean error reduction: {reduction:.2f}%")

print(f"CAQE lower-error trials: {wins}/{TRIALS}")
print(f"Equal-error trials: {ties}/{TRIALS}")

print(
    "\nLimitations: one small active-space Hamiltonian; "
    "the full qubit-space minimum must be checked against the "
    "intended physical sector. The reduced model is not a full "
    "six-electron LiH calculation. No quantum advantage is established."
)
