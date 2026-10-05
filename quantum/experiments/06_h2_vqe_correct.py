from qiskit_nature.units import DistanceUnit
from qiskit_nature.second_q.drivers import PySCFDriver
from qiskit_nature.second_q.mappers import JordanWignerMapper

from qiskit_nature.second_q.algorithms import GroundStateEigensolver
from qiskit_algorithms import VQE
from qiskit_algorithms.optimizers import SLSQP
from qiskit.circuit.library import TwoLocal
from qiskit.primitives import StatevectorEstimator


# ============================================
# CUREGENIX QUANTUM
# H2 - CHEMISTRY-AWARE VQE
# ============================================

# 1. Molecular problem
driver = PySCFDriver(
    atom="H 0 0 0; H 0 0 0.735",
    basis="sto3g",
    charge=0,
    spin=0,
    unit=DistanceUnit.ANGSTROM,
)

problem = driver.run()


# ============================================
# 2. Quantum ansatz
# ============================================

ansatz = TwoLocal(
    num_qubits=4,
    rotation_blocks="ry",
    entanglement_blocks="cz",
    entanglement="full",
    reps=2,
)


# ============================================
# 3. Optimizer
# ============================================

optimizer = SLSQP(maxiter=100)


# ============================================
# 4. Estimator
# ============================================

estimator = StatevectorEstimator()


# ============================================
# 5. VQE
# ============================================

vqe = VQE(
    estimator=estimator,
    ansatz=ansatz,
    optimizer=optimizer,
)


# ============================================
# 6. Ground-state solver
# ============================================

mapper = JordanWignerMapper()

solver = GroundStateEigensolver(
    mapper,
    vqe,
)


# ============================================
# 7. Solve
# ============================================

result = solver.solve(problem)


# ============================================
# 8. Display
# ============================================

print("\n==============================")
print("     CUREGENIX QUANTUM")
print("==============================")
print("Molecule       : H2")
print("Method         : VQE")
print("Mapping        : Jordan-Wigner")
print("Basis          : STO-3G")
print()

print("Electronic energy:")
print(f"{result.electronic_energies[0]:.12f} Hartree")

print()
print("Nuclear repulsion:")
print(f"{result.nuclear_repulsion_energy:.12f} Hartree")

print()
print("Total molecular energy:")
print(f"{result.electronic_energies[0] + result.nuclear_repulsion_energy:.12f} Hartree")

print("==============================")