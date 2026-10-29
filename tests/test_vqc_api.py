"""HTTP integration coverage for the read-only saved VQC endpoint."""

import unittest

from fastapi.testclient import TestClient

from backend.main import app


class VQCApiTests(unittest.TestCase):
    def test_saved_egfr_result_is_exposed_without_training(self):
        with TestClient(app) as client:
            response = client.get("/api/vqc/egfr")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "completed")
        self.assertIn("vqc", payload["evaluation"]["metrics"])
        self.assertIn("classical_rbf_svm", payload["evaluation"]["metrics"])
        self.assertFalse(payload["evaluation"].get("quantum_advantage_claimed", False))


if __name__ == "__main__":
    unittest.main()
