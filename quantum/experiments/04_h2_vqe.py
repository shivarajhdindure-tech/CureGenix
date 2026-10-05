from qiskit_nature.units import DistanceUnit
from qiskit_nature.second_q.drivers import PySCFDriver
from qiskit_nature.second_q.mappers import JordanWignerMapper

from qiskit_algorithms import VQE
from qiskit_algorithms.optimizers import SLSQP

from qiskit.circuit.library import TwoLocal
from qiskit.primitives import StatevectorEstimator


# ============================================
# CUREGENIX QUANTUM
# H2 VQE
# ============================================

# --------------------------------------------
# 1. Build H2 molecular problem
# --------------------------------------------

driver = PySCFDriver(
    atom="H 0 0 0; H 0 0 0.735",
    basis="sto3g",
    charge=0,
    spin=0,
    unit=DistanceUnit.ANGSTROM,
)

problem = driver.run()


# --------------------------------------------
# 2. Get fermionic Hamiltonian
# --------------------------------------------

fermionic_hamiltonian = problem.hamiltonian.second_q_op()


# --------------------------------------------
# 3. Map fermions -> qubits
# --------------------------------------------

mapper = JordanWignerMapper()

qubit_hamiltonian = mapper.map(fermionic_hamiltonian)


# --------------------------------------------
# 4. Create quantum ansatz
# --------------------------------------------

ansatz = TwoLocal(
    num_qubits=4,
    rotation_blocks="ry",
    entanglement_blocks="cz",
    entanglement="full",
    reps=2,
)


# --------------------------------------------
# 5. Create optimizer
# --------------------------------------------

optimizer = SLSQP(maxiter=100)


# --------------------------------------------
# 6. Create estimator
# --------------------------------------------

estimator = StatevectorEstimator()


# --------------------------------------------
# 7. Create VQE
# --------------------------------------------

vqe = VQE(
    estimator,
    ansatz,
    optimizer,
)


# --------------------------------------------
# 8. Run VQE
# --------------------------------------------

result = vqe.compute_minimum_eigenvalue(
    qubit_hamiltonian
)


# --------------------------------------------
# 9. Display result
# --------------------------------------------

print("\n==============================")
print("     CUREGENIX QUANTUM")
print("==============================")
print("Algorithm : VQE")
print("Molecule  : H2")
print("Qubits    : 4")
print("Mapping   : Jordan-Wigner")
print()
print(f"Ground-state energy: {result.eigenvalue.real:.12f} Hartree")
print("==============================")