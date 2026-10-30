"""Tests for verified Lysozyme C (P00698) target support and fail-closed behavior."""

import unittest
from backend.services.target_aware_generation import (
    SUPPORTED_TARGETS,
    get_target_references,
)
from backend.agents.molecule_agent import MoleculeAgent
from backend.mcp.molecule_mcp import MoleculeMCPServer


class Memory:
    def __init__(self, values):
        self.values = values

    def call_tool(self, tool, **kwargs):
        if tool == "retrieve":
            return {"data": {"value": self.values.get(kwargs["key"])}}
        if tool == "store":
            self.values[kwargs["key"]] = kwargs["value"]
            return {"data": {"ok": True}}
        return {"data": {}}


class LysozymeTargetTests(unittest.TestCase):
    def test_p00698_target_configuration_is_present_and_has_verified_metadata(self):
        self.assertIn("P00698", SUPPORTED_TARGETS)
        lysozyme = SUPPORTED_TARGETS["P00698"]
        self.assertEqual(lysozyme["target_name"], "Lysozyme C")
        self.assertEqual(lysozyme["organism"], "Gallus gallus")
        self.assertEqual(len(lysozyme["references"]), 1)
        ref = lysozyme["references"][0]
        self.assertEqual(ref["name"], "N-acetyl-D-glucosamine")
        self.assertEqual(ref["chembl_id"], "CHEMBL447878")
        self.assertEqual(ref["scaffold_name"], "2-acetamido-2-deoxy-D-glucopyranose")
        self.assertTrue(any("P00698" in s["url"] for s in ref["sources"]))
        self.assertTrue(any("CHEMBL1932892" in s["url"] for s in ref["sources"]))
        self.assertTrue(any("CHEMBL447878" in s["url"] for s in ref["sources"]))
        self.assertTrue(any("28009" in s["url"] for s in ref["sources"]))

    def test_p00698_reference_lookup_succeeds_only_with_accepted_sequence_support(self):
        valid_identity = {
            "uniprot_id": "P00698",
            "identity_state": "structure_linked_partial_sequence_support",
            "candidate_generation_allowed": True,
            "protein_name": "Lysozyme C",
            "selected_chain_id": "A",
        }
        refs, warning = get_target_references(valid_identity)
        self.assertEqual(len(refs), 1)
        self.assertEqual(refs[0]["chembl_id"], "CHEMBL447878")
        self.assertIsNone(warning)

        # Fail-closed when candidate_generation_allowed is False
        unauthorized = dict(valid_identity, candidate_generation_allowed=False)
        refs_unauth, warning_unauth = get_target_references(unauthorized)
        self.assertEqual(refs_unauth, [])
        self.assertIn("does not have accepted sequence support", warning_unauth)

    def test_molecule_mcp_generates_chemically_valid_analogs_from_nag(self):
        server = MoleculeMCPServer()
        nag_smiles = SUPPORTED_TARGETS["P00698"]["references"][0]["smiles"]
        result = server._generate_analogs(nag_smiles, parent_name="N-acetyl-D-glucosamine", count=2)
        self.assertEqual(result["analogs_generated"], 2)
        analogs = result["analogs"]
        self.assertEqual(len(analogs), 2)
        self.assertTrue(any("N-propionyl" in a["modification"] for a in analogs))
        self.assertTrue(any("N-glycolyl" in a["modification"] for a in analogs))

    def test_molecule_agent_generates_candidates_for_p00698_with_provenance(self):
        identity = {
            "uniprot_id": "P00698",
            "identity_state": "structure_linked_partial_sequence_support",
            "candidate_generation_allowed": True,
            "protein_name": "Lysozyme C",
            "selected_chain_id": "A",
        }
        memory = Memory({"protein_info": {"protein_name": "Lysozyme C", "target_identity": identity}})
        agent = MoleculeAgent({"memory": memory, "molecule": MoleculeMCPServer()})
        res = agent.run({})
        self.assertEqual(len(res["molecules"]), 2)
        self.assertEqual(res["candidate_generation"]["candidate_count"], 2)
        self.assertEqual(res["candidate_generation"]["reference_compound_count"], 1)
        for m in res["molecules"]:
            self.assertEqual(m["candidate_metadata"]["target"]["uniprot_id"], "P00698")
            self.assertEqual(m["candidate_metadata"]["scaffold_provenance"]["reference_compound"], "N-acetyl-D-glucosamine")
            self.assertEqual(m["candidate_metadata"]["scaffold_provenance"]["reference_chembl_id"], "CHEMBL447878")

    def test_p00533_egfr_support_is_completely_preserved(self):
        egfr_identity = {
            "uniprot_id": "P00533",
            "identity_state": "structure_linked_sequence_validated",
            "candidate_generation_allowed": True,
            "protein_name": "EGFR",
            "selected_chain_id": "A",
        }
        refs, warning = get_target_references(egfr_identity)
        self.assertEqual(len(refs), 1)
        self.assertEqual(refs[0]["chembl_id"], "CHEMBL553")
        self.assertEqual(refs[0]["name"], "Erlotinib")
        self.assertIsNone(warning)
