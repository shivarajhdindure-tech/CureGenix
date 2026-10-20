
import time

from quantum.chemistry.smiles_adapter import smiles_to_geometry
from quantum.chemistry.molecule import build_molecular_problem
from quantum.chemistry.active_space import reduce_to_active_space
from quantum.chemistry.hamiltonian import build_qubit_hamiltonian
from quantum.algorithms.vqe import run_vqe
from quantum.algorithms.caqe import run_caqe

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

start = time.perf_counter()
baseline = run_vqe(
    hamiltonian,
    num_qubits=hamiltonian.num_qubits,
    maxiter=50,
)
baseline_runtime = time.perf_counter() - start


adaptive = run_caqe(
    hamiltonian,
    maxiter=50,
    max_starts=3,
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

print("\n--- Adaptive CAQE: Water ---")
print("Starts completed:", adaptive["starts_completed"])
print("Stop reason:", adaptive["stop_reason"])
print(
    "Total VQE runtime:",
    adaptive["total_vqe_runtime_seconds"]
)
print("Best raw energy:", adaptive["best_run"]["energy_hartree"])
print(
    "Full-space reference error:",
    adaptive["best_run"]["absolute_error_hartree"]
)
print(
    "Corrected total molecular energy:",
    adaptive["best_run"].get("total_molecular_energy_hartree")
)

best = adaptive["best_run"]

print("\n--- Water Hamiltonian benchmark ---")
print("Qubits:", hamiltonian.num_qubits)
print("Baseline VQE energy:", baseline["electronic_energy"])
print("Baseline runtime:", baseline_runtime)
print("Multi-start best energy:", best["energy_hartree"])
print("Multi-start best error:", best["absolute_error_hartree"])
print("Multi-start runs:", len(adaptive["runs"]))

for run in adaptive["runs"]:
    print(
        f"Run {run['run']}: "
        f"error={run['absolute_error_hartree']:.6e}, "
        f"evaluations={run['evaluations']}, "
        f"runtime={run['runtime_seconds']:.3f}s"
    )
