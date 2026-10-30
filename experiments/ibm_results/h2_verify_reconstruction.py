import json
from pathlib import Path
from qiskit.circuit.library import TwoLocal
from qiskit.quantum_info import Statevector, SparsePauliOp

root = Path("/mnt/d/Projects/quantum/CureGenix/experiments/ibm_results")
vqe = json.loads((root / "h2_local_vqe.json").read_text(encoding="utf-8"))
ham = json.loads((root / "h2_hamiltonian_export.json").read_text(encoding="utf-8"))
qpu = json.loads((root / "h2_ibm_fixed_vqe_energy.json").read_text(encoding="utf-8"))

ansatz = TwoLocal(
    4,
    rotation_blocks="ry",
    entanglement_blocks="cz",
    entanglement="full",
    reps=2,
)

saved = vqe["optimal_parameters"]
ordered_values = [float(saved[str(p)]) for p in ansatz.parameters]
bound = ansatz.assign_parameters(dict(zip(ansatz.parameters, ordered_values)))

observable = SparsePauliOp.from_list([
    (t["pauli"], complex(t["real"], t["imag"]))
    for t in ham["terms"]
])
state = Statevector.from_instruction(bound)
reconstructed_energy = float(state.expectation_value(observable).real)

print("Saved local VQE energy:", vqe["vqe_eigenvalue_hartree"])
print("Reconstructed exact statevector energy:", reconstructed_energy)
print("IBM hardware energy:", qpu["electronic_energy_hartree"])
print("Reconstruction minus saved VQE:",
      reconstructed_energy - vqe["vqe_eigenvalue_hartree"])
print("Hardware minus reconstructed local:",
      qpu["electronic_energy_hartree"] - reconstructed_energy)
