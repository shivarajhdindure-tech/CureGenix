from qiskit_nature.units import DistanceUnit
from qiskit_nature.second_q.drivers import PySCFDriver
from qiskit_nature.second_q.mappers import JordanWignerMapper


# ============================================
# CUREGENIX QUANTUM
# H2 -> Fermionic Hamiltonian -> Qubit Hamiltonian
# ============================================

driver = PySCFDriver(
    atom="H 0 0 0; H 0 0 0.735",
    basis="sto3g",
    charge=0,
    spin=0,
    unit=DistanceUnit.ANGSTROM,
)

# Build molecular problem
problem = driver.run()

# Fermionic Hamiltonian
fermionic_hamiltonian = problem.hamiltonian.second_q_op()

# Jordan-Wigner mapping
mapper = JordanWignerMapper()

qubit_hamiltonian = mapper.map(fermionic_hamiltonian)


print("\n==============================")
print("     CUREGENIX QUANTUM")
print("==============================")
print("Molecule : H2")
print("Mapping  : Jordan-Wigner")
print()

print("FERMIONIC HAMILTONIAN")
print("------------------------------")
print(fermionic_hamiltonian)

print()
print("QUBIT HAMILTONIAN")
print("------------------------------")
print(qubit_hamiltonian)

print("==============================")