from qiskit_nature.units import DistanceUnit
from qiskit_nature.second_q.drivers import PySCFDriver
from qiskit_nature.second_q.transformers import ActiveSpaceTransformer


# ============================================
# CUREGENIX QUANTUM
# H2 ACTIVE SPACE
# ============================================

# 1. Build the full molecular problem
driver = PySCFDriver(
    atom="H 0 0 0; H 0 0 0.735",
    basis="sto3g",
    charge=0,
    spin=0,
    unit=DistanceUnit.ANGSTROM,
)

problem = driver.run()


# ============================================
# 2. Display original system
# ============================================

print("\n==============================")
print("     CUREGENIX QUANTUM")
print("==============================")
print("Molecule       : H2")
print("Basis          : STO-3G")
print("Original system")
print("------------------------------")
print("Particles      :", problem.num_particles)
print("Spatial orbitals:", problem.num_spatial_orbitals)


# ============================================
# 3. Create active-space transformer
# ============================================

transformer = ActiveSpaceTransformer(
    num_electrons=2,
    num_spatial_orbitals=2,
)


# ============================================
# 4. Reduce the molecular problem
# ============================================

active_problem = transformer.transform(problem)


# ============================================
# 5. Display active-space system
# ============================================

print()
print("ACTIVE SPACE")
print("------------------------------")
print("Active electrons :", active_problem.num_particles)
print("Active orbitals  :", active_problem.num_spatial_orbitals)

print()
print("Active-space Hamiltonian")
print("------------------------------")

active_hamiltonian = active_problem.hamiltonian.second_q_op()

print(active_hamiltonian)

print("==============================")