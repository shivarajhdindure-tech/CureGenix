"""Milestone 6 generation gate and RCSB API tests (network mocked)."""

import json
from pathlib import Path
import unittest
from unittest.mock import patch

from backend.agents.target_agent import TargetAgent
from backend.mcp.web_mcp import WebMCPServer
from backend.services.target_generation_policy import authorize_target_generation


class TargetIdentityPolicyM6Tests(unittest.TestCase):
    def test_known_close_homolog_and_short_fragment_do_not_authorize_without_independent_evidence(self):
        for state, validation in (
            ("structure_linked_partial_sequence_support", {"validation_outcome": "passed_partial", "identity_fraction": .916, "informative_aligned_residues": 500}),
            ("structure_linked_partial_sequence_support", {"validation_outcome": "passed_partial", "identity_fraction": 1.0, "informative_aligned_residues": 150}),
        ):
            with self.subTest(validation=validation):
                result = authorize_target_generation(state, validation, selected_chain_id="A", uniprot_accession="P00533")
                self.assertFalse(result["allowed"])
                self.assertEqual(result["policy_state"], "partial_support_unverified")

    def test_documented_partial_construct_requires_chain_accession_and_entity_sequence_evidence(self):
        independent = {
            "status": "verified", "pdb_id": "1M17", "requested_pdb_id": "1M17", "auth_chain_id": "A",
            "mapping": {"database_accession": "P00533", "database_name": "UniProt", "provenance_source": "SIFTS"},
            "entity_sequence_validation": {"validation_outcome": "passed_partial", "informative_aligned_residues": 312},
        }
        result = authorize_target_generation(
            "structure_linked_partial_sequence_support",
            {"validation_outcome": "passed_partial", "identity_fraction": 1.0},
            selected_chain_id="A", uniprot_accession="P00533", independent_structure_evidence=independent,
        )
        self.assertTrue(result["allowed"])
        self.assertEqual(result["policy_state"], "independently_documented_partial_construct")

    def test_partial_mapping_conflict_wrong_chain_or_missing_construct_support_fails_closed(self):
        evidence = {
            "status": "verified", "pdb_id": "1M17", "requested_pdb_id": "1M17", "auth_chain_id": "A",
            "mapping": {"database_accession": "P00533", "database_name": "UniProt", "provenance_source": "SIFTS"},
            "entity_sequence_validation": {"validation_outcome": "passed_partial", "informative_aligned_residues": 312},
        }
        for changes in (
            {"auth_chain_id": "B"},
            {"mapping": {"database_accession": "P04626", "database_name": "UniProt", "provenance_source": "SIFTS"}},
            {"mapping": {"database_accession": "P00533", "database_name": "UniProt", "provenance_source": "Primary Data"}},
            {"entity_sequence_validation": {"validation_outcome": "sequence_mismatch", "informative_aligned_residues": 312}},
        ):
            changed = {**evidence, **changes}
            result = authorize_target_generation(
                "structure_linked_partial_sequence_support", {"validation_outcome": "passed_partial"},
                selected_chain_id="A", uniprot_accession="P00533", independent_structure_evidence=changed,
            )
            self.assertFalse(result["allowed"])

    def test_exact_full_correspondence_keeps_existing_generation_path(self):
        result = authorize_target_generation(
            "structure_linked_sequence_validated",
            {"validation_outcome": "passed_full", "identity_fraction": 1.0, "substitution_count": 0, "insertion_count": 0, "deletion_count": 0},
            selected_chain_id="A", uniprot_accession="P00533",
        )
        self.assertTrue(result["allowed"])
        self.assertEqual(result["policy_state"], "exact_sequence_correspondence")

    def test_target_agent_requires_and_propagates_independent_partial_evidence(self):
        sequence = "ACDEFGHIKLMNPQRSTVWY" * 6
        values = {
            "parsed_protein": {"protein": {"name": "protein", "sequence": sequence}, "metadata": {"pdb_header_id": "1M17"}},
            "target_selection": {"selected_chain_id": "A", "structure_identity_evidence": {
                "chain_ids": ["A"], "chain_accessions": {"A": ["P00533"]},
                "uniprot_accessions": ["P00533"], "dbref_records": [{"chain_id": "A", "accession": "P00533", "valid": True}],
                "chain_sequences": {"A": {"chain_id": "A", "sequence": sequence, "residues": [], "warnings": []}},
                "warnings": [],
            }},
        }

        class Memory:
            def call_tool(self, tool, **kwargs):
                if tool == "retrieve":
                    return {"data": {"value": values.get(kwargs["key"])}}
                if tool == "store":
                    values[kwargs["key"]] = kwargs["value"]
                    return {"data": {"ok": True}}

        class Web:
            def __init__(self, independent): self.independent = independent; self.calls = []
            def call_tool(self, tool, **kwargs):
                self.calls.append((tool, kwargs))
                if tool == "uniprot_fetch_by_accession":
                    return {"data": {"found": True, "status": "verified", "uniprot_id": "P00533", "sequence": sequence + "A" * 100, "name": "EGFR"}}
                if tool == "rcsb_verify_chain_accession":
                    return {"data": self.independent}
                return {"data": {}}

        evidence = {"status": "verified", "verified": True, "pdb_id": "1M17", "auth_chain_id": "A",
                    "mapping": {"database_accession": "P00533", "database_name": "UniProt", "provenance_source": "SIFTS"},
                    "entity_sequence": sequence + "A" * 100}
        web = Web(evidence)
        identity = TargetAgent({"memory": Memory(), "web": web}).run({})["target_identity"]
        self.assertTrue(identity["candidate_generation_allowed"])
        self.assertEqual(identity["generation_authorization"]["policy_state"], "independently_documented_partial_construct")
        self.assertEqual(identity["independent_structure_evidence"]["pdb_id"], "1M17")
        self.assertTrue(any(name == "rcsb_verify_chain_accession" for name, _ in web.calls))

        values["parsed_protein"]["metadata"].pop("pdb_header_id")
        web = Web(evidence)
        identity = TargetAgent({"memory": Memory(), "web": web}).run({})["target_identity"]
        self.assertFalse(identity["candidate_generation_allowed"])
        self.assertEqual(identity["independent_structure_evidence"]["status"], "missing_pdb_header_id")
        self.assertTrue(identity["warnings"])


