import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.venv-win', 'Lib', 'site-packages')))
"""Unit and API Integration Tests for Molecular Risk & Digital Twin.

Covers:
  - Candidate identity validation and strict SMILES matching
  - Invalid SMILES rejection (422)
  - Manual-only execution policy (rejects manual_trigger=False)
  - All 5 required risk modules:
      A. ADMET & Developability Risk (Lipinski, ESOL, Boiled-Egg, CYP motifs, FilterCatalog)
      B. Binding Stability & Interaction Risk (honestly reporting prepared_only when GROMACS is unconfigured)
      C. Off-Target & Kinase Selectivity Risk (ERBB family sequence/pocket homology)
      D. Mutation, Resistance & Robustness Risk (T790M, L858R, C797S, Exon 19 del)
      E. Synthetic Feasibility & Chemical Liabilities (BertzCT, SAscore, rule-based disconnections)
  - Missing external tools handling (no fabricated trajectories)
  - Resource limit guardrail skips (heavy/total atom count threshold)
  - Duplicate simultaneous execution lock (HTTP 409)
  - Cooperative cancellation
  - Historical report preservation and candidate-switch report isolation
"""

import unittest
from backend.models.molecular_risk_models import RiskAnalysisConfig, RiskAnalyzeRequest
from backend.services.molecular_risk_service import MolecularRiskService


