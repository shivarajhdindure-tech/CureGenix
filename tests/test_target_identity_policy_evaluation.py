"""Reproducible regression checks for the target identity policy fixture set."""

import json
from pathlib import Path
import unittest

from scripts.evaluate_target_identity_policy import evaluate_cases
from backend.services.target_sequence import SequenceValidationPolicy


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs" / "target_identity_policy_fixtures.json"


class TargetIdentityPolicyEvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        cls.results = evaluate_cases(cls.manifest, ROOT)
        cls.by_id = {case["case_id"]: case for case in cls.results["cases"]}

    def test_every_manifest_case_runs_and_expected_decisions_are_explicit(self):
        manifest_ids = [case["case_id"] for case in self.manifest["cases"]]
        self.assertEqual(len(manifest_ids), len(set(manifest_ids)))
        self.assertEqual(set(manifest_ids), set(self.by_id))
        for item in self.manifest["cases"]:
            result = self.by_id[item["case_id"]]
            self.assertEqual(result["expected_generation_allowed"], item["expected_generation_allowed"])
            self.assertEqual(result["expected_state"], item["expected_state"])

    def test_default_policy_is_unchanged_and_reproducible(self):
        policy = SequenceValidationPolicy()
        self.assertEqual(policy.min_identity_fraction, 0.90)
        self.assertEqual(policy.min_observed_coverage, 0.80)
        self.assertEqual(policy.min_reference_coverage, 0.15)
        self.assertEqual(policy.min_aligned_residues, 100)
        self.assertEqual(policy.max_gap_fraction, 0.10)
        self.assertEqual(self.results["evaluation_policy"]["source"], "explicit SequenceValidationPolicy defaults; environment overrides are not applied")

    def test_known_synthetic_false_acceptance_risks_remain_visible(self):
        summary = self.results["summary"]
        self.assertEqual(summary["false_acceptance_cases"], [
            "synthetic_close_homolog_8pct",
            "synthetic_local_match_150_of_500",
        ])
        close_homolog = self.by_id["synthetic_close_homolog_8pct"]
        self.assertAlmostEqual(close_homolog["validation"]["identity_fraction"], 0.916)
        self.assertEqual(close_homolog["validation"]["reference_sequence_coverage"], 1.0)
        local_match = self.by_id["synthetic_local_match_150_of_500"]
        self.assertAlmostEqual(local_match["validation"]["reference_sequence_coverage"], 0.30)
        self.assertTrue(local_match["sequence_policy_allows_generation"])
        self.assertTrue(local_match["actual_generation_allowed"])

    def test_short_and_external_or_unsupported_identity_states_stay_product_disabled(self):
        for case_id in (
            "synthetic_local_match_60_of_500",
            "synthetic_missing_dbref_external_accession",
            "synthetic_unsupported_dbref1_dbref2",
            "synthetic_missing_dbref_no_accession",
            "synthetic_multiple_chains",
            "synthetic_conflicting_dbref",
        ):
            with self.subTest(case_id=case_id):
                self.assertFalse(self.by_id[case_id]["actual_generation_allowed"])
        extended = self.by_id["synthetic_unsupported_dbref1_dbref2"]
        self.assertEqual(extended["actual_state"], "externally_verified")
        self.assertTrue(extended["unsupported_dbref1_dbref2"])
        self.assertFalse(extended["configured_target_reference_available"])

    def test_partial_constructs_engineered_variants_and_indels_are_reported(self):
        for case_id in (
            "synthetic_terminal_truncation_60pct",
            "synthetic_engineered_substitutions_3",
            "synthetic_internal_deletion_12",
            "synthetic_internal_insertion_8",
        ):
            with self.subTest(case_id=case_id):
                result = self.by_id[case_id]
                self.assertEqual(result["actual_state"], "structure_linked_partial_sequence_support")
                self.assertTrue(result["actual_generation_allowed"])
        self.assertEqual(self.by_id["synthetic_engineered_substitutions_3"]["validation"]["substitution_count"], 3)
        self.assertEqual(self.by_id["synthetic_internal_deletion_12"]["validation"]["deletion_count"], 12)
        self.assertEqual(self.by_id["synthetic_internal_insertion_8"]["validation"]["insertion_count"], 8)

    def test_real_1crn_canonical_difference_is_not_mislabeled_as_exact(self):
        result = self.by_id["real_1crn_chain_a_p01542"]
        self.assertEqual(result["label_confidence"], "source_conflict")
        self.assertEqual(result["actual_state"], "insufficient_sequence_evidence")
        self.assertFalse(result["actual_generation_allowed"])
        self.assertAlmostEqual(result["validation"]["identity_fraction"], 45 / 46)
        self.assertEqual(result["validation"]["substitutions"][0]["reference_position"], 25)
        self.assertEqual(result["diagnostic_validation"]["identity_state"], "structure_linked_partial_sequence_support")

    def test_unrelated_sequences_reject_generation_even_when_state_is_insufficient(self):
        result = self.by_id["synthetic_unrelated_sequence"]
        self.assertEqual(result["actual_state"], "insufficient_sequence_evidence")
        self.assertFalse(result["actual_generation_allowed"])
        self.assertLess(result["validation"]["informative_aligned_residues"], 100)


if __name__ == "__main__":
    unittest.main()
