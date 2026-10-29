"""Integrity tests for the repeated EGFR scaffold validation artifacts."""

import csv
import json
import unittest
from pathlib import Path

import numpy as np

from benchmark_egfr_scaffold_validation import (
    OUT_DIR,
    SEEDS,
    assert_split_integrity,
    grouped_split,
    validate_dataset,
)


class EgfrScaffoldValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.compounds, cls.valid_indices, cls.groups, cls.invalid = (
            validate_dataset()
        )
        cls.y = cls.data["y"]
        cls.groups_full = np.empty(len(cls.y), dtype=object)
        cls.groups_full[:] = ""
        cls.groups_full[cls.valid_indices] = cls.groups
        cls.results = json.loads((OUT_DIR / "results.json").read_text(encoding="utf-8"))

    def test_rdkit_groups_reproduce_saved_groups_and_invalid_row_is_excluded(self):
        self.assertEqual(self.invalid.tolist(), [0])
        self.assertEqual(len(self.valid_indices), 2995)
        self.assertEqual(len(np.unique(self.groups)), 1129)

    def test_group_splits_are_deterministic_and_disjoint(self):
        for seed in SEEDS:
            first = grouped_split(self.valid_indices, self.y, self.groups_full, seed)
            second = grouped_split(self.valid_indices, self.y, self.groups_full, seed)
            for partition in ("train", "validation", "test"):
                np.testing.assert_array_equal(first[partition], second[partition])
            assert_split_integrity(first, self.groups_full)

    def test_audit_has_complete_membership_and_no_scaffold_crossing(self):
        audit_path = OUT_DIR / "split_membership_audit.csv"
        with audit_path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), len(self.valid_indices) * len(SEEDS))
        for seed in SEEDS:
            seed_rows = [row for row in rows if int(row["seed"]) == seed]
            self.assertEqual(len(seed_rows), len(self.valid_indices))
            self.assertEqual(
                len({int(row["source_row_index"]) for row in seed_rows}),
                len(self.valid_indices),
            )
            by_partition = {
                part: [row for row in seed_rows if row["partition"] == part]
                for part in ("train", "validation", "test")
            }
            for left, right in (("train", "validation"), ("train", "test"), ("validation", "test")):
                self.assertFalse(
                    {row["murcko_scaffold_id"] for row in by_partition[left]}
                    & {row["murcko_scaffold_id"] for row in by_partition[right]}
                )

    def test_aggregate_statistics_and_quantum_scope_are_explicit(self):
        self.assertEqual(len(self.results["per_split_results"]), len(SEEDS))
        self.assertFalse(
            self.results["evaluation_protocol"][
                "test_labels_used_for_selection_or_preprocessing"
            ]
        )
        for model in ("rbf_svr", "random_forest"):
            for metric in ("mae", "rmse", "r2"):
                values = [
                    fold["test_metrics"][model][metric]
                    for fold in self.results["per_split_results"]
                ]
                summary = self.results["aggregate_test_metrics"][model][metric]
                self.assertAlmostEqual(summary["mean"], float(np.mean(values)))
                self.assertAlmostEqual(
                    summary["sample_standard_deviation"], float(np.std(values, ddof=1))
                )
        quantum = self.results["quantum_comparability"]
        self.assertTrue(
            quantum["existing_quantum_pilot_can_be_compared_on_its_original_single_split"]
        )
        self.assertFalse(quantum["quantum_artifact_availability"]["per_compound_quantum_predictions"])
        self.assertFalse(quantum["quantum_artifact_availability"]["kernel_matrices"])


if __name__ == "__main__":
    unittest.main()
