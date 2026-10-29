import unittest
from unittest.mock import patch

from backend.services.quantum_resource_policy import (
    assess_geometry_resources,
    assess_smiles_resources,
)


class QuantumResourcePolicyTests(unittest.TestCase):
    def test_small_molecule_is_eligible_under_default_policy(self):
        result = assess_smiles_resources("O")
        self.assertEqual(result["status"], "eligible")
        self.assertTrue(result["eligible"])

    def test_heavy_atom_limit_is_configurable_and_reports_reason(self):
        with patch.dict("os.environ", {"CUREGENIX_QUANTUM_MAX_HEAVY_ATOMS": "1"}):
            result = assess_smiles_resources("CC")
        self.assertEqual(result["status"], "skipped_resource_limit")
        self.assertIn("Heavy-atom count", result["reasons"][0])
        self.assertIn("no memory prediction", result["estimation_method"])

    def test_iteration_and_basis_parameters_are_checked(self):
        result = assess_smiles_resources("O", basis="def2-svp", maxiter=101)
        self.assertEqual(result["status"], "skipped_resource_limit")
        self.assertEqual(len(result["reasons"]), 2)

    def test_unknown_element_has_explicit_skip_without_basis_estimate(self):
        result = assess_geometry_resources("Xe 0 0 0")
        self.assertEqual(result["status"], "skipped_resource_limit")
        self.assertIsNone(result["resource_metrics"]["estimated_sto3g_basis_functions"])
        self.assertIn("Xe", result["reasons"][0])

    def test_malformed_geometry_is_not_reported_as_resource_skip(self):
        result = assess_geometry_resources("C bad 0 0")
        self.assertEqual(result["status"], "invalid_input")

    def test_invalid_smiles_is_not_reported_as_resource_skip(self):
        result = assess_smiles_resources("not a smiles")
        self.assertEqual(result["status"], "invalid_input")

    def test_analysis_preflight_skips_before_3d_embedding(self):
        from quantum.chemistry.quantum_analysis import analyze_smiles

        with patch.dict("os.environ", {"CUREGENIX_QUANTUM_MAX_HEAVY_ATOMS": "1"}), \
             patch("quantum.chemistry.quantum_analysis.smiles_to_geometry") as embed:
            result = analyze_smiles("CC")
        self.assertEqual(result["status"], "skipped_resource_limit")
        embed.assert_not_called()

    def test_eligible_small_molecule_continues_existing_wsl_workflow(self):
        from quantum.chemistry.quantum_analysis import analyze_smiles

        expected = {"status": "success", "method": "VQE", "vqe": {"electronic_energy_hartree": -1.0}}
        with patch.dict("os.environ", {"CUREGENIX_QUANTUM_BACKEND": "wsl"}), \
             patch("quantum.chemistry.quantum_analysis.smiles_to_geometry", return_value="O 0 0 0" ) as embed, \
             patch("backend.services.wsl_quantum_adapter.wsl_quantum_adapter.analyze_geometry", return_value=expected) as worker:
            result = analyze_smiles("O", basis="sto3g", maxiter=50)
        self.assertIs(result, expected)
        embed.assert_called_once_with("O")
        worker.assert_called_once_with(atom="O 0 0 0", basis="sto3g", charge=0, spin=0, maxiter=50, benchmark=False)


if __name__ == "__main__":
    unittest.main()
