import json
from pathlib import Path
from qiskit.circuit.library import TwoLocal
from qiskit.primitives import StatevectorEstimator
from qiskit_algorithms import VQE
from qiskit_algorithms.optimizers import SLSQP
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

ansatz = TwoLocal(
    hamiltonian.num_qubits,
    rotation_blocks="ry",
    entanglement_blocks="cz",
    entanglement="full",
    reps=2,
)

vqe = VQE(
    estimator=StatevectorEstimator(),
    ansatz=ansatz,
    optimizer=SLSQP(maxiter=100),
)
result = vqe.compute_minimum_eigenvalue(hamiltonian)

report = {
    "molecule": "H2",
    "bond_distance_angstrom": 0.735,
    "basis": "STO-3G",
    "mapping": "Jordan-Wigner",
    "method": "VQE",
    "simulator": "StatevectorEstimator",
    "optimizer": "SLSQP",
    "maxiter": 100,
    "num_qubits": hamiltonian.num_qubits,
    "vqe_eigenvalue_hartree": float(result.eigenvalue.real),
    "exact_reference_eigenvalue_hartree": -1.8572750302023775,
    "absolute_energy_error_hartree": abs(
        float(result.eigenvalue.real) - (-1.8572750302023775)
    ),
    "optimal_parameters": {
        str(parameter): float(value)
        for parameter, value in zip(
            ansatz.parameters, result.optimal_point
        )
    },
    "note": "Local simulation only; not a hardware result."
}

out = Path("/mnt/d/Projects/quantum/CureGenix/experiments/ibm_results")
path = out / "h2_local_vqe.json"
path.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
print("Saved:", path)
