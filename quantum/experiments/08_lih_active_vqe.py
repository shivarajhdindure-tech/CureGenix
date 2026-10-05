from qiskit_nature.units import DistanceUnit
from qiskit_nature.second_q.drivers import PySCFDriver
from qiskit_nature.second_q.transformers import ActiveSpaceTransformer
from qiskit_nature.second_q.mappers import JordanWignerMapper

from qiskit_nature.second_q.algorithms import GroundStateEigensolver
from qiskit_algorithms import VQE
from qiskit_algorithms.optimizers import SLSQP
from qiskit.circuit.library import TwoLocal
from qiskit.primitives import StatevectorEstimator


# ============================================
# CUREGENIX QUANTUM
# LiH ACTIVE-SPACE VQE
# ============================================

# 1. Full LiH molecular problem
driver = PySCFDriver(
    atom="Li 0 0 0; H 0 0 1.6",
    basis="sto3g",
    charge=0,
    spin=0,
    unit=DistanceUnit.ANGSTROM,
)

problem = driver.run()


# ============================================
# 2. Active-space reduction
# ============================================

transformer = ActiveSpaceTransformer(
    num_electrons=2,
    num_spatial_orbitals=2,
)

active_problem = transformer.transform(problem)


# ============================================
# 3. Jordan-Wigner mapper
# ============================================

mapper = JordanWignerMapper()


# ============================================
# 4. VQE ansatz
# ============================================

ansatz = TwoLocal(
    num_qubits=4,
    rotation_blocks="ry",
    entanglement_blocks="cz",
    entanglement="full",
    reps=2,
)


# ============================================
# 5. Optimizer
# ============================================

optimizer = SLSQP(maxiter=100)


# ============================================
# 6. Estimator
# ============================================

estimator = StatevectorEstimator()


# ============================================
# 7. VQE
# ============================================

vqe = VQE(
    estimator=estimator,
    ansatz=ansatz,
    optimizer=optimizer,
)


# ============================================
# 8. Ground-state solver
# ============================================

solver = GroundStateEigensolver(
    mapper,
    vqe,
)


# ============================================
# 9. Solve active-space problem
# ============================================

result = solver.solve(active_problem)


# ============================================
# 10. Display results
# ============================================

print("\n==============================")
print("     CUREGENIX QUANTUM")
print("==============================")
print("Molecule          : LiH")
print("Basis             : STO-3G")
print("Active electrons  : 2")
print("Active orbitals   : 2")
print("Qubits            : 4")
print("Method            : VQE")
print("Mapping           : Jordan-Wigner")
print()

print("Electronic energy:")
print(f"{result.electronic_energies[0]:.12f} Hartree")

print()
print("Nuclear repulsion:")
print(f"{result.nuclear_repulsion_energy:.12f} Hartree")

print()
print("Total molecular energy:")
print(
    f"{result.electronic_energies[0] + result.nuclear_repulsion_energy:.12f}"
    " Hartree"
)

print("==============================")