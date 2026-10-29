import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.main import app
from backend.services import molecular_activity_api as activity


class MolecularActivityApiTests(unittest.TestCase):
    def test_offline_artifacts_predict_one_molecule_through_shared_endpoint(self):
        activity._load_vqc_bundle.cache_clear()
        activity._load_qgnn_bundle.cache_clear()
        with TestClient(app) as client:
            response = client.post("/api/molecular-activity/predict", json={"smiles": "CCO"})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["endpoint"], activity.ENDPOINT)
        self.assertEqual(set(payload["models"]), {"vqc", "qgnn", "classical_rbf_svm"})
        for result in (payload["models"]["vqc"], payload["models"]["qgnn"]):
            self.assertEqual(result["status"], "success")
            self.assertIn(result["prediction"], {"active_proxy", "inactive_proxy"})
            self.assertFalse(result["probability_calibrated"])
            self.assertGreaterEqual(result["runtime_seconds"], 0.0)
        self.assertEqual(payload["models"]["classical_rbf_svm"]["status"], "evaluation_only")
        activity._load_vqc_bundle.cache_clear()
        activity._load_qgnn_bundle.cache_clear()

    def test_same_rdkit_molecule_is_parsed_once_for_both_paths(self):
        activity._load_vqc_bundle.cache_clear()
        activity._load_qgnn_bundle.cache_clear()
        original = activity.Chem.MolFromSmiles
        with patch.object(activity.Chem, "MolFromSmiles", wraps=original) as parse:
            result = activity.predict_for_smiles("CCO")
        self.assertEqual(parse.call_count, 1)
        self.assertIn(result["models"]["vqc"]["status"], {"success", "failed", "not_trained"})
        self.assertIn(result["models"]["qgnn"]["status"], {"success", "failed", "not_trained"})
        activity._load_vqc_bundle.cache_clear()
        activity._load_qgnn_bundle.cache_clear()

    def test_valid_smiles_reports_each_untrained_model_without_fabrication(self):
        activity._load_vqc_bundle.cache_clear()
        activity._load_qgnn_bundle.cache_clear()
        with patch.object(activity, "VQC_PATH") as vqc_path, patch.object(activity, "QGNN_PATH") as qgnn_path:
            vqc_path.is_file.return_value = False
            qgnn_path.is_file.return_value = False
            with TestClient(app) as client:
                response = client.post("/api/molecular-activity/predict", json={"smiles": "CCO"})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["canonical_smiles"], "CCO")
        self.assertEqual(payload["models"]["vqc"]["status"], "not_trained")
        self.assertEqual(payload["models"]["qgnn"]["status"], "not_trained")
        self.assertNotIn("prediction", payload["models"]["vqc"])
        self.assertNotIn("prediction", payload["models"]["qgnn"])
        activity._load_vqc_bundle.cache_clear()
        activity._load_qgnn_bundle.cache_clear()

    def test_one_model_error_does_not_hide_the_other_status(self):
        activity._load_vqc_bundle.cache_clear()
        activity._load_qgnn_bundle.cache_clear()
        with patch.object(activity, "_load_vqc_bundle", side_effect=RuntimeError("mock VQC error")), patch.object(
            activity, "_load_qgnn_bundle", side_effect=FileNotFoundError("QGNN not trained")
        ):
            result = activity.predict_for_smiles("CCO")
        self.assertEqual(result["models"]["vqc"]["status"], "failed")
        self.assertEqual(result["models"]["qgnn"]["status"], "not_trained")

    def test_invalid_smiles_is_rejected_once_at_api_boundary(self):
        with TestClient(app) as client:
            response = client.post("/api/molecular-activity/predict", json={"smiles": "not-a-smiles"})
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
