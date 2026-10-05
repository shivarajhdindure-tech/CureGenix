from qiskit_nature.units import DistanceUnit
from qiskit_nature.second_q.drivers import PySCFDriver
from qiskit_nature.second_q.transformers import ActiveSpaceTransformer


# ============================================
# CUREGENIX QUANTUM
# LiH ACTIVE-SPACE EXPERIMENT
# ============================================

# 1. Build the full LiH molecular problem
driver = PySCFDriver(
    atom="Li 0 0 0; H 0 0 1.6",
    basis="sto3g",
    charge=0,
    spin=0,
    unit=DistanceUnit.ANGSTROM,
)

problem = driver.run()


# ============================================
# 2. Display original problem
# ============================================

print("\n==============================")
print("     CUREGENIX QUANTUM")
print("==============================")
print("Molecule        : LiH")
print("Basis           : STO-3G")
print()
print("FULL MOLECULAR SYSTEM")
print("------------------------------")
print("Particles       :", problem.num_particles)
print("Spatial orbitals:", problem.num_spatial_orbitals)


# ============================================
# 3. Select active space
# ============================================

transformer = ActiveSpaceTransformer(
    num_electrons=2,
    num_spatial_orbitals=2,
)


# ============================================
# 4. Transform
# ============================================

active_problem = transformer.transform(problem)


# ============================================
# 5. Display reduced problem
# ============================================

print()
print("ACTIVE SPACE")
print("------------------------------")
print("Active electrons :", active_problem.num_particles)
print("Active orbitals  :", active_problem.num_spatial_orbitals)

print()
print("ACTIVE-SPACE HAMILTONIAN")
print("------------------------------")

active_hamiltonian = active_problem.hamiltonian.second_q_op()

print(active_hamiltonian)

print("==============================")