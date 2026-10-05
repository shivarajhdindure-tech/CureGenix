from qiskit_nature.units import DistanceUnit
from qiskit_nature.second_q.drivers import PySCFDriver


# H2 molecule
driver = PySCFDriver(
    atom="H 0 0 0; H 0 0 0.735",
    basis="sto3g",
    charge=0,
    spin=0,
    unit=DistanceUnit.ANGSTROM,
)

# Run the electronic structure calculation
problem = driver.run()

# Get the electronic Hamiltonian
hamiltonian = problem.hamiltonian.second_q_op()

print("\n==============================")
print("     CUREGENIX QUANTUM")
print("==============================")
print("Molecule : H2")
print("Basis    : STO-3G")
print()
print("FERMIONIC HAMILTONIAN")
print("------------------------------")
print(hamiltonian)
print("==============================")