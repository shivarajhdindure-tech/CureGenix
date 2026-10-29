"""Fast regression tests for WSL launch failures and partial candidate results."""

import json
import subprocess
import unittest
from unittest.mock import patch

from backend.agents.quantum_analysis_agent import QuantumAnalysisAgent
from backend.mcp.memory_mcp import MemoryMCPServer
from backend.services.wsl_quantum_adapter import (
    WSLQuantumAdapter,
    WSLResourceError,
    WSLServiceError,
    WSLTimeoutError,
)
from quantum.wsl_worker import _run_molecular_analysis


class AdapterFailureClassificationTests(unittest.TestCase):
    def setUp(self):
        self.adapter = WSLQuantumAdapter(timeout_seconds=12)
        self.adapter._cached_wsl_exe = "wsl.exe"
        self.adapter._resolved_python_path = "/home/test/.venv/bin/python"

    def run_worker_with(self, side_effect):
        with patch.object(self.adapter, "get_worker_wsl_path", return_value="/mnt/d/project/quantum/wsl_worker.py"), \
             patch("backend.services.wsl_quantum_adapter.subprocess.run", side_effect=side_effect) as run:
            result = self.adapter._execute_worker({"action": "smoke_test"}, timeout=12)
        return result, run

    @staticmethod
    def completed(returncode, stdout="", stderr=""):
        return subprocess.CompletedProcess(args=["wsl"], returncode=returncode, stdout=stdout, stderr=stderr)

    def test_known_wsl_service_e_unexpected_retries_once_and_records_diagnostics(self):
        result, run = self.run_worker_with([
            self.completed(4294967295, stderr="Wsl/Service/E_UNEXPECTED: transient launch error"),
            self.completed(0, stdout=json.dumps({"status": "success", "action": "smoke_test"})),
        ])
        self.assertEqual(run.call_count, 2)
        self.assertEqual(result["adapter_diagnostics"]["attempts"], 2)
        self.assertEqual(result["adapter_diagnostics"]["transient_service_retries"], 1)
        self.assertLessEqual(result["adapter_diagnostics"]["elapsed_seconds"], 1.0)

    def test_service_error_after_single_retry_preserves_full_diagnostic(self):
        detail = "Wsl/Service/E_UNEXPECTED: " + ("service details " * 100)
        with patch.object(self.adapter, "get_worker_wsl_path", return_value="/worker.py"), \
             patch("backend.services.wsl_quantum_adapter.subprocess.run", side_effect=[
                 self.completed(4294967295, stderr=detail),
                 self.completed(4294967295, stderr=detail),
             ]) as run, \
             patch("backend.services.wsl_quantum_adapter.time.sleep"):
            with self.assertRaises(WSLServiceError) as caught:
                self.adapter._execute_worker({"action": "analyze_molecule"}, timeout=12)
        self.assertEqual(run.call_count, 2)
        self.assertIn("2 attempt(s)", str(caught.exception))
        self.assertIn("Wsl/Service/E_UNEXPECTED", str(caught.exception))
        self.assertGreater(len(str(caught.exception)), 400)

    def test_signal_termination_is_not_retried_and_identifies_possible_oom(self):
        with patch.object(self.adapter, "get_worker_wsl_path", return_value="/worker.py"), \
             patch("backend.services.wsl_quantum_adapter.subprocess.run", return_value=self.completed(9)) as run:
            with self.assertRaises(WSLResourceError) as caught:
                self.adapter._execute_worker({"action": "analyze_molecule"}, timeout=12)
        self.assertEqual(run.call_count, 1)
        self.assertIn("memory exhaustion", str(caught.exception))
        self.assertIn("code 9", str(caught.exception))

    def test_timeout_is_not_retried_and_includes_elapsed_time(self):
        exc = subprocess.TimeoutExpired("wsl", 12, stderr="worker still active")
        with patch.object(self.adapter, "get_worker_wsl_path", return_value="/worker.py"), \
             patch("backend.services.wsl_quantum_adapter.subprocess.run", side_effect=exc) as run:
            with self.assertRaises(WSLTimeoutError) as caught:
                self.adapter._execute_worker({"action": "analyze_molecule"}, timeout=12)
        self.assertEqual(run.call_count, 1)
        self.assertIn("timed out after 12s", str(caught.exception))
        self.assertIn("worker still active", str(caught.exception))

    def test_resource_ineligible_geometry_is_skipped_before_subprocess(self):
        adapter = WSLQuantumAdapter()
        geometry = "; ".join(f"C {index}.0 0 0" for index in range(21))
        with patch.object(adapter, "_execute_worker") as execute:
            result = adapter.analyze_geometry(geometry)
        self.assertEqual(result["status"], "skipped_resource_limit")
        self.assertIn("Heavy-atom count", result["resource_eligibility"]["reasons"][0])
        execute.assert_not_called()

    def test_worker_resource_skip_happens_before_pyscf_setup(self):
        geometry = "; ".join(f"C {index}.0 0 0" for index in range(21))
        with patch("quantum.chemistry.molecule.build_molecular_problem", side_effect=AssertionError("must not run")) as build:
            result = _run_molecular_analysis({"atom": geometry, "basis": "sto3g", "maxiter": 50})
        self.assertEqual(result["result"]["status"], "skipped_resource_limit")
        self.assertIn("resource_preflight", result["result"]["stage_diagnostics"])
        build.assert_not_called()


