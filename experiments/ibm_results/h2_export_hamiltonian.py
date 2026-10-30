import json
from pathlib import Path
from qiskit_nature.units import DistanceUnit
from qiskit_nature.second_q.drivers import PySCFDriver
from qiskit_nature.second_q.mappers import JordanWignerMapper

driver = PySCFDriver(
    atom="H 0 0 0; H 0 0 0.735",
    basis="sto3g",
    charge=0,
    spin=0,
    unit=DistanceUnit.ANGSTROM,
)
problem = driver.run()
hamiltonian = JordanWignerMapper().map(problem.hamiltonian.second_q_op())

terms = []
for label, coefficient in hamiltonian.to_list():
    terms.append({
        "pauli": label,
        "real": float(complex(coefficient).real),
        "imag": float(complex(coefficient).imag),
    })

report = {
    "molecule": "H2",
    "bond_distance_angstrom": 0.735,
    "basis": "STO-3G",
    "mapping": "Jordan-Wigner",
    "num_qubits": hamiltonian.num_qubits,
    "num_pauli_terms": len(terms),
    "nuclear_repulsion_energy_hartree": float(problem.nuclear_repulsion_energy),
    "terms": terms,
    "note": "Hamiltonian generated locally with PySCF and Qiskit Nature."
}

out = Path("/mnt/d/Projects/quantum/CureGenix/experiments/ibm_results")
path = out / "h2_hamiltonian_export.json"
path.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("Qubits:", report["num_qubits"])
print("Pauli terms:", report["num_pauli_terms"])
print("Saved:", path)
