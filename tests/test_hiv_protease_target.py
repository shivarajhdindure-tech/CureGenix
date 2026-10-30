"""Tests for verified HIV-1 Protease (P03367) target support and fail-closed behavior."""

import unittest
from rdkit import Chem
from backend.services.target_aware_generation import (
    SUPPORTED_TARGETS,
    get_target_references,
)
from backend.services.target_generation_policy import authorize_target_generation
from backend.agents.molecule_agent import MoleculeAgent
from backend.mcp.molecule_mcp import MoleculeMCPServer


class Memory:
    def __init__(self, values):
        self.values = dict(values)

    def call_tool(self, tool, **kwargs):
        if tool == "retrieve":
            return {"data": {"value": self.values.get(kwargs["key"])}}
        if tool == "store":
            self.values[kwargs["key"]] = kwargs["value"]
            return {"data": {"ok": True}}
        return {"data": {}}


class HIVProteaseTargetTests(unittest.TestCase):
    def test_p03367_target_configuration_is_present_and_has_verified_metadata(self):
        self.assertIn("P03367", SUPPORTED_TARGETS)
        hiv_target = SUPPORTED_TARGETS["P03367"]
        self.assertIn("HIV-1 retropepsin", hiv_target["target_name"])
        self.assertEqual(hiv_target["organism"], "Human immunodeficiency virus type 1")
        self.assertEqual(len(hiv_target["references"]), 1)
        ref = hiv_target["references"][0]
        self.assertEqual(ref["name"], "Indinavir")
        self.assertEqual(ref["chembl_id"], "CHEMBL115")
        self.assertIn("hydroxyethylamine", ref["scaffold_name"])
        self.assertTrue(any("P03367" in s["url"] for s in ref["sources"]))
        self.assertTrue(any("CHEMBL243" in s["url"] for s in ref["sources"]))
        self.assertTrue(any("CHEMBL115" in s["url"] for s in ref["sources"]))
        self.assertTrue(any("1HSG" in s["url"] for s in ref["sources"]))

    def test_p03367_reference_lookup_succeeds_only_with_accepted_sequence_support(self):
        valid_identity = {
            "uniprot_id": "P03367",
            "identity_state": "structure_linked_partial_sequence_support",
            "candidate_generation_allowed": True,
            "protein_name": "Gag-Pol polyprotein / HIV-1 retropepsin (Protease)",
            "selected_chain_id": "A",
        }
        refs, warning = get_target_references(valid_identity)
        self.assertEqual(len(refs), 1)
        self.assertEqual(refs[0]["chembl_id"], "CHEMBL115")
        self.assertEqual(refs[0]["name"], "Indinavir")
        self.assertIsNone(warning)

        # Fail-closed when candidate_generation_allowed is False
        unauthorized = dict(valid_identity, candidate_generation_allowed=False)
        refs_unauth, warning_unauth = get_target_references(unauthorized)
        self.assertEqual(refs_unauth, [])
        self.assertIn("does not have accepted sequence support", warning_unauth)

    def test_molecule_mcp_generates_chemically_valid_analogs_from_indinavir(self):
        server = MoleculeMCPServer()
        indinavir_smiles = SUPPORTED_TARGETS["P03367"]["references"][0]["smiles"]
        result = server._generate_analogs(indinavir_smiles, parent_name="Indinavir", count=2)
        self.assertEqual(result["analogs_generated"], 2)
        analogs = result["analogs"]
        self.assertEqual(len(analogs), 2)
        self.assertTrue(any("isopropylamide" in a["modification"] for a in analogs))
        self.assertTrue(any("benzyl bioisostere" in a["modification"] for a in analogs))
        for a in analogs:
            mol = Chem.MolFromSmiles(a["smiles"])
            self.assertIsNotNone(mol)
            self.assertGreater(mol.GetNumAtoms(), 20)

    def test_molecule_agent_generates_candidates_for_p03367_with_provenance(self):
        identity = {
            "uniprot_id": "P03367",
            "identity_state": "structure_linked_partial_sequence_support",
            "candidate_generation_allowed": True,
            "protein_name": "Gag-Pol polyprotein / HIV-1 retropepsin (Protease)",
            "selected_chain_id": "A",
        }
        memory = Memory({
            "protein_info": {
                "protein_name": "Gag-Pol polyprotein / HIV-1 retropepsin (Protease)",
                "target_identity": identity,
            }
        })
        agent = MoleculeAgent({"memory": memory, "molecule": MoleculeMCPServer()})
        res = agent.run({})
        self.assertEqual(len(res["molecules"]), 2)
        self.assertEqual(res["candidate_generation"]["candidate_count"], 2)
        self.assertEqual(res["candidate_generation"]["reference_compound_count"], 1)
        for m in res["molecules"]:
            self.assertEqual(m["candidate_metadata"]["target"]["uniprot_id"], "P03367")
            self.assertEqual(
                m["candidate_metadata"]["scaffold_provenance"]["reference_compound"], "Indinavir"
            )
            self.assertEqual(
                m["candidate_metadata"]["scaffold_provenance"]["reference_chembl_id"], "CHEMBL115"
            )
            self.assertIn(
                "target-informed hypothesis",
                m["candidate_metadata"]["generation_method"]["scope"],
            )

    def test_target_generation_policy_authorizes_sifts_verified_mature_construct(self):
        # 99 residues SIFTS-verified construct (like 1HSG HIV-1 protease monomer)
        independent_sifts = {
            "status": "verified",
            "pdb_id": "1HSG",
            "requested_pdb_id": "1HSG",
            "auth_chain_id": "A",
            "mapping": {
                "database_accession": "P03367",
                "database_name": "UniProt",
                "provenance_source": "SIFTS",
            },
            "entity_sequence_validation": {
                "validation_outcome": "passed_full",
                "informative_aligned_residues": 99,
                "substitution_count": 0,
            },
        }
        policy_res = authorize_target_generation(
            "structure_linked_partial_sequence_support",
            sequence_validation={"validation_outcome": "passed_partial"},
            selected_chain_id="A",
            uniprot_accession="P03367",
            independent_structure_evidence=independent_sifts,
        )
        self.assertTrue(policy_res["allowed"])
        self.assertEqual(policy_res["policy_state"], "independently_documented_partial_construct")

        # Rejection when SIFTS mapping is missing or unverified
        unverified_sifts = dict(independent_sifts, status="tool_error")
        policy_fail = authorize_target_generation(
            "structure_linked_partial_sequence_support",
            sequence_validation={"validation_outcome": "passed_partial"},
            selected_chain_id="A",
            uniprot_accession="P03367",
            independent_structure_evidence=unverified_sifts,
        )
        self.assertFalse(policy_fail["allowed"])
        self.assertEqual(policy_fail["policy_state"], "partial_support_unverified")

    def test_1crn_crambin_rejection_retained(self):
        crambin_identity = {
            "uniprot_id": "P01542",
            "identity_state": "insufficient_sequence_evidence",
            "candidate_generation_allowed": False,
            "protein_name": "Crambin",
            "selected_chain_id": "A",
        }
        refs, warning = get_target_references(crambin_identity)
        self.assertEqual(refs, [])
        self.assertIsNotNone(warning)
        memory = Memory({
            "protein_info": {
                "protein_name": "Crambin",
                "target_identity": crambin_identity,
            }
        })
        agent = MoleculeAgent({"memory": memory, "molecule": MoleculeMCPServer()})
        res = agent.run({})
        self.assertEqual(len(res["molecules"]), 0)
        self.assertEqual(res["candidate_generation"]["candidate_count"], 0)
        self.assertIn("disabled", res["candidate_generation"]["generation_method"])

    def test_unconfigured_target_fails_closed(self):
        # A valid target with accepted sequence support, but no references configured in CureGenix
        unconfigured_identity = {
            "uniprot_id": "P99999",
            "identity_state": "structure_linked_sequence_validated",
            "candidate_generation_allowed": True,
            "protein_name": "Unconfigured Kinase",
            "selected_chain_id": "A",
        }
        refs, warning = get_target_references(unconfigured_identity)
        self.assertEqual(refs, [])
        self.assertIn("no configured target-linked reference compounds", warning)

    def test_existing_egfr_and_lysozyme_support_completely_preserved(self):
        egfr = {"uniprot_id": "P00533", "identity_state": "structure_linked_sequence_validated", "candidate_generation_allowed": True}
        refs_egfr, warn_egfr = get_target_references(egfr)
        self.assertEqual(len(refs_egfr), 1)
        self.assertEqual(refs_egfr[0]["name"], "Erlotinib")
        self.assertIsNone(warn_egfr)

        lyz = {"uniprot_id": "P00698", "identity_state": "structure_linked_partial_sequence_support", "candidate_generation_allowed": True}
        refs_lyz, warn_lyz = get_target_references(lyz)
        self.assertEqual(len(refs_lyz), 1)
        self.assertEqual(refs_lyz[0]["name"], "N-acetyl-D-glucosamine")
        self.assertIsNone(warn_lyz)


if __name__ == "__main__":
    unittest.main()
