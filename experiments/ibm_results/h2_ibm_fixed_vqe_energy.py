"""Opt-in H2 fixed-parameter IBM Runtime evaluation.

This script only evaluates saved local VQE parameters; it does not optimize on
hardware. Importing the module is safe and never contacts IBM Runtime.
"""

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "experiments" / "ibm_results"
# Keep legacy behavior unless the operator changes this explicit configuration.
RUNTIME_MITIGATION_CONFIG: dict[str, Any] = {"profile": "runtime_default"}


def run_h2_estimator(
    estimator_class: Any,
    backend: Any,
    circuit: Any,
    observable: Any,
    precision: float,
    mitigation_config: dict[str, Any] | None = None,
    on_submitted: Any = None,
) -> dict[str, Any]:
    """Shared, mockable H2 Estimator call used by the guarded script entry point."""
    from quantum.chemistry.runtime_mitigation import execute_estimator_with_provenance

    return execute_estimator_with_provenance(
        estimator_class,
        backend,
        [(circuit, observable)],
        precision,
        mitigation_config or RUNTIME_MITIGATION_CONFIG,
        circuit=circuit,
        observable=observable,
        on_submitted=on_submitted,
    )


def _write_new_record(path: Path, record: dict[str, Any], *, create: bool = False) -> None:
    serialized = json.dumps(record, indent=2, allow_nan=False)
    if create:
        with path.open("x", encoding="utf-8") as handle:
            handle.write(serialized)
    else:
        path.write_text(serialized, encoding="utf-8")


def main() -> None:
    from qiskit import QuantumCircuit  # noqa: F401 - explicit Qiskit environment check
    from qiskit.circuit.library import TwoLocal
    from qiskit.quantum_info import SparsePauliOp
    from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
    from qiskit_ibm_runtime import QiskitRuntimeService, EstimatorV2

    local_vqe = json.loads((RESULTS / "h2_local_vqe.json").read_text(encoding="utf-8"))
    ham_data = json.loads((RESULTS / "h2_hamiltonian_export.json").read_text(encoding="utf-8"))
    reference = json.loads((RESULTS / "h2_local_reference.json").read_text(encoding="utf-8"))
    if ham_data["num_qubits"] != 4 or ham_data["num_pauli_terms"] != 15:
        raise RuntimeError("Unexpected saved H2 Hamiltonian dimensions.")

    token = os.environ.get("QISKIT_IBM_TOKEN")
    instance = os.environ.get("QISKIT_IBM_INSTANCE")
    if not token or not instance:
        raise RuntimeError("IBM token or instance environment variable is missing.")

    service = QiskitRuntimeService(
        channel=os.environ.get("QISKIT_IBM_CHANNEL", "ibm_quantum_platform"),
        token=token,
        instance=instance,
    )
    backend = service.backend("ibm_fez")
    print("Backend:", backend.name)
    print("Status:", backend.status().status_msg)
    print("Operational:", backend.status().operational)
    if not backend.status().operational:
        raise RuntimeError("ibm_fez is not operational; no job submitted.")

    ansatz = TwoLocal(
        4,
        rotation_blocks="ry",
        entanglement_blocks="cz",
        entanglement="full",
        reps=2,
    )
    saved_parameters = local_vqe["optimal_parameters"]
    parameter_values = []
    for parameter in ansatz.parameters:
        key = str(parameter)
        if key not in saved_parameters:
            raise ValueError(f"Missing saved VQE parameter: {key}")
        parameter_values.append(float(saved_parameters[key]))
    bound_circuit = ansatz.assign_parameters(dict(zip(ansatz.parameters, parameter_values)))
    if bound_circuit.num_parameters != 0:
        raise RuntimeError("Circuit still has unbound parameters.")

    observable = SparsePauliOp.from_list([
        (item["pauli"], complex(item["real"], item["imag"]))
        for item in ham_data["terms"]
    ])
    pass_manager = generate_preset_pass_manager(backend=backend, optimization_level=1)
    isa_circuit = pass_manager.run(bound_circuit)
    isa_observable = observable.apply_layout(isa_circuit.layout)

    created = datetime.now(timezone.utc)
    stamp = created.strftime("%Y%m%dT%H%M%S%fZ")
    profile = RUNTIME_MITIGATION_CONFIG.get("profile", "runtime_default")
    out_path = RESULTS / f"h2_ibm_fixed_vqe_energy_{stamp}_{uuid.uuid4().hex[:8]}.json"
    record = {
        "experiment": "H2 fixed-parameter energy estimation",
        "created_utc": created.isoformat(),
        "molecule": "H2",
        "bond_distance_angstrom": 0.735,
        "basis": "STO-3G",
        "mapping": "Jordan-Wigner",
        "backend": str(backend.name),
        "num_qubits": int(isa_circuit.num_qubits),
        "num_pauli_terms": len(ham_data["terms"]),
        "local_vqe_electronic_energy_hartree": local_vqe["vqe_eigenvalue_hartree"],
        "exact_electronic_reference_hartree": reference["exact_qubit_hamiltonian_eigenvalue_hartree"],
        "nuclear_repulsion_energy_hartree": ham_data["nuclear_repulsion_energy_hartree"],
        "mitigation_profile": profile,
        "status": "prepared",
        "note": "Fixed local VQE parameters evaluated on hardware; not hardware-optimized VQE.",
    }
    _write_new_record(out_path, record, create=True)

    try:
        def record_submission(job_id: str, provenance: dict[str, Any]) -> None:
            record.update({"job_id": job_id, "status": "submitted", "runtime_provenance": provenance})
            _write_new_record(out_path, record)

        run = run_h2_estimator(
            EstimatorV2, backend, isa_circuit, isa_observable, 0.03,
            RUNTIME_MITIGATION_CONFIG, on_submitted=record_submission,
        )
    except Exception as exc:
        provenance = getattr(exc, "provenance", None)
        record.update({
            "status": "failed",
            "error_type": getattr(exc, "error_type", type(exc).__name__),
            "runtime_provenance": provenance,
        })
        _write_new_record(out_path, record)
        print(json.dumps(record, indent=2))
        return
    job = run["job"]
    record.update({"job_id": run["job_id"], "status": "submitted"})
    _write_new_record(out_path, record)
    print("Submitted job:", record["job_id"])
    print("Saved:", out_path)

    pub_result = run["pub_result"]
    energy = float(pub_result.data.evs)
    std_error = float(pub_result.data.stds)
    nuclear = float(ham_data["nuclear_repulsion_energy_hartree"])
    record.update({
        "status": "completed",
        "electronic_energy_hartree": energy,
        "electronic_energy_standard_error_hartree": std_error,
        "total_energy_hartree": energy + nuclear,
        "total_energy_standard_error_hartree": std_error,
        "difference_from_local_vqe_hartree": energy - float(local_vqe["vqe_eigenvalue_hartree"]),
        "absolute_difference_from_exact_electronic_reference_hartree": abs(
            energy - float(reference["exact_qubit_hamiltonian_eigenvalue_hartree"])
        ),
        "runtime_provenance": run["provenance"],
        "result_metadata": run["provenance"]["pub_metadata"],
        "queue_or_execution_status": str(job.status()),
    })
    _write_new_record(out_path, record)
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