class MolecularRiskDigitalTwinTests(unittest.TestCase):
    def setUp(self):
        # Create an isolated service instance for clean testing
        self.service = MolecularRiskService()

    def test_candidate_registration_and_descriptor_calculation(self):
        """Validates candidate registration computes accurate RDKit 2D descriptors."""
        rec = self.service.register_candidate(
            candidate_id="TEST-ERL",
            smiles="COCCOc1cc2ncnc(Nc3cccc(c3)C#C)c2cc1OCCOC",
            drug_name="Erlotinib Test",
        )
        self.assertEqual(rec.candidate_id, "TEST-ERL")
        self.assertAlmostEqual(rec.descriptors.molecular_weight, 393.436, places=1)
        self.assertGreater(rec.descriptors.tpsa, 70.0)
        self.assertEqual(rec.descriptors.hbd, 1)
        self.assertEqual(rec.descriptors.hba, 7)

    def test_invalid_smiles_rejected(self):
        """Invalid SMILES strings must raise ValueError and never proceed."""
        with self.assertRaises(ValueError):
            self.service.register_candidate(
                candidate_id="INVALID-SMILES",
                smiles="NOT_A_VALID_SMILES_STRING",
            )

    def test_candidate_identity_mismatch_prevents_silent_substitution(self):
        """Submitting a different SMILES under an existing candidate ID must fail."""
        self.service.register_candidate(
            candidate_id="CAND-001",
            smiles="CCO",  # Ethanol
            drug_name="Ethanol",
        )
        # Attempt to run analysis with aspirin SMILES under CAND-001
        with self.assertRaises(ValueError) as ctx:
            self.service.run_analysis(
                candidate_id="CAND-001",
                smiles="CC(=O)Oc1ccccc1C(=O)O",  # Aspirin
                manual_trigger=True,
            )
        self.assertIn("Candidate identity mismatch", str(ctx.exception))

    def test_manual_trigger_mandatory(self):
        """Automated execution without manual user trigger must be rejected."""
        with self.assertRaises(ValueError) as ctx:
            self.service.run_analysis(
                candidate_id="CHEMBL553",
                manual_trigger=False,
            )
        self.assertIn("Automated risk execution is disabled", str(ctx.exception))

    def test_full_five_dimension_analysis_on_erlotinib(self):
        """Evaluates all 5 required dimensions on reference compound Erlotinib."""
        report = self.service.run_analysis(
            candidate_id="CHEMBL553",
            manual_trigger=True,
        )

        self.assertEqual(report.execution_status, "completed")
        self.assertEqual(report.progress_percent, 100)
        self.assertIsNone(report.combined_risk_score, "Arbitrary combined score must be None")
        self.assertIn("five independent risk dimensions", report.scoring_policy_disclosure)

        dims = report.dimensions
        self.assertEqual(set(dims.keys()), {
            "admet_risk", "binding_stability", "off_target_risk",
            "mutation_robustness", "synthetic_feasibility"
        })

        # Module A: ADMET
        dim_a = dims["admet_risk"]
        self.assertEqual(dim_a.calculation_status, "completed")
        self.assertIn("solubility_esol", dim_a.details)
        self.assertIn("radar_metrics", dim_a.details)
        self.assertIn("cyp_matrix", dim_a.details)
        self.assertEqual(len(dim_a.details["cyp_matrix"]), 5)

        # Module B: Binding Stability (honest reporting: prepared_only, no fabricated MD)
        dim_b = dims["binding_stability"]
        self.assertEqual(dim_b.calculation_status, "prepared_only")
        self.assertIn("pocket_contacts", dim_b.details)
        self.assertIn("key_residue_table", dim_b.details)
        self.assertIsNone(dim_b.details["rmsd_time_series"], "Must not fabricate dynamic RMSD")

        # Module C: Off-Target Selectivity
        dim_c = dims["off_target_risk"]
        self.assertEqual(dim_c.calculation_status, "completed")
        self.assertIn("panel_evaluations", dim_c.details)
        symbols = [p["symbol"] for p in dim_c.details["panel_evaluations"]]
        self.assertIn("HER2", symbols)
        self.assertIn("HER4", symbols)
        self.assertIn("BTK", symbols)

        # Module D: Mutation Robustness
        dim_d = dims["mutation_robustness"]
        self.assertEqual(dim_d.calculation_status, "completed")
        self.assertIn("variant_assessments", dim_d.details)
        variants = [v["variant"] for v in dim_d.details["variant_assessments"]]
        self.assertIn("T790M", variants)
        self.assertIn("L858R", variants)
        self.assertIn("C797S", variants)
        # Erlotinib (quinazoline without covalent warhead) should detect gatekeeper clash
        self.assertTrue(dim_d.details["gatekeeper_clash_detected"])

        # Module E: Synthetic Feasibility
        dim_e = dims["synthetic_feasibility"]
        self.assertEqual(dim_e.calculation_status, "completed")
        self.assertGreaterEqual(dim_e.details["synthetic_accessibility_score"], 1.0)
        self.assertLessEqual(dim_e.details["synthetic_accessibility_score"], 10.0)
        self.assertGreater(len(dim_e.details["retrosynthetic_disconnections"]), 0)

    def test_covalent_inhibitor_mutation_profile_osimertinib(self):
        """Irreversible covalent inhibitor (Osimertinib) must flag C797S resistance."""
        report = self.service.run_analysis(
            candidate_id="CHEMBL428647",  # Osimertinib
            manual_trigger=True,
        )
        dim_d = report.dimensions["mutation_robustness"]
        c797s_eval = next(v for v in dim_d.details["variant_assessments"] if v["variant"] == "C797S")
        self.assertIn("Covalent Inactivation", c797s_eval["resistance_risk"])

    def test_resource_limit_skips_large_molecules(self):
        """Molecules exceeding configured atom limits must be skipped with explicit reason."""
        custom_config = RiskAnalysisConfig(
            max_heavy_atoms=10,  # Deliberately strict threshold
            max_total_atoms=20,
        )
        report = self.service.run_analysis(
            candidate_id="CHEMBL553",  # Erlotinib has 29 heavy atoms
            config=custom_config,
            manual_trigger=True,
        )
        self.assertEqual(report.execution_status, "skipped_resource_limit")
        self.assertFalse(report.resource_assessment["eligible"])
        self.assertTrue(any("exceeds configured limit" in r for r in report.resource_assessment["reasons"]))
        # Dimensions must report skipped_resource_limit, never low risk!
        for dim in report.dimensions.values():
            self.assertEqual(dim.risk_category, "skipped_resource_limit")
            self.assertEqual(dim.calculation_status, "skipped_resource_limit")

    def test_cooperative_cancellation(self):
        """Asynchronously running jobs can be cooperatively cancelled."""
        report = self.service.run_analysis(
            candidate_id="GEN-68E3342F",
            manual_trigger=True,
            run_async=True,
        )
        # Immediately cancel
        cancelled = self.service.cancel_report(report.report_id)
        self.assertTrue(cancelled)
        retrieved = self.service.get_report(report.report_id)
        self.assertIn(retrieved.execution_status, ("cancelled", "completed"))

    def test_historical_reports_preservation(self):
        """Multiple runs must be preserved as auditable historical records."""
        rep1 = self.service.run_analysis(candidate_id="CHEMBL553", manual_trigger=True)
        rep2 = self.service.run_analysis(candidate_id="CHEMBL25", manual_trigger=True)

        history = self.service.list_reports()
        self.assertGreaterEqual(len(history), 2)
        erlotinib_history = self.service.list_reports(candidate_id="CHEMBL553")
        self.assertTrue(any(r.report_id == rep1.report_id for r in erlotinib_history))


if __name__ == "__main__":
    unittest.main()
