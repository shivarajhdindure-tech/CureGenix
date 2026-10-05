
from quantum.chemistry.molecule import build_molecular_problem
from quantum.chemistry.active_space import reduce_to_active_space

from qiskit_nature.second_q.mappers import JordanWignerMapper
from qiskit_nature.second_q.algorithms import GroundStateEigensolver

from qiskit_algorithms import VQE
from qiskit_algorithms.optimizers import SLSQP
from qiskit.circuit.library import n_local
from qiskit.primitives import StatevectorEstimator

# 1. Build LiH molecule
problem = build_molecular_problem(
    "Li 0 0 0; H 0 0 1.6"
)

# 2. Select active space
active_problem = reduce_to_active_space(
    problem,
    num_electrons=2,
    num_spatial_orbitals=2,
)

# 3. Build variational circuit
ansatz = n_local(
    num_qubits=4,
    rotation_blocks=["ry"],
    entanglement_blocks=["cz"],
    entanglement="full",
    reps=2,
)

# 4. Configure VQE
vqe = VQE(
    estimator=StatevectorEstimator(),
    ansatz=ansatz,
    optimizer=SLSQP(maxiter=100),
)

# 5. Use Qiskit Nature for energy interpretation
solver = GroundStateEigensolver(
    JordanWignerMapper(),
    vqe,
)

result = solver.solve(active_problem)

print("\n===== CUREGENIX LiH ENERGY TEST =====")
print("Electronic energy:", result.electronic_energies[0])
print("Nuclear repulsion:", result.nuclear_repulsion_energy)
print("Total molecular energy:", result.total_energies[0])
