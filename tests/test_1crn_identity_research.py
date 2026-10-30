"""Regression coverage for the 1CRN target identity and evidence safeguards."""

import unittest
from pathlib import Path

from backend.agents.molecule_agent import MoleculeAgent
from backend.agents.research_agent import ResearchAgent
from backend.services.target_identity import parse_pdb_identity, resolve_target_identity
from backend.services.target_sequence import extract_pdb_chain_sequence, validate_chain_sequence


class Memory:
    def __init__(self, values):
        self.values = values

    def call_tool(self, tool, **kwargs):
        if tool == "retrieve":
            return {"data": {"value": self.values.get(kwargs["key"])} }
        if tool == "store":
            self.values[kwargs["key"]] = kwargs["value"]
        return {"data": {"ok": True}}


class Web:
    def __init__(self, binder_result=None):
        self.calls = []
        self.binder_result = binder_result or {"found": True, "title": "Nicotinic acetylcholine receptor", "summary": "Receptor pharmacology."}

    def call_tool(self, tool, **kwargs):
        self.calls.append((tool, kwargs))
        if tool == "uniprot_fetch_by_accession":
            return {"data": {"found": True}}
        if tool == "verify_alphafold":
            return {"data": {"url": "https://alphafold.ebi.ac.uk/entry/P01542"}}
        if tool == "search_binders":
            return {"data": self.binder_result}
        return {"data": {}}


class CrambinIdentityEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture = Path(__file__).resolve().parents[1] / "1crn.pdb"
        cls.lines = fixture.read_text(encoding="utf-8", errors="replace").splitlines()
        cls.structure = parse_pdb_identity(cls.lines)
        cls.chain = extract_pdb_chain_sequence(cls.lines, "A")
        cls.sequence_result = validate_chain_sequence(
            cls.chain,
            "TTCCPSIVARSNFNVCRLPGTPEALCATYTGCIIIPGATCPGDYAN",
        )

    def test_1crn_dbref_chain_and_short_variant_are_retained(self):
        self.assertIn("P01542", self.structure["chain_accessions"]["A"])
        dbref = next(record for record in self.structure["dbref_records"] if record["chain_id"] == "A")
        self.assertTrue(dbref["valid"])
        self.assertEqual((dbref["pdb_sequence_begin"], dbref["pdb_sequence_end"]), ("1", "46"))
        seqres_lines = [line for line in self.lines if line.startswith("SEQRES") and line[11] == "A"]
        self.assertEqual(len(seqres_lines), 4)
        self.assertTrue(all(int(line[13:17]) == 46 for line in seqres_lines))
        atom_chains = {line[21] for line in self.lines if line.startswith("ATOM  ")}
        self.assertEqual(atom_chains, {"A"})
        self.assertEqual(self.chain["chain_id"], "A")
        result = self.sequence_result
        self.assertEqual(result["identity_state"], "insufficient_sequence_evidence")
        self.assertEqual(result["thresholds"]["minimum_aligned_residues"], 100)
        self.assertEqual(result["aligned_observed_residue_count"], 46)
        self.assertAlmostEqual(result["identity_fraction"], 45 / 46)
        self.assertEqual(result["substitutions"][0]["reference_position"], 25)
        self.assertEqual(result["substitutions"][0]["observed_amino_acid"], "I")
        self.assertEqual(result["substitutions"][0]["reference_amino_acid"], "L")
        self.assertEqual(result["observed_terminal_residue_ids"], {"first": "1", "last": "46"})
        self.assertEqual(self.chain["numbering_gaps"], [])

    def test_dbref_resolution_is_not_mislabeled_as_user_selected_accession(self):
        identity = resolve_target_identity(
            structure_evidence=self.structure,
            selected_chain_id="A",
            selected_uniprot_id=None,
            lookup_result={
                "found": True,
                "status": "verified",
                "uniprot_id": "P01542",
                "sequence": "TTCCPSIVARSNFNVCRLPGTPEALCATYTGCIIIPGATCPGDYAN",
            },
        )
        self.assertEqual(identity["identity_state"], "structure_linked")
        self.assertEqual(identity["uniprot_id"], "P01542")
        self.assertIsNone(identity["selected_uniprot_id"])

    def test_1crn_short_chain_remains_unresolved_and_generation_stays_empty(self):
        memory = Memory({"protein_info": {"protein_name": "Crambin", "target_identity": {
            "uniprot_id": "P01542", "identity_state": self.sequence_result["identity_state"],
            "candidate_generation_allowed": False,
        }}})
        result = MoleculeAgent({"memory": memory}).run({})
        self.assertEqual(result["molecules"], [])
        self.assertEqual(result["candidate_generation"]["candidate_count"], 0)
        self.assertEqual(result["candidate_generation"]["reference_compound_count"], 0)
        self.assertEqual(result["candidate_generation"]["generation_method"], "disabled: target identity is not accepted")
        self.assertIn("target identity does not have accepted sequence support", result["candidate_generation"]["warning"])

        accepted_but_unconfigured = {"uniprot_id": "P01542", "identity_state": "structure_linked_sequence_validated", "candidate_generation_allowed": True}
        supported = MoleculeAgent({"memory": Memory({"protein_info": {"target_identity": accepted_but_unconfigured}})}).run({})
        self.assertEqual(supported["molecules"], [])
        self.assertEqual(supported["candidate_generation"]["reference_compound_count"], 0)
        self.assertEqual(supported["candidate_generation"]["generation_method"], "disabled: no configured target references")
        self.assertIn("no configured target-linked reference compounds", supported["candidate_generation"]["warning"])

    def test_unaccepted_identity_prevents_binder_search_and_unsupported_biology(self):
        identity = {"uniprot_id": "P01542", "protein_name": "Crambin", "identity_state": "insufficient_sequence_evidence", "candidate_generation_allowed": False}
        memory = Memory({"protein_info": {"protein_name": "Crambin", "target_identity": identity}})
        web = Web()
        result = ResearchAgent({"memory": memory, "web": web}).run({})["research_data"]
        self.assertEqual(web.calls, [])
        self.assertEqual(result["binder_search"]["status"], "not_searched_identity_unverified")
        self.assertEqual(result["analysis_method"], "template_based_evidence_summary")
        self.assertIn("did not pass sequence validation", result["llm_analysis"])
        self.assertNotIn("cellular signaling", result["llm_analysis"].lower())
        self.assertNotIn("druggability potential", result["llm_analysis"].lower())

    def test_inconsistent_binder_search_hit_is_rejected_for_accepted_target(self):
        identity = {"uniprot_id": "P01542", "protein_name": "Crambin", "identity_state": "structure_linked_partial_sequence_support", "candidate_generation_allowed": True, "sequence_validation": {"aligned_observed_residue_count": 46}}
        memory = Memory({"protein_info": {"protein_name": "Crambin", "target_identity": identity}})
        web = Web()
        result = ResearchAgent({"memory": memory, "web": web}).run({})["research_data"]
        binder = result["binder_search"]
        self.assertEqual(binder["status"], "rejected_target_mismatch")
        self.assertFalse(binder["found"])
        self.assertEqual(binder["rejected_title"], "Nicotinic acetylcholine receptor")
        self.assertTrue(any(call[0] == "search_binders" for call in web.calls))
        self.assertIn("not assessed", result["llm_analysis"])


if __name__ == "__main__":
    unittest.main()