class M6ArtifactIntegrityTests(unittest.TestCase):
    def test_saved_real_evaluation_has_source_labeled_cases_and_no_mislabeled_acceptance(self):
        root = Path(__file__).resolve().parents[1]
        report = json.loads((root / "docs/target_identity_policy_m6/milestone6_results.json").read_text(encoding="utf-8"))
        self.assertEqual(report["synthetic"]["case_count"], 19)
        self.assertEqual(report["diagnostics"][0]["case_id"], "real_1crn_chain_a_p01542")
        self.assertEqual(report["real_world"]["false_acceptances"], [])
        self.assertEqual(report["real_world"]["false_rejections"], [])
        cases = report["real_world"]["cases"]
        self.assertEqual(len(cases), 4)
        self.assertTrue(all(case["source_urls"] and case["observed_dbref_records"] for case in cases))
        control = next(case for case in cases if case["pdb"] == "3PP0" and case["accession"] == "P00533")
        self.assertFalse(control["actual_generation_allowed"])


class RCSBAdapterM6Tests(unittest.TestCase):
    @staticmethod
    def response(payload):
        class Response:
            status = 200
            def read(self):
                return json.dumps(payload).encode()
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
        return Response()

    def test_rcsb_sifts_chain_mapping_is_verified_from_two_api_records(self):
        instance = {"rcsb_polymer_entity_instance_container_identifiers": {"auth_asym_id": "A", "entity_id": "1", "asym_id": "A"}}
        entity = {
            "entity_poly": {"pdbx_seq_one_letter_code_can": "ACDE"},
            "rcsb_polymer_entity_container_identifiers": {"reference_sequence_identifiers": [
                {"database_accession": "P00533", "database_name": "UniProt", "provenance_source": "SIFTS"}
            ]},
        }
        with patch("backend.mcp.web_mcp.urllib.request.urlopen", side_effect=[self.response(instance), self.response(entity)]):
            result = WebMCPServer()._rcsb_verify_chain_accession("1M17", "A", "P00533")
        self.assertTrue(result["verified"])
        self.assertEqual(result["mapping"]["database_accession"], "P00533")
        self.assertEqual(result["entity_sequence"], "ACDE")

    def test_rcsb_conflicting_accession_and_network_failure_fail_closed(self):
        instance = {"rcsb_polymer_entity_instance_container_identifiers": {"auth_asym_id": "A", "entity_id": "1"}}
        conflict = {
            "entity_poly": {"pdbx_seq_one_letter_code_can": "ACDE"},
            "rcsb_polymer_entity_container_identifiers": {"reference_sequence_identifiers": [
                {"database_accession": "P04626", "database_name": "UniProt", "provenance_source": "SIFTS"}
            ]},
        }
        with patch("backend.mcp.web_mcp.urllib.request.urlopen", side_effect=[self.response(instance), self.response(conflict)]):
            result = WebMCPServer()._rcsb_verify_chain_accession("1M17", "A", "P00533")
        self.assertFalse(result["verified"])
        self.assertEqual(result["status"], "accession_mapping_mismatch")
        with patch("backend.mcp.web_mcp.urllib.request.urlopen", side_effect=TimeoutError("mock timeout")):
            timed_out = WebMCPServer()._rcsb_verify_chain_accession("1M17", "A", "P00533")
        self.assertFalse(timed_out["verified"])
        self.assertEqual(timed_out["status"], "timeout")

    def test_saved_official_rcsb_payload_shapes_are_accepted_offline(self):
        root = Path(__file__).resolve().parents[1] / "docs" / "target_identity_policy_m6" / "real_pdb"
        examples = [
            ("1M17_A_instance.json", "1M17_entity_1.json", "1M17", "A", "P00533"),
            ("3PP0_B_instance.json", "3PP0_entity_1.json", "3PP0", "B", "P04626"),
        ]
        for instance_name, entity_name, pdb_id, chain, accession in examples:
            with self.subTest(pdb_id=pdb_id, chain=chain):
                instance = json.loads((root / instance_name).read_text(encoding="utf-8"))
                entity = json.loads((root / entity_name).read_text(encoding="utf-8"))
                with patch("backend.mcp.web_mcp.urllib.request.urlopen", side_effect=[self.response(instance), self.response(entity)]):
                    result = WebMCPServer()._rcsb_verify_chain_accession(pdb_id, chain, accession)
                self.assertTrue(result["verified"])
                self.assertEqual(result["mapping"]["database_accession"], accession)


if __name__ == "__main__":
    unittest.main()
