import csv
import json
import unittest
from pathlib import Path

from sklearn.metrics import accuracy_score, balanced_accuracy_score, roc_auc_score


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "benchmark_reports" / "egfr_regression" / "vqc_qgnn_same_day_v3"


class VQCQGNNExperimentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.results = json.loads((EXPERIMENT / "results.json").read_text(encoding="utf-8"))
        with (EXPERIMENT / "split_membership.csv").open(encoding="utf-8", newline="") as handle:
            cls.membership = list(csv.DictReader(handle))
        with (EXPERIMENT / "heldout_predictions.csv").open(encoding="utf-8", newline="") as handle:
            cls.predictions = list(csv.DictReader(handle))

    def test_training_subset_and_scaffolds_are_disjoint(self):
        selected = [r for r in self.membership if r["selected_for_training"].lower() == "true"]
        self.assertEqual(len(selected), 128)
        self.assertTrue(all(r["original_partition"] == "train" for r in selected))
        groups = {
            part: {r["murcko_scaffold"] for r in self.membership if r["original_partition"] == part and r["label"] != "excluded"}
            for part in ("train", "validation", "test")
        }
        for a, b in (("train", "validation"), ("train", "test"), ("validation", "test")):
            self.assertFalse(groups[a] & groups[b])

    def test_all_three_heldout_metrics_reproduce_from_saved_predictions(self):
        test = [r for r in self.predictions if r["partition"] == "test"]
        y = [int(r["label"]) for r in test]
        field_map = {
            "vqc": ("vqc_prediction", "vqc_probability_active_uncalibrated"),
            "qgnn": ("qgnn_prediction", "qgnn_probability_active_uncalibrated"),
            "classical_rbf_svm": ("classical_rbf_svm_prediction", "classical_rbf_svm_score"),
        }
        for model, (prediction_key, score_key) in field_map.items():
            predicted = [int(r[prediction_key]) for r in test]
            scores = [float(r[score_key]) for r in test]
            saved = self.results["metrics"][model]["test"]
            self.assertAlmostEqual(accuracy_score(y, predicted), saved["accuracy"], places=12)
            self.assertAlmostEqual(balanced_accuracy_score(y, predicted), saved["balanced_accuracy"], places=12)
            self.assertAlmostEqual(roc_auc_score(y, scores), saved["roc_auc"], places=12)

    def test_saved_model_artifacts_exist_and_optimizer_limit_is_disclosed(self):
        self.assertTrue((EXPERIMENT / "vqc_model.joblib").is_file())
        self.assertTrue((EXPERIMENT / "qgnn_model.joblib").is_file())
        qgnn_status = self.results["models"]["qgnn"]["training"]["status"]
        self.assertIn(qgnn_status, {"converged", "completed_max_evaluations"})


if __name__ == "__main__":
    unittest.main()
