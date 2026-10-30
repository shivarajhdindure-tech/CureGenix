"""Offline tests for explicit quantum job dispatch and lifecycle persistence."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import BackgroundTasks, HTTPException

from backend.services import quantum_calculation_api as api
from backend.services.quantum_calculation_api import QuantumCalculationRequest


class QuantumCalculationApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)
        self.jobs = api._jobs
        self.fingerprints = api._active_fingerprints
        self.jobs.clear()
        self.fingerprints.clear()
        self.results_dir_patch = patch.object(api, "RESULTS_DIR", self.directory)
        self.results_dir_patch.start()

    def tearDown(self):
        self.jobs.clear()
        self.fingerprints.clear()
        self.results_dir_patch.stop()
        self.temp.cleanup()

    @staticmethod
    def request():
        return QuantumCalculationRequest(candidate_id="GEN-TEST", smiles="CCO")

    def test_explicit_submission_queues_backend_calculation_and_persists_completed_result(self):
        background = BackgroundTasks()
        accepted = api.submit_quantum_calculation(self.request(), background)
        self.assertEqual(accepted["status"], "queued")
        self.assertEqual(len(background.tasks), 1)
        self.assertEqual(background.tasks[0].func, api._execute_job)
        with patch("quantum.chemistry.quantum_analysis.analyze_smiles", return_value={
            "status": "success", "homo_lumo_gap_hartree": 0.2,
            "vqe": {"electronic_energy_hartree": -1.1, "total_molecular_energy_hartree": -1.0,
                    "optimizer_success": True, "optimizer_message": "Optimization terminated successfully."},
        }) as analyze:
            api._execute_job(accepted["job_id"])
        analyze.assert_called_once()
        saved = api.get_quantum_calculation(accepted["job_id"])
        self.assertEqual(saved["status"], "completed")
        self.assertEqual(saved["experiment_record_id"], accepted["job_id"])
        self.assertEqual(saved["result"]["vqe"]["optimizer_success"], True)
        self.assertTrue((self.directory / f"{accepted['job_id']}.json").is_file())

    def test_duplicate_active_submission_returns_same_job_without_queuing_twice(self):
        first_background = BackgroundTasks()
        first = api.submit_quantum_calculation(self.request(), first_background)
        second_background = BackgroundTasks()
        second = api.submit_quantum_calculation(self.request(), second_background)
        self.assertEqual(second["job_id"], first["job_id"])
        self.assertTrue(second["duplicate"])
        self.assertEqual(len(second_background.tasks), 0)

        changed_options = QuantumCalculationRequest(candidate_id="GEN-TEST", smiles="CCO", maxiter=75)
        third = api.submit_quantum_calculation(changed_options, BackgroundTasks())
        self.assertEqual(third["job_id"], first["job_id"])
        self.assertTrue(third["duplicate"])

    def test_policy_skip_is_persisted_as_skipped_with_explicit_reasons(self):
        background = BackgroundTasks()
        accepted = api.submit_quantum_calculation(self.request(), background)
        skipped = {
            "status": "skipped_resource_limit",
            "message": "Skipped before geometry and PySCF setup: heavy-atom count exceeds policy.",
            "resource_eligibility": {"reasons": ["Heavy-atom count 30 exceeds configured limit 20."]},
        }
        with patch("quantum.chemistry.quantum_analysis.analyze_smiles", return_value=skipped):
            api._execute_job(accepted["job_id"])
        result = api.get_quantum_calculation(accepted["job_id"])
        self.assertEqual(result["status"], "skipped")
        self.assertEqual(result["result"]["resource_eligibility"]["reasons"][0], "Heavy-atom count 30 exceeds configured limit 20.")
        self.assertNotIn("vqe", result["result"])

    def test_worker_failure_is_failed_and_diagnostic_error_is_not_exposed(self):
        background = BackgroundTasks()
        accepted = api.submit_quantum_calculation(self.request(), background)
        with patch("quantum.chemistry.quantum_analysis.analyze_smiles", side_effect=RuntimeError("private worker traceback detail")):
            api._execute_job(accepted["job_id"])
        result = api.get_quantum_calculation(accepted["job_id"])
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["result"]["message"], "The chemistry calculation failed. Review the backend log entry for its diagnostic details.")
        self.assertNotIn("private worker traceback detail", json.dumps(result))

    def test_unknown_job_is_404_and_invalid_job_id_is_rejected(self):
        with self.assertRaises(HTTPException) as missing:
            api.get_quantum_calculation("molecular-" + "0" * 32)
        self.assertEqual(missing.exception.status_code, 404)
        with self.assertRaises(HTTPException) as invalid:
            api.get_quantum_calculation("..\\secret")
        self.assertEqual(invalid.exception.status_code, 422)


if __name__ == "__main__":
    unittest.main()
