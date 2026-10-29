
from qiskit.quantum_info import Statevector

from quantum.chemistry.molecule import build_molecular_problem
from quantum.chemistry.active_space import reduce_to_active_space
from quantum.chemistry.hamiltonian import build_qubit_hamiltonian
from quantum.algorithms.exact_solver import run_exact_solver
from qiskit_algorithms import NumPyMinimumEigensolver
from qiskit_nature.second_q.mappers import JordanWignerMapper
from qiskit_nature.second_q.algorithms import GroundStateEigensolver

# LiH equilibrium-like geometry, distances in Angstrom.
# This is a diagnostic geometry, not a geometry optimization.
geometry = (
    "Li 0.000000 0.000000 0.000000; "
    "H 0.000000 0.000000 1.600000"
)

problem = build_molecular_problem(
    atom=geometry,
    basis="sto3g",
    charge=0,
    spin=0,
)

print("Molecule: LiH")
print("Basis: STO-3G")
print("Charge: 0")
print("Spin: 0")
print("Particle counts (alpha, beta):", problem.num_particles)
print("Spatial orbitals:", problem.num_spatial_orbitals)

# Start with a 2-electron, 2-spatial-orbital active space.
# We will verify the resulting dimensions before benchmarking.
alpha, beta = problem.num_particles
occupied = (alpha + beta) // 2

active_problem = reduce_to_active_space(
    problem,
    num_electrons=2,
    num_spatial_orbitals=2,
    active_orbitals=[occupied - 1, occupied],
)

hamiltonian = build_qubit_hamiltonian(active_problem)
reference = run_exact_solver(hamiltonian)
solver = GroundStateEigensolver(
    JordanWignerMapper(),
    NumPyMinimumEigensolver(),
)

ground_state = solver.solve(active_problem)

print("\n--- Independent active-space check ---")
print("Ground-state electronic eigenvalue(s):", ground_state.eigenvalues)
print("Ground-state total energy:", ground_state.total_energies)
print("Exact full-space minimum:", reference["exact_energy_hartree"])

print("\nActive-space particle counts:", active_problem.num_particles)
print("Active-space spatial orbitals:", active_problem.num_spatial_orbitals)
print("Qubit count:", hamiltonian.num_qubits)
print("Full qubit-space minimum (Ha):", reference["exact_energy_hartree"])
print(
    "Active-space constants:",
    active_problem.hamiltonian.constants,
)
print(
    "\nCaution: the full qubit-space minimum is not automatically "
    "guaranteed to lie in the intended physical particle-number and spin sector."
)