class PartialQuantumPipelineTests(unittest.TestCase):
    def test_one_candidate_failure_does_not_hide_other_candidate_result(self):
        memory = MemoryMCPServer()
        memory.init_pipeline("failure-test", "test")
        memory._store("molecules", [
            {"id": "GEN-FAIL", "smiles": "CCO", "category": "novel"},
            {"id": "GEN-OK", "smiles": "CCN", "category": "novel"},
        ])
        success = {"status": "success", "method": "VQE", "vqe": {"electronic_energy_hartree": -1.0}}
        with patch("quantum.chemistry.quantum_analysis.analyze_smiles", side_effect=[RuntimeError("simulated worker OOM"), success]):
            summary = QuantumAnalysisAgent({"memory": memory}).run({})
        results = memory._retrieve("molecules")["value"]
        self.assertEqual(summary["failed"], 1)
        self.assertEqual(summary["successful"], 1)
        self.assertEqual(results[0]["quantum_analysis"]["status"], "failed")
        self.assertEqual(results[0]["quantum_analysis"]["error_type"], "RuntimeError")
        self.assertEqual(results[1]["quantum_analysis"]["status"], "success")

    def test_resource_skip_and_failure_preserve_other_candidate_fields(self):
        memory = MemoryMCPServer()
        memory.init_pipeline("partial-test", "test")
        memory._store("molecules", [
            {"id": "GEN-SKIP", "smiles": "CC", "category": "novel", "generation_provenance": {"method": "test"}},
            {"id": "GEN-FAIL", "smiles": "CCO", "category": "novel", "descriptors": {"mw": 46}},
            {"id": "GEN-OK", "smiles": "CCN", "category": "novel", "rank": 2},
        ])
        skipped = {"status": "skipped_resource_limit", "message": "above test limit"}
        success = {"status": "success", "method": "VQE", "vqe": {"electronic_energy_hartree": -1.0}}
        with patch("quantum.chemistry.quantum_analysis.analyze_smiles", side_effect=[skipped, RuntimeError("mock worker exit 9"), success]):
            response = QuantumAnalysisAgent({"memory": memory}).execute({})
        summary = response["data"]
        results = memory._retrieve("molecules")["value"]
        self.assertEqual(summary["successful"], 1)
        self.assertEqual(summary["failed"], 1)
        self.assertEqual(summary["skipped_resource_limit"], 1)
        self.assertEqual(results[0]["quantum_analysis"]["status"], "skipped_resource_limit")
        self.assertEqual(results[0]["generation_provenance"], {"method": "test"})
        self.assertEqual(results[1]["descriptors"], {"mw": 46})
        self.assertEqual(results[2]["quantum_analysis"]["status"], "success")
        self.assertEqual(response["status"], "completed")
        self.assertEqual(response["data"]["total_candidates"], 3)
        self.assertEqual(response["data"]["quantum_candidates"], 3)
        for candidate in results:
            self.assertGreaterEqual(candidate["quantum_analysis"]["elapsed_seconds"], 0)


if __name__ == "__main__":
    unittest.main()
