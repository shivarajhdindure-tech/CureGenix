"""Keep displayed benchmark summaries aligned with their saved experiment records."""

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GRAPH_PATH = ROOT / "frontend-next/components/charts/ClassicalVsQuantumComparisonGraph.js"
SCIENTIFIC_CHARTS_PATH = ROOT / "frontend-next/components/charts/ScientificCharts.js"
ARTIFACTS = ROOT / "benchmark_reports/egfr_regression"


def _json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _records(source, array_declaration, key_field="id"):
    match = re.search(
        re.escape(array_declaration) + r"(.*?)\n\s*\];",
        source,
        re.DOTALL,
    )
    if not match:
        raise AssertionError(f"Could not locate {array_declaration} in frontend source")
    records = {}
    for item in re.finditer(
        rf'\{{\s*{key_field}:\s*"([^"]+)"(.*?)\n\s*\}}',
        match.group(1),
        re.DOTALL,
    ):
        values = {key_field: item.group(1)}
        for field in ("label", "name", "value", "formattedValue", "errorStd", "balancedAccuracy", "rocAuc", "mae", "rmse", "r2"):
            found = re.search(rf'{field}:\s*(?:"([^"]*)"|(-?\d+(?:\.\d+)?))', item.group(2))
            if found:
                values[field] = found.group(1) if found.group(1) is not None else float(found.group(2))
        records[item.group(1)] = values
    return records


def _assert_close(test, actual, expected, places=4):
    test.assertAlmostEqual(float(actual), float(expected), places=places)


class ClassicalQuantumGraphIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graph_source = GRAPH_PATH.read_text(encoding="utf-8")
        cls.scientific_source = SCIENTIFIC_CHARTS_PATH.read_text(encoding="utf-8")
        cls.classification = _json(ARTIFACTS / "vqc_qgnn_same_day_v3/results.json")
        cls.pilot = _json(ARTIFACTS / "classical_quantum_comparison_16d_pilot/comparison_results.json")
        cls.repeated = _json(ARTIFACTS / "scaffold_validation/results.json")

    def test_metric_series_and_labels_match_saved_artifacts(self):
        metrics = self.classification["metrics"]
        bal_acc = _records(self.graph_source, "const classificationBalAccData = [")
        roc_auc = _records(self.graph_source, "const classificationRocAucData = [")
        for model_id, artifact_id, label in (
            ("rbf_svm", "classical_rbf_svm", "Classical RBF-SVM"),
            ("vqc", "vqc", "Quantum VQC"),
            ("qgnn", "qgnn", "Molecular QGNN"),
        ):
            self.assertEqual(bal_acc[model_id]["label"], label)
            self.assertEqual(roc_auc[model_id]["label"], label)
            _assert_close(self, bal_acc[model_id]["value"], metrics[artifact_id]["test"]["balanced_accuracy"] * 100, 2)
            _assert_close(self, roc_auc[model_id]["value"], metrics[artifact_id]["test"]["roc_auc"], 4)

        pilot_values = self.pilot["results"]
        model_aliases = {
            "rf_16d": ("classical_random_forest_16d", "Classical Random Forest"),
            "rbf_svr_16d": ("classical_rbf_svr_16d", "Classical RBF-SVR"),
            "quantum_svr_16d": ("saved_quantum_nystrom_svr", "Quantum-Kernel SVR"),
        }
        for chart_array, metric in (("pilotMaeData", "mae"), ("pilotRmseData", "rmse"), ("pilotR2Data", "r2")):
            chart = _records(self.graph_source, f"const {chart_array} = [")
            for chart_id, (artifact_id, label) in model_aliases.items():
                self.assertEqual(chart[chart_id]["label"], label)
                _assert_close(self, chart[chart_id]["value"], pilot_values[artifact_id]["test"][metric], 4)

        aggregate = self.repeated["aggregate_test_metrics"]
        repeated_aliases = {"rf_5split": "random_forest", "svr_5split": "rbf_svr"}
        for chart_array, metric in (("fiveSplitMaeData", "mae"), ("fiveSplitRmseData", "rmse"), ("fiveSplitR2Data", "r2")):
            chart = _records(self.graph_source, f"const {chart_array} = [")
            for chart_id, artifact_id in repeated_aliases.items():
                _assert_close(self, chart[chart_id]["value"], aggregate[artifact_id][metric]["mean"], 4)
                _assert_close(self, chart[chart_id]["errorStd"], aggregate[artifact_id][metric]["sample_standard_deviation"], 4)

    def test_scientific_charts_duplicate_values_match_saved_artifacts(self):
        activity = _records(self.scientific_source, "const metrics = data || [")
        for model_id in ("vqc", "qgnn", "classical_rbf_svm"):
            saved = self.classification["metrics"][model_id]["test"]
            _assert_close(self, activity[model_id]["balancedAccuracy"], saved["balanced_accuracy"], 4)
            _assert_close(self, activity[model_id]["rocAuc"], saved["roc_auc"], 4)

        pilot = _records(self.scientific_source, "const pilotModels = [", key_field="name")
        saved_pilot = self.pilot["results"]
        for chart_name, artifact_id in (
            ("Quantum-Kernel SVR (16D)", "saved_quantum_nystrom_svr"),
            ("Classical RBF-SVR (16D)", "classical_rbf_svr_16d"),
            ("Classical Random Forest (16D)", "classical_random_forest_16d"),
        ):
            for metric in ("mae", "rmse", "r2"):
                _assert_close(self, pilot[chart_name][metric], saved_pilot[artifact_id]["test"][metric], 4)

    def test_counts_split_labels_and_activity_scope_are_accurate(self):
        self.assertEqual(self.graph_source.count("<CartesianBarChart"), 8)
        self.assertIn("All Graphs (8)", self.graph_source)
        self.assertIn("5-Seed Repeated Holdout", self.graph_source)
        self.assertNotIn("5-Fold", self.graph_source)
        self.assertNotIn("5-Fold", self.scientific_source)
        self.assertEqual(self.pilot["sample_alignment"]["split_sizes"]["test"], 64)
        self.assertIn("Curated biochemical IC50 activity-proxy cohort", self.graph_source)
        self.assertIn("Curated biochemical IC50 activity-proxy cohort", self.scientific_source)
        self.assertIn("pIC50 Points", self.graph_source)
        self.assertNotIn("pIC50 Units", self.graph_source)
        self.assertIn("No quantum results are available for the five-seed splits", self.graph_source)

    def test_training_and_hardware_diagnostic_disclosures_match_records(self):
        vqc = self.classification["models"]["vqc"]["training"]
        qgnn = self.classification["models"]["qgnn"]["training"]
        self.assertIsNone(vqc["optimizer_success"])
        self.assertFalse(vqc["optimizer_status_available"])
        self.assertEqual(qgnn["status"], "completed_max_evaluations")
        self.assertFalse(qgnn["optimizer_success"])
        self.assertIn("convergence was not reported", self.graph_source.lower())
        self.assertIn(f"maximum of {qgnn['objective_evaluations']} objective evaluations", self.graph_source)
        self.assertIn("optimizer_success=false", self.graph_source)

        vqc_hardware = _json(ROOT / "experiments/ibm_results/curegenix_vqc_dbhnetune4hc73bd8h70.json")
        qgnn_hardware = _json(ROOT / "experiments/ibm_results/curegenix_qgnn_dbhm4ntep8hs73amelf0.json")
        vqc_divergence_pct = round(max(vqc_hardware["absolute_difference_by_class"]) * 100, 2)
        qgnn_divergence_pct = round(qgnn_hardware["absolute_difference_from_local"] * 100, 1)
        self.assertEqual(vqc_divergence_pct, 11.28)
        self.assertEqual(qgnn_divergence_pct, 3.0)
        self.assertIn("11.28 percentage points for VQC", self.graph_source)
        self.assertIn("approximately 3.0 percentage points for QGNN", self.graph_source)
        self.assertIn("not the molecular activity benchmark scores", self.graph_source)
        self.assertIn("11.28 and approximately 3.0 percentage points, respectively", self.graph_source)
        self.assertNotIn("always outperform", self.graph_source.lower())


if __name__ == "__main__":
    unittest.main()
