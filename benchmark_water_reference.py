
from quantum.chemistry.smiles_adapter import smiles_to_geometry
from quantum.chemistry.molecule import build_molecular_problem
from quantum.chemistry.active_space import reduce_to_active_space
from quantum.chemistry.hamiltonian import build_qubit_hamiltonian

from qiskit_nature.second_q.algorithms import GroundStateEigensolver
from qiskit_nature.second_q.mappers import JordanWignerMapper
from qiskit_algorithms import NumPyMinimumEigensolver


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

mapper = JordanWignerMapper()

# Full-qubit-space reference, for comparison.
qubit_hamiltonian = build_qubit_hamiltonian(active_problem)

full_result = NumPyMinimumEigensolver().compute_minimum_eigenvalue(
    qubit_hamiltonian
)

# Molecular problem-aware reference.
solver = GroundStateEigensolver(
    mapper,
    NumPyMinimumEigensolver(),
)

ground_state = solver.solve(active_problem)

print("Active-space particles:", active_problem.num_particles)
print("Full-qubit minimum eigenvalue:", float(full_result.eigenvalue.real))
print("Ground-state total energy:", ground_state.total_energies)
print("Ground-state eigenvalues:", ground_state.eigenvalues)
print("Ground-state result type:", type(ground_state).__name__)
