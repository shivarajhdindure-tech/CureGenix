"""Lightweight integrity tests for the saved EGFR pilot comparison."""

import csv
import json
import unittest
from pathlib import Path

import numpy as np

from benchmark_egfr_classical_quantum_comparison_16d_pilot import (
    DATA_PATH,
    FEATURES_PATH,
    OUT_DIR,
    PILOT_RESULT_PATH,
    validate_alignment,
)


class EgfrClassicalQuantumComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = np.load(DATA_PATH, allow_pickle=False)
        cls.features = np.load(FEATURES_PATH, allow_pickle=False)
        cls.pilot = json.loads(PILOT_RESULT_PATH.read_text(encoding="utf-8"))
        cls.comparison = json.loads(
            (OUT_DIR / "comparison_results.json").read_text(encoding="utf-8")
        )
        cls.indices = validate_alignment(cls.data, cls.features)

    def test_saved_pilot_rows_match_source_compounds_and_targets(self):
        self.assertEqual(
            {split: len(indices) for split, indices in self.indices.items()},
            {"train": 256, "validation": 64, "test": 64},
        )
        for split, indices in self.indices.items():
            np.testing.assert_array_equal(
                self.features[f"{split}_smiles"], self.data["smiles"][indices]
            )
            np.testing.assert_array_equal(
                self.features[f"{split}_y"], self.data["y"][indices]
            )

    def test_classical_comparison_uses_matched_split_and_correct_landmark_count(self):
        self.assertTrue(self.comparison["alignment_verified"])
        self.assertEqual(self.comparison["sample_alignment"]["pilot_compound_count"], 384)
        self.assertEqual(self.comparison["landmark_metadata"]["corrected_count"], 4)
        self.assertFalse(
            self.comparison["input_features"][
                "validation_or_test_used_for_fit_or_preprocessing"
            ]
        )
        self.assertEqual(
            self.comparison["results"]["saved_quantum_nystrom_svr"]["test"],
            self.pilot["metrics"]["test"],
        )

    def test_prediction_csv_preserves_exact_test_row_order_and_targets(self):
        csv_path = OUT_DIR / "test_predictions_classical.csv"
        with csv_path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 64)
        self.assertEqual(
            [row["smiles"] for row in rows], self.features["test_smiles"].tolist()
        )
        np.testing.assert_array_equal(
            np.array([float(row["pIC50_target"]) for row in rows]),
            self.features["test_y"],
        )


if __name__ == "__main__":
    unittest.main()
