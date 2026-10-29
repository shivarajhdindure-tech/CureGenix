"""Unit tests for the EGFR Benchmark & Validation API."""

import unittest
from backend.services.benchmark_api import (
    ALLOWED_REPORTS,
    get_egfr_benchmark_data,
    get_egfr_report,
)


class BenchmarkApiTests(unittest.TestCase):
    def test_benchmark_data_structure(self):
        data = get_egfr_benchmark_data()

        # Requirement 6: status indicators
        self.assertIn("status_indicators", data)
        self.assertEqual(
            data["status_indicators"]["classical_validation"],
            "Classical scaffold validation complete",
        )
        self.assertEqual(
            data["status_indicators"]["quantum_validation"],
            "Repeated scaffold-split quantum validation pending",
        )

        # Dataset details
        self.assertEqual(data["dataset"]["evaluated_compounds"], 2995)
        self.assertEqual(data["dataset"]["unique_murcko_scaffolds"], 1129)
        self.assertEqual(len(data["dataset"]["excluded_compounds"]), 1)

        # Requirement 2: 5-split classical results
        classical = data["five_split_classical"]["models"]
        self.assertEqual(classical["rbf_svr"]["mae"]["formatted"], "0.5607 ± 0.0689")
        self.assertEqual(classical["rbf_svr"]["rmse"]["formatted"], "0.7609 ± 0.0883")
        self.assertEqual(classical["rbf_svr"]["r2"]["formatted"], "0.6061 ± 0.0496")

        self.assertEqual(classical["random_forest"]["mae"]["formatted"], "0.5270 ± 0.0672")
        self.assertEqual(classical["random_forest"]["rmse"]["formatted"], "0.7286 ± 0.0758")
        self.assertEqual(classical["random_forest"]["r2"]["formatted"], "0.6386 ± 0.0394")

        # Requirement 3: matched pilot comparison
        pilot = data["single_split_pilot_comparison"]["models"]
        self.assertAlmostEqual(pilot["quantum_kernel_svr"]["test_mae"], 0.9435, places=4)
        self.assertAlmostEqual(pilot["quantum_kernel_svr"]["test_rmse"], 1.1234, places=4)
        self.assertAlmostEqual(pilot["quantum_kernel_svr"]["test_r2"], -0.0531, places=4)

        self.assertAlmostEqual(pilot["classical_rbf_svr"]["test_mae"], 0.6476, places=4)
        self.assertAlmostEqual(pilot["classical_rbf_svr"]["test_rmse"], 0.9045, places=4)
        self.assertAlmostEqual(pilot["classical_rbf_svr"]["test_r2"], 0.3172, places=4)

        self.assertAlmostEqual(pilot["classical_random_forest"]["test_mae"], 0.6166, places=4)
        self.assertAlmostEqual(pilot["classical_random_forest"]["test_rmse"], 0.7839, places=4)
        self.assertAlmostEqual(pilot["classical_random_forest"]["test_r2"], 0.4872, places=4)

        # Requirement 5: simulator disclosure & no quantum advantage claim
        quantum_exec = data["single_split_pilot_comparison"]["quantum_execution"]
        self.assertFalse(quantum_exec["is_quantum_hardware"])
        self.assertFalse(quantum_exec["quantum_advantage_claimed"])
        self.assertEqual(quantum_exec["landmark_count_verified"], 4)
        self.assertIn("Statevector", quantum_exec["hardware"])

    def test_report_retrieval(self):
        for report_id in ALLOWED_REPORTS:
            report = get_egfr_report(report_id)
            self.assertEqual(report["id"], report_id)
            self.assertTrue(len(report["content"]) > 100)
            self.assertTrue(report["content"].startswith("#"))

    def test_invalid_report_id_raises_404(self):
        from fastapi import HTTPException
        with self.assertRaises(HTTPException) as ctx:
            get_egfr_report("malicious_path_or_unknown_id")
        self.assertEqual(ctx.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
