import json
from pathlib import Path
from qiskit_nature.units import DistanceUnit
from qiskit_nature.second_q.drivers import PySCFDriver
from qiskit_nature.second_q.mappers import JordanWignerMapper
from qiskit_algorithms import NumPyMinimumEigensolver

driver = PySCFDriver(
    atom="H 0 0 0; H 0 0 0.735",
    basis="sto3g",
    charge=0,
    spin=0,
    unit=DistanceUnit.ANGSTROM,
)
problem = driver.run()
hamiltonian = JordanWignerMapper().map(problem.hamiltonian.second_q_op())
exact = NumPyMinimumEigensolver().compute_minimum_eigenvalue(hamiltonian)

report = {
    "molecule": "H2",
    "bond_distance_angstrom": 0.735,
    "basis": "STO-3G",
    "mapping": "Jordan-Wigner",
    "num_qubits": hamiltonian.num_qubits,
    "num_particles": list(problem.num_particles),
    "num_spatial_orbitals": problem.num_spatial_orbitals,
    "num_pauli_terms": len(hamiltonian),
    "exact_qubit_hamiltonian_eigenvalue_hartree": float(exact.eigenvalue.real),
    "nuclear_repulsion_energy_hartree": float(problem.nuclear_repulsion_energy),
    "note": "Local exact reference; not a hardware result."
}

out = Path("/mnt/d/Projects/quantum/CureGenix/experiments/ibm_results")
out.mkdir(parents=True, exist_ok=True)
path = out / "h2_local_reference.json"
path.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
print("Saved:", path)
