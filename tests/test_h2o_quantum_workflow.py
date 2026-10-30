"""Focused, network-free tests for the H2O workflow and opt-in hardware guard."""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from backend.main import app
from backend.services import h2o_quantum_api as api
from backend.services.h2o_quantum_api import (
    ClassicalRequest,
    HardwareRequest,
    SimulatorRequest,
    evaluate_hardware,
    h2o_preflight,
    h2o_environment_status,
    get_h2o_statevector,
    run_classical_reference,
    run_simulator,
)
from fastapi import HTTPException
from backend.services.h2o_quantum_api import _run_or_http_error, _save_record, DEFAULT_H2O_SIMULATOR_TIMEOUT_SECONDS
from quantum.chemistry.h2o_experiment import (
    _optimizer_outcome,
    _resource_estimates,
    _status_reporting_slsqp,
    _qiskit_basis_state_label,
    reconstruct_h2o_statevector,
    validate_h2o_statevector_record,
    run_h2o_hardware_evaluation,
    water_configuration,
)
from backend.services.wsl_quantum_adapter import WSLQuantumAdapter, WSLTimeoutError
from backend.services.wsl_quantum_adapter import WSLCalculationError
from backend.services.quantum_resource_policy import DEFAULT_LIMITS


class H2OWorkflowTests(unittest.TestCase):
    def test_configuration_and_resource_counts(self):
        config = water_configuration()
        self.assertEqual(config["formula"], "H2O")
        self.assertEqual((config["charge"], config["spin"], config["spin_multiplicity"]), (0, 0, 1))
        self.assertEqual(config["basis"], "sto-3g")
        self.assertEqual(config["coordinate_units"], "Angstrom")
        self.assertEqual([atom["element"] for atom in config["atoms"]], ["O", "H", "H"])
        self.assertAlmostEqual(config["oh_bond_length_angstrom"], 0.9572)
        with self.assertRaises(ValueError):
            water_configuration(float("nan"), 104.5)

        sizes = _resource_estimates(7, 4)
        self.assertEqual(sizes["full_system"]["qubits"], 14)
        self.assertEqual(sizes["active_space"]["qubits"], 8)
        self.assertEqual(sizes["active_space"]["fixed_particle_sector_dimension"], 36)
        self.assertEqual(sizes["full_system"]["closed_shell_sector_dimension"], 441)
        self.assertEqual(h2o_preflight()["resource_estimates"]["full_system"]["qubits"], 14)

    @staticmethod
    def _saved_statevector_record():
        path = Path(__file__).resolve().parents[1] / "experiments" / "h2o_results" / "simulator-d33cf70ce6ac47b0809ebd853ca7203a.json"
        return path, json.loads(path.read_text(encoding="utf-8"))

    def test_final_statevector_reconstructs_saved_parameters_without_vqe(self):
        path, record = self._saved_statevector_record()
        original_bytes = path.read_bytes()
        with patch("qiskit_algorithms.VQE", side_effect=AssertionError("VQE must not be called")) as vqe_call:
            result = reconstruct_h2o_statevector(record)
        vqe_call.assert_not_called()
        self.assertEqual(result["experiment_record_id"], record["experiment_record_id"])
        self.assertEqual(result["execution_type"], "ideal_statevector_simulation")
        self.assertFalse(result["hardware_execution"])
        self.assertEqual((result["qubit_count"], result["statevector_dimension"]), (8, 256))
        self.assertEqual(result["hamiltonian"], {"mapping": "Jordan-Wigner", "qubit_count": 8, "pauli_term_count": 105})
        self.assertEqual(len(result["states"]), 256)
        self.assertTrue(result["normalization_check"]["normalized"])
        self.assertAlmostEqual(sum(state["probability"] for state in result["states"]), 1.0, places=10)
        for state in result["states"]:
            self.assertIsInstance(state["amplitude_real"], float)
            self.assertIsInstance(state["amplitude_imag"], float)
            self.assertIsInstance(state["probability"], float)
        encoded = json.dumps(result, allow_nan=False)
        self.assertEqual(len(json.loads(encoded)["states"]), 256)
        self.assertEqual(path.read_bytes(), original_bytes)

    def test_statevector_basis_ordering_is_explicit_and_qiskit_compatible(self):
        self.assertEqual(_qiskit_basis_state_label(0, 8), "00000000")
        self.assertEqual(_qiskit_basis_state_label(1, 8), "00000001")
        self.assertEqual(_qiskit_basis_state_label(128, 8), "10000000")

    def test_statevector_rejects_incomplete_malformed_and_unsupported_records(self):
        import copy
        _path, original = self._saved_statevector_record()

        missing_parameters = copy.deepcopy(original)
        missing_parameters["simulator"]["optimized_parameters"] = []
        with self.assertRaisesRegex(ValueError, "optimized parameters"):
            validate_h2o_statevector_record(missing_parameters)

        nonfinite_parameter = copy.deepcopy(original)
        nonfinite_parameter["simulator"]["optimized_parameters"][0] = float("nan")
        with self.assertRaisesRegex(ValueError, "finite numeric"):
            validate_h2o_statevector_record(nonfinite_parameter)

        hardware_record = copy.deepcopy(original)
        hardware_record["execution"]["hardware_execution"] = True
        with self.assertRaisesRegex(ValueError, "simulator records only"):
            validate_h2o_statevector_record(hardware_record)

        unsupported_size = copy.deepcopy(original)
        unsupported_size["active_space"]["mapped_qubits"] = 12
        with self.assertRaisesRegex(ValueError, "4e/4o"):
            validate_h2o_statevector_record(unsupported_size)

        incomplete = copy.deepcopy(original)
        incomplete["execution"]["status"] = "failed"
        with self.assertRaisesRegex(ValueError, "completed"):
            validate_h2o_statevector_record(incomplete)

    def test_hardware_requires_explicit_confirmation_and_missing_credentials(self):
        with patch.dict(os.environ, {"QISKIT_IBM_TOKEN": "", "QISKIT_IBM_INSTANCE": ""}):
            not_submitted = run_h2o_hardware_evaluation({}, "ibm_example", 0.05, False)
            self.assertEqual(not_submitted["status"], "not_submitted")
            record = {
                "execution": {"mode": "simulator", "status": "completed"},
                "active_space": {}, "simulator": {},
            }
            missing = run_h2o_hardware_evaluation(record, "ibm_example", 0.05, True)
            self.assertEqual(missing["status"], "not_configured")

    def test_worker_and_adapter_forward_explicit_mitigation_config_without_wsl(self):
        from quantum.wsl_worker import _run_h2o_hardware

        config = {"profile": "readout_mitigated", "gate_twirling": True}
        simulator = {"execution": {"mode": "simulator", "status": "completed"}}
        worker_result = {"status": "completed"}
        with patch(
            "quantum.chemistry.h2o_experiment.run_h2o_hardware_evaluation",
            return_value=worker_result,
        ) as run_hardware:
            _run_h2o_hardware({
                "simulator_record": simulator,
                "backend_name": "mock-backend",
                "precision": 0.05,
                "confirm_submission": True,
                "mitigation_config": config,
            })
        run_hardware.assert_called_once_with(simulator, "mock-backend", 0.05, True, config)

        adapter = WSLQuantumAdapter()
        with patch.object(adapter, "_execute_worker", return_value={"result": worker_result}) as execute:
            adapter.run_h2o_hardware_evaluation(
                simulator, "mock-backend", 0.05, confirm_submission=True,
                mitigation_config=config,
            )
        self.assertEqual(execute.call_args.args[0]["mitigation_config"], config)

    def test_hardware_fixed_parameter_path_uses_mock_runtime_only(self):
        import numpy as np
        from qiskit_nature.second_q.circuit.library import HartreeFock, UCCSD
        from qiskit_nature.second_q.mappers import JordanWignerMapper

        mapper = JordanWignerMapper()
        ansatz = UCCSD(4, (2, 2), qubit_mapper=mapper, initial_state=HartreeFock(4, (2, 2), mapper), reps=1)
        fake_backend = SimpleNamespace(name="mock_backend", status=lambda: SimpleNamespace(operational=True))

        class FakeJob:
            def job_id(self):
                return "mock-job-id"

            def result(self):
                class FakePrimitiveResult(list):
                    metadata = {
                        "resilience": {"measure_mitigation": True, "zne_mitigation": False, "pec_mitigation": False},
                        "twirling": {"enable_gates": True, "enable_measure": True, "num_randomizations": 8},
                        "dynamical_decoupling": {"enable": False},
                    }

                return FakePrimitiveResult([SimpleNamespace(
                    data=SimpleNamespace(evs=-0.75, stds=0.01),
                    metadata={"shots": 2048, "target_precision": 0.05, "num_randomizations": 8},
                )])

            def status(self):
                return "DONE"

        class FakeEstimator:
            def __init__(self, mode, **kwargs):
                self.mode = mode
                self.options = kwargs.get("options")
                self.kwargs = kwargs

            def run(self, _pubs, precision):
                self.precision = precision
                return FakeJob()

        fake_runtime = SimpleNamespace(
            EstimatorV2=FakeEstimator,
            QiskitRuntimeService=lambda **_kwargs: SimpleNamespace(backend=lambda _name: fake_backend),
        )
        class FakePassManager:
            def run(self, circuit):
                return circuit

        record = {
            "execution": {"mode": "simulator", "status": "completed"},
            "active_space": {
                "active_particles_alpha_beta": [2, 2], "active_spatial_orbitals": 4,
                "hamiltonian_terms": [{"pauli": "IIIIIIII", "real": -0.5, "imag": 0.0}],
                "exact_reference": {"active_space_constant_hartree": -1.0, "nuclear_repulsion_energy_hartree": 0.7},
            },
            "simulator": {"optimized_parameters": np.zeros(ansatz.num_parameters).tolist(), "energy_hartree": -0.8},
        }
        with patch.dict(os.environ, {"QISKIT_IBM_TOKEN": "mock-token", "QISKIT_IBM_INSTANCE": "mock-instance"}), \
             patch.dict(sys.modules, {"qiskit_ibm_runtime": fake_runtime}), \
             patch("quantum.chemistry.runtime_mitigation.importlib.metadata.version", return_value="0.51.0"), \
             patch("qiskit.transpiler.preset_passmanagers.generate_preset_pass_manager", return_value=FakePassManager()), \
             patch("qiskit.quantum_info.SparsePauliOp.apply_layout", autospec=True, side_effect=lambda self, _layout: self):
            result = run_h2o_hardware_evaluation(
                record, "mock_backend", 0.05, True,
                {"profile": "readout_mitigated", "gate_twirling": True, "num_randomizations": 8},
            )

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["job_id"], "mock-job-id")
        self.assertEqual(result["execution_type"], "hardware_evaluation_of_fixed_simulator_optimized_parameters")
        self.assertAlmostEqual(result["total_molecular_energy_hartree"], -1.05)
        self.assertEqual(result["runtime_provenance"]["configuration_provenance"], "explicitly_configured")
        self.assertEqual(result["runtime_provenance"]["runtime_package_version"], "0.51.0")
        self.assertEqual(result["runtime_provenance"]["backend"], "mock_backend")
        self.assertEqual(result["runtime_provenance"]["actual_shots"], 2048)
        self.assertEqual(result["runtime_provenance"]["twirling_randomizations"], 8)
        self.assertTrue(result["runtime_provenance"]["options_requested"]["resilience"]["measure_mitigation"])
        self.assertNotIn("mock-token", json.dumps(result))

    def test_simulator_record_schema_and_same_active_space_comparison(self):
        import numpy as np
        class FakeVQE:
            def __init__(self, **kwargs):
                self.ansatz = kwargs["ansatz"]

            def compute_minimum_eigenvalue(self, _operator):
                return SimpleNamespace(
                    eigenvalue=-0.5,
                    optimal_point=np.zeros(self.ansatz.num_parameters),
                    optimizer_result=SimpleNamespace(success=True, message="ok", nit=2, nfev=3),
                )

        record = {
            "execution": {"mode": "classical_reference", "status": "completed"},
            "molecule": water_configuration(),
            "active_space": {
                "hamiltonian_terms": [{"pauli": "IIIIIIII", "real": -0.5, "imag": 0.0}],
                "active_particles_alpha_beta": [2, 2], "active_spatial_orbitals": 4,
                "exact_reference": {
                    "active_space_constant_hartree": -1.0,
                    "nuclear_repulsion_energy_hartree": 0.7,
                    "total_energy_hartree": -0.9,
                    "electronic_energy_hartree": -1.6,
                },
            },
        }
        # Patch the optimizer; build the genuine Qiskit Nature ansatz and operator.
        with patch("qiskit_algorithms.VQE", FakeVQE):
            from quantum.chemistry.h2o_experiment import run_h2o_simulator
            result = run_h2o_simulator(record, maxiter=3)
        self.assertEqual(result["execution"]["mode"], "simulator")
        self.assertFalse(result["execution"]["hardware_execution"])
        self.assertEqual(result["simulator"]["mapper"], "Jordan-Wigner")
        self.assertIn("difference_from_same_active_space_exact_hartree", result["simulator"])
        self.assertEqual(result["simulator"]["optimizer_success"], True)
        self.assertEqual(result["simulator"]["optimizer_status"], "success")
        self.assertTrue(result["simulator"]["optimizer_status_available"])
        self.assertEqual(result["simulator"]["optimizer_message"], "ok")

    def test_optimizer_outcome_maps_success_failure_and_missing_status(self):
        success = _optimizer_outcome(SimpleNamespace(success=True, message="Optimization terminated successfully."))
        self.assertEqual(success, {
            "optimizer_status": "success",
            "optimizer_status_available": True,
            "optimizer_success": True,
            "optimizer_message": "Optimization terminated successfully.",
        })

        unsuccessful = _optimizer_outcome(SimpleNamespace(success=False, message="Iteration limit reached."))
        self.assertEqual(unsuccessful["optimizer_status"], "unsuccessful")
        self.assertTrue(unsuccessful["optimizer_status_available"])
        self.assertIs(unsuccessful["optimizer_success"], False)
        self.assertEqual(unsuccessful["optimizer_message"], "Iteration limit reached.")

        unavailable = _optimizer_outcome(SimpleNamespace(nit=6, nfev=164))
        self.assertEqual(unavailable, {
            "optimizer_status": "unavailable",
            "optimizer_status_available": False,
            "optimizer_success": None,
            "optimizer_message": None,
        })

    def test_status_reporting_slsqp_preserves_scipy_success_and_message(self):
        optimizer = _status_reporting_slsqp(maxiter=10)
        result = optimizer.minimize(lambda point: float((point[0] - 1.0) ** 2), [0.0])
        self.assertIs(result.success, True)
        self.assertIsInstance(result.message, str)
        self.assertGreaterEqual(result.nfev, 1)

    def test_api_saves_separate_records_and_hardware_needs_explicit_request(self):
        reference = {
            "execution": {"mode": "classical_reference", "status": "completed"},
            "references": {}, "active_space": {},
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(api, "RESULTS_DIR", Path(temp_dir)), patch.object(
                api.wsl_quantum_adapter, "run_h2o_classical_reference", return_value=reference
            ) as classical_call:
                saved = run_classical_reference(ClassicalRequest())
                self.assertTrue((Path(temp_dir) / f"{saved['experiment_record_id']}.json").is_file())
                self.assertEqual(json.loads((Path(temp_dir) / f"{saved['experiment_record_id']}.json").read_text())["execution"]["mode"], "classical_reference")
                classical_call.assert_called_once()

                simulator = {
                    "execution": {"mode": "simulator", "status": "completed"},
                    "simulator": {"optimized_parameters": [0.0]},
                }
                simulator_id = f"classical-{saved['experiment_record_id'].split('-', 1)[1]}"
                with patch.object(api.wsl_quantum_adapter, "run_h2o_simulator", return_value=simulator) as simulator_call:
                    sim_saved = run_simulator(SimulatorRequest(classical_record_id=simulator_id, maxiter=2))
                self.assertNotEqual(saved["experiment_record_id"], sim_saved["experiment_record_id"])
                simulator_call.assert_called_once_with(
                    reference, 2, timeout=DEFAULT_H2O_SIMULATOR_TIMEOUT_SECONDS
                )

            with patch.object(api, "RESULTS_DIR", Path(temp_dir)), patch.object(
                api.wsl_quantum_adapter, "run_h2o_hardware_evaluation"
            ) as hardware_call:
                with self.assertRaises(Exception):
                    evaluate_hardware(HardwareRequest(simulator_record_id="simulator-" + "a" * 32, backend_name="fake"))
                hardware_call.assert_not_called()

        completed_simulator = {
            "experiment_record_id": "simulator-" + "a" * 32,
            "execution": {"mode": "simulator", "status": "completed"},
        }
        hardware_result = {"status": "completed", "job_id": "offline-mock"}
        mitigation = {"profile": "readout_mitigated", "gate_twirling": True}
        with tempfile.TemporaryDirectory() as temp_dir, \
             patch.object(api, "RESULTS_DIR", Path(temp_dir)), \
             patch.object(api, "_read_record", return_value=completed_simulator), \
             patch.object(api.wsl_quantum_adapter, "run_h2o_hardware_evaluation", return_value=hardware_result) as hardware_call:
            request = HardwareRequest(
                simulator_record_id=completed_simulator["experiment_record_id"],
                backend_name="fake",
                confirm_submission=True,
                mitigation_config=mitigation,
            )
            saved_hardware = evaluate_hardware(request)
            self.assertTrue((Path(temp_dir) / f"{saved_hardware['experiment_record_id']}.json").is_file())
            self.assertEqual(saved_hardware["execution"]["hardware_execution"], True)
            hardware_call.assert_called_once_with(
                completed_simulator,
                "fake",
                0.05,
                confirm_submission=True,
                mitigation_config=mitigation,
            )

        with patch.object(api, "_read_record") as read_record:
            invalid = HardwareRequest(
                simulator_record_id="simulator-" + "a" * 32,
                backend_name="fake",
                confirm_submission=True,
                mitigation_config={"profile": "readout_mitigated", "measurement_twirling": False},
            )
            with self.assertRaises(HTTPException) as raised:
                evaluate_hardware(invalid)
            self.assertEqual(raised.exception.status_code, 422)
            read_record.assert_not_called()

    def test_quantum_chemistry_api_is_registered(self):
        paths = set(app.openapi()["paths"])
        self.assertIn("/api/quantum-chemistry/h2o/classical", paths)
        self.assertIn("/api/quantum-chemistry/h2o/simulator", paths)
        self.assertIn("/api/quantum-chemistry/h2o/hardware", paths)
        self.assertIn("/api/quantum-chemistry/h2o/preflight", paths)
        self.assertIn("/api/quantum-chemistry/h2o/environment", paths)
        self.assertIn("/api/quantum-chemistry/h2o/statevector/{record_id}", paths)

    def test_statevector_api_validates_ids_and_returns_ephemeral_simulator_data(self):
        with tempfile.TemporaryDirectory() as temp_dir, patch.object(api, "RESULTS_DIR", Path(temp_dir)):
            with self.assertRaises(HTTPException) as invalid:
                get_h2o_statevector("../../secrets")
            self.assertEqual(invalid.exception.status_code, 422)
            with self.assertRaises(HTTPException) as missing:
                get_h2o_statevector("simulator-" + "a" * 32)
            self.assertEqual(missing.exception.status_code, 404)

        _path, record = self._saved_statevector_record()
        statevector_response = {
            "experiment_record_id": record["experiment_record_id"],
            "execution_type": "ideal_statevector_simulation",
            "hardware_execution": False,
            "qubit_count": 8,
            "statevector_dimension": 256,
            "states": [],
            "normalization_check": {"normalized": True, "probability_sum": 1.0},
        }
        with patch.object(api, "_read_record", return_value=record), patch.object(
            api.wsl_quantum_adapter,
            "reconstruct_h2o_statevector",
            return_value=statevector_response,
        ) as reconstruct:
            response = get_h2o_statevector(record["experiment_record_id"])
        self.assertIs(response, statevector_response)
        reconstruct.assert_called_once_with(record)

    def test_statevector_api_rejects_bad_records_and_handles_worker_errors(self):
        import copy
        _path, record = self._saved_statevector_record()
        malformed = copy.deepcopy(record)
        malformed["simulator"]["optimized_parameters"] = []
        with patch.object(api, "_read_record", return_value=malformed), patch.object(
            api.wsl_quantum_adapter, "reconstruct_h2o_statevector"
        ) as reconstruct:
            with self.assertRaises(HTTPException) as invalid:
                get_h2o_statevector(record["experiment_record_id"])
        self.assertEqual(invalid.exception.status_code, 422)
        reconstruct.assert_not_called()

        with patch.object(api, "_read_record", return_value=record), patch.object(
            api.wsl_quantum_adapter,
            "reconstruct_h2o_statevector",
            side_effect=WSLCalculationError("private worker diagnostic"),
        ):
            with self.assertRaises(HTTPException) as failed:
                get_h2o_statevector(record["experiment_record_id"])
        self.assertEqual(failed.exception.status_code, 503)
        self.assertNotIn("private worker diagnostic", json.dumps(failed.exception.detail))

    def test_statevector_adapter_and_worker_dispatch_without_vqe(self):
        _path, record = self._saved_statevector_record()
        expected = {
            "experiment_record_id": record["experiment_record_id"],
            "execution_type": "ideal_statevector_simulation",
            "hardware_execution": False,
        }
        adapter = WSLQuantumAdapter(distro="Ubuntu")
        with patch.object(adapter, "_execute_worker", return_value={"result": expected}) as execute:
            self.assertEqual(adapter.reconstruct_h2o_statevector(record), expected)
        execute.assert_called_once_with({"action": "h2o_statevector", "simulator_record": record}, timeout=120)

        from quantum.wsl_worker import _run_h2o_statevector
        with patch("quantum.chemistry.h2o_experiment.reconstruct_h2o_statevector", return_value=expected) as reconstruct:
            worker_response = _run_h2o_statevector({"simulator_record": record})
        reconstruct.assert_called_once_with(record)
        self.assertEqual(worker_response, {"status": "success", "action": "h2o_statevector", "result": expected})

    def test_environment_status_is_sanitized(self):
        with patch.object(api.wsl_quantum_adapter, "is_available", return_value=(True, "private path and stderr")):
            ready = h2o_environment_status()
        self.assertTrue(ready["ready"])
        self.assertEqual(ready["status"], "ready")
        self.assertNotIn("private", json.dumps(ready))

        with patch.object(api.wsl_quantum_adapter, "is_available", return_value=(False, "secret path and token")):
            unavailable = h2o_environment_status()
        self.assertFalse(unavailable["ready"])
        self.assertEqual(unavailable["status"], "unavailable")
        self.assertNotIn("secret", json.dumps(unavailable))

        with patch.object(api.wsl_quantum_adapter, "is_available", side_effect=RuntimeError("private diagnostic")):
            failed_check = h2o_environment_status()
        self.assertFalse(failed_check["ready"])
        self.assertNotIn("private diagnostic", json.dumps(failed_check))

    def test_frontend_resource_defaults_match_backend_configuration(self):
        import re
        helper = Path(__file__).resolve().parents[1] / "frontend-next" / "lib" / "quantumLabTransparency.mjs"
        source = helper.read_text(encoding="utf-8")
        frontend_values = {
            key: int(re.search(rf"{name}: (\d+)", source).group(1))
            for key, name in {
                "max_heavy_atoms": "maxHeavyAtoms",
                "max_total_atoms": "maxTotalAtoms",
                "max_estimated_basis_functions": "maxEstimatedBasisFunctions",
                "max_vqe_iterations": "maxVqeIterations",
            }.items()
        }
        self.assertEqual(frontend_values, DEFAULT_LIMITS)
        adapter_source = (Path(__file__).resolve().parents[1] / "backend" / "services" / "wsl_quantum_adapter.py").read_text(encoding="utf-8")
        timeout = int(re.search(r"DEFAULT_TIMEOUT_SECONDS = (\d+)", adapter_source).group(1))
        self.assertEqual(int(re.search(r"wslTimeoutSeconds: (\d+)", source).group(1)), timeout)
        api_source = (Path(__file__).resolve().parents[1] / "backend" / "services" / "h2o_quantum_api.py").read_text(encoding="utf-8")
        h2o_timeout = int(re.search(r"DEFAULT_H2O_SIMULATOR_TIMEOUT_SECONDS = (\d+)", api_source).group(1))
        self.assertEqual(int(re.search(r"h2oSimulatorTimeoutSeconds: (\d+)", source).group(1)), h2o_timeout)

    def test_simulator_timeout_is_configurable_and_timeout_response_is_safe(self):
        self.assertEqual(SimulatorRequest(classical_record_id="classical-" + "a" * 32).timeout_seconds, 3600)
        self.assertEqual(SimulatorRequest(
            classical_record_id="classical-" + "a" * 32, timeout_seconds=7200
        ).timeout_seconds, 7200)
        with self.assertRaises(Exception):
            SimulatorRequest(classical_record_id="classical-" + "a" * 32, timeout_seconds=14401)

        timeout_error = WSLTimeoutError("timed out; private worker stderr and path must not leak")
        timeout_error.timeout_seconds = 7200
        timeout_error.elapsed_seconds = 7200.25
        with self.assertRaises(HTTPException) as raised:
            _run_or_http_error(lambda: (_ for _ in ()).throw(timeout_error))
        self.assertEqual(raised.exception.status_code, 504)
        detail = raised.exception.detail
        self.assertEqual(detail["status"], "timed_out")
        self.assertEqual(detail["timeout_seconds"], 7200)
        self.assertEqual(detail["elapsed_seconds"], 7200.25)
        self.assertNotIn("private", json.dumps(detail))

    def test_experiment_retries_create_unique_records_without_overwriting(self):
        with tempfile.TemporaryDirectory() as temp_dir, patch.object(api, "RESULTS_DIR", Path(temp_dir)):
            first = _save_record({"marker": "first"}, "simulator")
            second = _save_record({"marker": "second"}, "simulator")
            self.assertNotEqual(first["experiment_record_id"], second["experiment_record_id"])
            first_path = Path(temp_dir) / f"{first['experiment_record_id']}.json"
            second_path = Path(temp_dir) / f"{second['experiment_record_id']}.json"
            self.assertEqual(json.loads(first_path.read_text(encoding="utf-8"))["marker"], "first")
            self.assertEqual(json.loads(second_path.read_text(encoding="utf-8"))["marker"], "second")

    def test_adapter_defaults_to_project_chemistry_venv(self):
        adapter = WSLQuantumAdapter(distro="Ubuntu")
        with patch("backend.services.wsl_quantum_adapter.subprocess.run", return_value=SimpleNamespace(
            returncode=0, stdout="cureuser\x00\n"
        )):
            self.assertEqual(
                adapter.resolve_wsl_python(),
                "/home/cureuser/curegenix-chem-venv/bin/python",
            )


if __name__ == "__main__":
    unittest.main()
