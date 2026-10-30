"""Focused tests for fail-closed target-informed candidate generation."""

import unittest
from pathlib import Path
from unittest.mock import patch

from backend.agents.molecule_agent import MoleculeAgent
from backend.agents.decision_agent import DecisionAgent
from backend.agents.quantum_analysis_agent import QuantumAnalysisAgent
from backend.agents.screening_agent import ScreeningAgent
from backend.agents.target_agent import TargetAgent
from backend.services.target_identity import parse_pdb_identity, resolve_target_identity
from backend.services.target_sequence import (
    SequenceValidationPolicy,
    extract_pdb_chain_sequence,
    validate_chain_sequence,
)
from backend.services.target_generation_policy import authorize_target_generation
from backend.services.target_aware_generation import get_target_references


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


class Molecules:
    def __init__(self, smiles=None):
        self.smiles = smiles
        self.calls = []

    def call_tool(self, tool, **kwargs):
        self.calls.append((tool, kwargs))
        if tool == "generate_analogs":
            variants = self.smiles if self.smiles is not None else [
                "CC#Cc1cccc(Nc2ncnc3cc(OCCOC)c(OCCOC)cc23)c1",
                "COCCOc1cc2ncnc(Nc3cccc(C#N)c3)c2cc1OCCOC",
                "invalid-smiles",
                "CC#Cc1cccc(Nc2ncnc3cc(OCCOC)c(OCCOC)cc23)c1",
            ]
            return {"data": {"analogs": [
                {"id": f"GEN-{i}", "smiles": value, "modification": "test edit"}
                for i, value in enumerate(variants)
            ]}}
        if tool == "compute_molecular_properties":
            return {"data": {"molecular_weight": 200}}
        return {"data": {}}


class TargetAwareGenerationTests(unittest.TestCase):
    @staticmethod
    def pdb_dbref(chain, accession):
        line = [" "] * 80
        line[0:6] = "DBREF "
        line[7:11] = "1ABC"
        line[12] = chain
        line[14:18] = "   1"
        line[20:24] = " 100"
        line[26:32] = "UNP   "
        line[33:41] = accession.ljust(8)
        return "".join(line)

    @staticmethod
    def pdb_atom(chain):
        line = [" "] * 80
        line[0:6] = "ATOM  "
        line[21] = chain
        return "".join(line)

    @staticmethod
    def pdb_residue(chain, number, residue_name, record="ATOM  ", altloc=" ", insertion_code="", occupancy=1.0):
        line = [" "] * 80
        line[0:6] = record
        line[12:16] = " CA "
        line[16] = altloc
        line[17:20] = residue_name.ljust(3)
        line[21] = chain
        line[22:26] = str(number).rjust(4)
        line[26] = insertion_code or " "
        line[54:60] = f"{occupancy:6.2f}"
        line[76:78] = " C"
        return "".join(line)

    @staticmethod
    def verified(accession="P00533"):
        return {"uniprot_id": accession, "identity_state": "structure_linked_sequence_validated",
                "identity_status": "structure_linked_sequence_validated", "candidate_generation_allowed": True,
                "protein_name": "EGFR", "selected_chain_id": "A",
                "structure_link_status": "pdb_dbref_uniprot_sequence_validated",
                "sequence_validation": {"identity_state": "structure_linked_sequence_validated", "validation_outcome": "passed_full"}}

    def run_agent(self, identity, generated=None):
        memory = Memory({"protein_info": {
            "protein_name": identity.get("protein_name", "Test target"),
            "target_identity": identity,
        }})
        molecules = Molecules(generated)
        result = MoleculeAgent({"memory": memory, "molecule": molecules}).run({})
        return result, memory, molecules

    def test_verified_egfr_propagates_target_and_scaffold_provenance(self):
        identity = self.verified()
        result, memory, _ = self.run_agent(identity)
        self.assertEqual(len(result["molecules"]), 2)
        candidate = result["molecules"][0]
        self.assertEqual(candidate["candidate_metadata"]["target"]["uniprot_id"], "P00533")
        self.assertEqual(candidate["candidate_metadata"]["scaffold_provenance"]["reference_compound"], "Erlotinib")
        self.assertTrue(candidate["candidate_metadata"]["scaffold_provenance"]["sources"])
        self.assertEqual(candidate["candidate_metadata"]["target"]["evidence"]["sequence_validation"]["validation_outcome"], "passed_full")
        self.assertEqual(memory.values["candidate_generation_status"]["candidate_count"], 2)

    def test_different_verified_target_does_not_receive_egfr_scaffold(self):
        identity = self.verified("P56817")
        result, _, molecules = self.run_agent(identity)
        self.assertEqual(result["molecules"], [])
        self.assertFalse(any(call[0] == "generate_analogs" for call in molecules.calls))
        self.assertIn("no configured", result["candidate_generation"]["warning"])

    def test_missing_or_ambiguous_target_fails_closed(self):
        for identity in (
            {},
            {"uniprot_id": None, "identity_state": "ambiguous"},
            {"uniprot_id": "P00533", "identity_state": "externally_verified", "candidate_generation_allowed": False},
        ):
            result, _, _ = self.run_agent(identity)
            self.assertEqual(result["molecules"], [])
            self.assertIn("No target-informed", result["candidate_generation"]["warning"])

    def test_invalid_and_duplicate_smiles_are_removed(self):
        identity = self.verified()
        result, _, _ = self.run_agent(identity)
        smiles = [item["smiles"] for item in result["molecules"]]
        self.assertEqual(len(smiles), 2)
        self.assertEqual(len(set(smiles)), 2)

    def test_invalid_parent_generates_nothing(self):
        from backend.mcp.molecule_mcp import MoleculeMCPServer
        response = MoleculeMCPServer()._generate_analogs("not-a-smiles", count=2)
        self.assertEqual(response["analogs"], [])
        self.assertEqual(response["analogs_generated"], 0)

    def test_molecule_tools_do_not_fabricate_affinity_and_use_rdkit_descriptors(self):
        from backend.mcp.molecule_mcp import MoleculeMCPServer
        server = MoleculeMCPServer()
        simulation = server._simulate_structure("CCO", "EGFR")["simulation"]
        self.assertEqual(simulation["status"], "not_performed")
        self.assertNotIn("binding_prediction", simulation)
        properties = server._compute_molecular_properties("CCO")
        self.assertEqual(properties["status"], "computed")
        self.assertAlmostEqual(properties["molecular_weight"], 46.069, places=2)

    def test_metadata_survives_screening_and_lightweight_quantum(self):
        metadata = {"target": {"uniprot_id": "P00533"}}
        candidate = {"name": "X", "smiles": "CCO", "category": "novel", "candidate_metadata": metadata}
        memory = Memory({"molecules": [candidate]})
        compute = type("Compute", (), {"call_tool": lambda self, tool, **kwargs: {"data": {
            "drug_likeness_score": 0.5, "bbb_score": 0.5, "toxicity_penalty": 0.1,
            "composite_score": 0.5,
        }}})()
        scored = ScreeningAgent({"memory": memory, "compute": compute}).run({})["screening_scores"][0]
        self.assertEqual(scored["candidate_metadata"], metadata)
        quantum = QuantumAnalysisAgent({"memory": memory})
        with patch.dict("os.environ", {"CUREGENIX_QUANTUM_MODE": "light"}):
            analyzed = quantum._run_lightweight_analysis([candidate])["molecules"][0]
        self.assertEqual(analyzed["candidate_metadata"], metadata)
        self.assertEqual(analyzed["quantum_analysis"]["mode"], "lightweight")

    def test_candidate_provenance_survives_final_decision(self):
        from unittest.mock import patch
        metadata = {"target": {"uniprot_id": "P00533"}, "scaffold_provenance": {"reference_compound": "Erlotinib"}}
        values = {
            "screened_molecules": [{"drug_name": "GEN-X", "smiles": "CCO", "category": "novel",
                                   "composite_score": 0.5, "candidate_metadata": metadata}],
            "risk_flags": [], "protein_info": {"protein_name": "EGFR"},
            "research_result": {"llm_analysis": ""},
        }
        with patch("backend.agents.decision_agent.call_llm", return_value=None):
            result = DecisionAgent({"memory": Memory(values)}).run({})
        self.assertEqual(result["recommendations"][0]["candidate_metadata"], metadata)

    def test_reference_lookup_is_scoped_to_exact_verified_target(self):
        refs, warning = get_target_references(self.verified())
        self.assertEqual(refs[0]["chembl_id"], "CHEMBL553")
        self.assertIsNone(warning)
        refs, warning = get_target_references({"uniprot_id": "P00533", "identity_state": "externally_verified", "candidate_generation_allowed": False})
        self.assertEqual(refs, [])
        self.assertIsNotNone(warning)

    def test_existing_1crn_fixture_exposes_canonical_sequence_variant_and_length_floor(self):
        fixture = Path(__file__).resolve().parents[1] / "1crn.pdb"
        lines = fixture.read_text(encoding="utf-8", errors="replace").splitlines()
        evidence = parse_pdb_identity(lines)
        chain = extract_pdb_chain_sequence(lines, "A")
        reference = "TTCCPSIVARSNFNVCRLPGTPEALCATYTGCIIIPGATCPGDYAN"
        self.assertIn("P01542", evidence["uniprot_accessions"])
        self.assertEqual(chain["sequence"], "TTCCPSIVARSNFNVCRLPGTPEAICATYTGCIIIPGATCPGDYAN")
        self.assertIn("ENGINEERED: YES", "\n".join(lines))
        self.assertNotEqual(chain["sequence"], reference)
        default_result = validate_chain_sequence(chain, reference)
        self.assertEqual(default_result["identity_state"], "insufficient_sequence_evidence")
        self.assertFalse(default_result["candidate_generation_allowed"])
        self.assertAlmostEqual(default_result["identity_fraction"], 45 / 46)
        self.assertEqual(default_result["aligned_observed_residue_count"], 46)
        self.assertEqual(default_result["substitutions"][0]["reference_position"], 25)
        self.assertEqual(default_result["substitution_count"], 1)
        self.assertEqual(default_result["substitutions"][0]["observed_amino_acid"], "I")
        self.assertEqual(default_result["substitutions"][0]["reference_amino_acid"], "L")

        exact_entity = validate_chain_sequence(chain, chain["sequence"])
        independent_evidence = {
            "status": "verified", "pdb_id": "1CRN", "requested_pdb_id": "1CRN",
            "auth_chain_id": "A",
            "mapping": {"database_accession": "P01542", "database_name": "UniProt", "provenance_source": "SIFTS"},
            "entity_sequence_validation": exact_entity,
        }
        policy = authorize_target_generation(
            "structure_linked_partial_sequence_support", default_result,
            selected_chain_id="A", uniprot_accession="P01542",
        )
        self.assertFalse(policy["allowed"])
        allowed = authorize_target_generation(
            "structure_linked_partial_sequence_support", default_result,
            selected_chain_id="A", uniprot_accession="P01542",
            independent_structure_evidence=independent_evidence,
        )
        self.assertFalse(allowed["allowed"])
        self.assertEqual(allowed["policy_state"], "partial_support_unverified")

        altered_entity = dict(exact_entity, substitution_count=1)
        rejected = authorize_target_generation(
            "structure_linked_partial_sequence_support", default_result,
            selected_chain_id="A", uniprot_accession="P01542",
            independent_structure_evidence={**independent_evidence, "entity_sequence_validation": altered_entity},
        )
        self.assertFalse(rejected["allowed"])

    def test_observed_chain_extraction_altloc_insertion_gap_modified_unknown_and_blank_chain(self):
        seqres = "SEQRES   1 A    4  ALA GLY MSE XAA"
        modres = [" "] * 80
        modres[0:6] = "MODRES"
        modres[12:15] = "ZZZ"
        modres[16] = "A"
        modres[18:22] = "  15"
        modres[24:27] = "SER"
        lines = [
            seqres,
            "".join(modres),
            self.pdb_residue("A", 10, "ALA", altloc="A", occupancy=0.50),
            self.pdb_residue("A", 10, "ALA", altloc="B", occupancy=0.50),
            self.pdb_residue("A", 10, "ALA", altloc=" ", occupancy=1.00),
            self.pdb_residue("A", 10, "GLY", insertion_code="A"),
            self.pdb_residue("A", 12, "MSE", record="HETATM"),
            self.pdb_residue("A", 13, "XAA", record="HETATM"),
            self.pdb_residue("A", 15, "ZZZ", record="HETATM"),
            self.pdb_residue("A", 14, "LIG", record="HETATM"),
            self.pdb_residue(" ", 1, "CYS"),
        ]
        chain = extract_pdb_chain_sequence(lines, "A")
        self.assertEqual(chain["sequence"], "AGMXS")
        self.assertEqual(chain["observed_residue_count"], 5)
        self.assertEqual(chain["alternate_location_residue_count"], 1)
        self.assertEqual(chain["residues"][1]["pdb_residue_id"], "10A")
        self.assertEqual(chain["residues"][2]["conversion"], "recognized_modified")
        self.assertEqual(chain["residues"][4]["conversion"], "MODRES_parent")
        self.assertEqual(chain["unknown_residue_counts"], {"XAA": 1})
        self.assertEqual(chain["numbering_gaps"][0]["missing_number_count"], 1)
        blank_chain = extract_pdb_chain_sequence(lines, "_")
        self.assertEqual(blank_chain["sequence"], "C")
        self.assertIn("LIG", chain["ignored_heterogen_residue_counts"])

    def test_sequence_alignment_exact_partial_substitution_indels_and_low_coverage(self):
        reference = "ACDEFGHIKLMNPQRSTVWY"
        policy = SequenceValidationPolicy(
            min_identity_fraction=0.90, min_observed_coverage=0.80,
            min_reference_coverage=0.15, min_aligned_residues=10,
            max_gap_fraction=0.10,
        )
        def validate(sequence, reference_sequence=reference, selected_policy=policy):
            return validate_chain_sequence({"chain_id": "A", "sequence": sequence}, reference_sequence, selected_policy)

        self.assertEqual(validate(reference)["identity_state"], "structure_linked_sequence_validated")
        partial = validate(reference[3:-3])
        self.assertEqual(partial["identity_state"], "structure_linked_partial_sequence_support")
        self.assertEqual(partial["unaligned_reference_prefix"], reference[:3])
        self.assertEqual(partial["unaligned_reference_suffix"], reference[-3:])

        substitution = validate(reference[:5] + "A" + reference[6:])
        self.assertEqual(substitution["identity_state"], "structure_linked_partial_sequence_support")
        self.assertEqual(substitution["substitution_count"], 1)
        self.assertEqual(substitution["substitutions"][0]["reference_position"], 6)

        deletion = validate(reference[:10] + reference[11:])
        self.assertEqual(deletion["identity_state"], "structure_linked_partial_sequence_support")
        self.assertEqual(deletion["deletion_count"], 1)
        insertion = validate(reference[:10] + "A" + reference[10:])
        self.assertEqual(insertion["identity_state"], "structure_linked_partial_sequence_support")
        self.assertEqual(insertion["insertion_count"], 1)

        short_policy = SequenceValidationPolicy(min_aligned_residues=10, min_reference_coverage=.15)
        low_coverage = validate("ACDEFG", reference * 3, short_policy)
        self.assertEqual(low_coverage["identity_state"], "insufficient_sequence_evidence")
        self.assertFalse(low_coverage["candidate_generation_allowed"])

    def test_identity_and_coverage_threshold_boundaries_are_explicit(self):
        reference = "ACDEFGHIKL"
        base = SequenceValidationPolicy(
            min_identity_fraction=.90, min_observed_coverage=.90,
            min_reference_coverage=1.0, min_aligned_residues=10,
            max_gap_fraction=.10,
        )
        exactly_90 = validate_chain_sequence({"sequence": "ACDEFAHIKL"}, reference, base)
        self.assertEqual(exactly_90["identity_fraction"], .90)
        self.assertEqual(exactly_90["identity_state"], "structure_linked_partial_sequence_support")
        stricter_identity = SequenceValidationPolicy(
            min_identity_fraction=.9001, min_observed_coverage=.90,
            min_reference_coverage=1.0, min_aligned_residues=10,
        )
        self.assertEqual(validate_chain_sequence({"sequence": "ACDEFAHIKL"}, reference, stricter_identity)["identity_state"], "sequence_mismatch")

        inserted = validate_chain_sequence({"sequence": "ACDEFGHIKAL"}, reference, base)
        self.assertAlmostEqual(inserted["observed_chain_coverage"], 10 / 11)
        self.assertEqual(inserted["identity_state"], "structure_linked_partial_sequence_support")
        stricter_coverage = SequenceValidationPolicy(
            min_identity_fraction=.9, min_observed_coverage=10 / 11 + .0001,
            min_reference_coverage=1.0, min_aligned_residues=10,
        )
        self.assertEqual(validate_chain_sequence({"sequence": "ACDEFGHIKAL"}, reference, stricter_coverage)["identity_state"], "insufficient_sequence_evidence")

    def test_environment_policy_errors_fail_closed(self):
        with patch.dict("os.environ", {"CUREGENIX_SEQUENCE_MIN_IDENTITY": "1.5"}):
            result = validate_chain_sequence({"sequence": "A" * 100}, "A" * 100)
        self.assertEqual(result["identity_state"], "insufficient_sequence_evidence")
        self.assertFalse(result["candidate_generation_allowed"])
        self.assertTrue(any("Invalid sequence-validation configuration" in warning for warning in result["warnings"]))

    def test_target_agent_uses_exact_pdb_accession_and_propagates_identity(self):
        memory = Memory({
            "parsed_protein": {"protein": {"name": "description only", "sequence": "ACD"},
                               "metadata": {}},
            "target_selection": {"selected_chain_id": "A", "dbref_uniprot_accessions": ["P00533"],
                                 "structure_identity_evidence": {"chain_ids": ["A"],
                                     "chain_accessions": {"A": ["P00533"]},
                                     "uniprot_accessions": ["P00533"],
                                     "chain_sequences": {"A": {"chain_id": "A", "sequence": "A" * 101,
                                         "observed_residue_count": 101, "residues": [], "warnings": []}},
                                     "dbref_records": [{"chain_id": "A", "accession": "P00533", "valid": True}],
                                     "warnings": []}},
        })
        class Web:
            def __init__(self): self.requested = []
            def call_tool(self, tool, **kwargs):
                self.requested.append((tool, kwargs))
                return {"data": {"found": True, "status": "verified", "uniprot_id": "P00533", "name": "EGFR", "sequence": "A" * 101}}
        web = Web()
        result = TargetAgent({"memory": memory, "web": web}).run({})
        self.assertEqual(web.requested[0][1]["accession"], "P00533")
        self.assertEqual(result["target_identity"]["identity_state"], "structure_linked_sequence_validated")
        self.assertEqual(result["target_identity"]["sequence_validation"]["selected_chain_id"], "A")
        self.assertEqual(result["target_identity"]["sequence_validation"]["uniprot_accession"], "P00533")
        self.assertEqual(memory.values["protein_info"]["target_identity"]["uniprot_id"], "P00533")

    def test_sequence_disagreement_with_dbref_blocks_candidate_generation(self):
        evidence = {"chain_ids": ["A"], "chain_accessions": {"A": ["P00533"]},
                    "uniprot_accessions": ["P00533"], "dbref_records": [{"chain_id": "A", "accession": "P00533", "valid": True}],
                    "chain_sequences": {"A": {"chain_id": "A", "sequence": "A" * 101, "residues": [], "warnings": []}},
                    "warnings": []}
        memory = Memory({"parsed_protein": {"protein": {"name": "PDB EGFR", "sequence": "A" * 101}, "metadata": {}},
                         "target_selection": {"selected_chain_id": "A", "structure_identity_evidence": evidence}})
        class Web:
            def call_tool(self, tool, **kwargs):
                return {"data": {"found": True, "status": "verified", "uniprot_id": "P00533", "name": "EGFR", "sequence": "C" * 101}}
        resolved = TargetAgent({"memory": memory, "web": Web()}).run({})["target_identity"]
        self.assertEqual(resolved["identity_state"], "sequence_mismatch")
        self.assertFalse(resolved["candidate_generation_allowed"])
        result, _, molecules = self.run_agent(resolved)
        self.assertEqual(result["molecules"], [])
        self.assertFalse(any(call[0] == "generate_analogs" for call in molecules.calls))

    def test_external_sequence_match_remains_unlinked_and_cannot_generate(self):
        evidence = {"chain_ids": ["A"], "chain_accessions": {}, "uniprot_accessions": [],
                    "chain_sequences": {"A": {"chain_id": "A", "sequence": "A" * 101, "residues": [], "warnings": []}},
                    "warnings": ["No usable UniProt DBREF annotation was found."]}
        memory = Memory({"parsed_protein": {"protein": {"name": "PDB title", "sequence": "A" * 101}, "metadata": {}},
                         "target_selection": {"selected_chain_id": "A", "selected_uniprot_id": "P00533", "structure_identity_evidence": evidence}})
        class Web:
            def call_tool(self, tool, **kwargs):
                return {"data": {"found": True, "status": "verified", "uniprot_id": "P00533", "sequence": "A" * 101}}
        resolved = TargetAgent({"memory": memory, "web": Web()}).run({})["target_identity"]
        self.assertEqual(resolved["identity_state"], "externally_verified")
        self.assertEqual(resolved["sequence_validation"]["validation_outcome"], "passed_full")
        self.assertFalse(resolved["candidate_generation_allowed"])

    def test_single_chain_dbref_is_structure_linked_only_after_exact_lookup(self):
        evidence = parse_pdb_identity([self.pdb_atom("A"), self.pdb_dbref("A", "P00533")])
        self.assertEqual(evidence["chain_accessions"], {"A": ["P00533"]})
        resolved = resolve_target_identity(evidence, None, None, {
            "found": True, "status": "verified", "uniprot_id": "P00533",
        })
        self.assertEqual(resolved["identity_state"], "structure_linked")
        self.assertTrue(resolved["candidate_generation_allowed"])
        self.assertEqual(resolved["selected_chain_id"], "A")

    def test_multiple_chains_require_explicit_chain_selection(self):
        evidence = parse_pdb_identity([
            self.pdb_atom("A"), self.pdb_atom("B"),
            self.pdb_dbref("A", "P00533"), self.pdb_dbref("B", "P56817"),
        ])
        ambiguous = resolve_target_identity(evidence, None, None, {"status": "not_attempted", "found": False})
        self.assertEqual(ambiguous["identity_state"], "ambiguous")
        self.assertFalse(ambiguous["candidate_generation_allowed"])
        selected = resolve_target_identity(evidence, "B", None, {
            "found": True, "status": "verified", "uniprot_id": "P56817",
        })
        self.assertEqual(selected["identity_state"], "structure_linked")
        self.assertEqual(selected["selected_chain_id"], "B")

    def test_missing_and_malformed_dbref_never_unlock_generation(self):
        missing = parse_pdb_identity([self.pdb_atom("A")])
        external = resolve_target_identity(missing, None, "P00533", {
            "found": True, "status": "verified", "uniprot_id": "P00533",
        })
        self.assertEqual(external["identity_state"], "externally_verified")
        self.assertFalse(external["candidate_generation_allowed"])
        malformed = list(self.pdb_dbref("A", "P00533"))
        malformed[33:41] = "        "
        parsed = parse_pdb_identity([self.pdb_atom("A"), "".join(malformed)])
        self.assertTrue(parsed["warnings"])
        result = resolve_target_identity(parsed, "A", None, {"found": False, "status": "not_attempted"})
        self.assertEqual(result["identity_state"], "ambiguous")
        self.assertFalse(result["candidate_generation_allowed"])
        annotation_without_coordinates = parse_pdb_identity([self.pdb_dbref("A", "P00533")])
        no_chain = resolve_target_identity(annotation_without_coordinates, None, None, {
            "found": True, "status": "verified", "uniprot_id": "P00533",
        })
        self.assertEqual(no_chain["identity_state"], "unresolved")
        self.assertFalse(no_chain["candidate_generation_allowed"])

    def test_conflicting_accession_and_conflicting_chain_mappings(self):
        evidence = parse_pdb_identity([self.pdb_atom("A"), self.pdb_dbref("A", "P00533")])
        mismatch = resolve_target_identity(evidence, "A", "P56817", {
            "found": True, "status": "verified", "uniprot_id": "P56817",
        })
        self.assertEqual(mismatch["identity_state"], "identity_mismatch")
        self.assertFalse(mismatch["candidate_generation_allowed"])
        conflicting = parse_pdb_identity([
            self.pdb_atom("A"), self.pdb_dbref("A", "P00533"), self.pdb_dbref("A", "P56817"),
        ])
        ambiguous = resolve_target_identity(conflicting, "A", None, {"status": "not_attempted", "found": False})
        self.assertEqual(ambiguous["identity_state"], "ambiguous")

    def test_uniprot_lookup_failures_are_distinguished(self):
        import io
        import json
        import urllib.error
        from backend.mcp.web_mcp import WebMCPServer
        server = WebMCPServer()
        with patch("backend.mcp.web_mcp.urllib.request.urlopen", side_effect=TimeoutError("timed out")):
            self.assertEqual(server._uniprot_fetch_by_accession("P00533")["status"], "timeout")
        with patch("backend.mcp.web_mcp.urllib.request.urlopen", side_effect=urllib.error.URLError("offline")):
            self.assertEqual(server._uniprot_fetch_by_accession("P00533")["status"], "network_error")
        valid_record = {
            "primaryAccession": "P00533",
            "proteinDescription": {"recommendedName": {"fullName": {"value": "EGFR"}}},
            "organism": {"scientificName": "Homo sapiens"},
            "sequence": {"length": 1210, "value": "A" * 1210},
        }
        with patch("backend.mcp.web_mcp.urllib.request.urlopen", return_value=io.BytesIO(json.dumps(valid_record).encode())):
            verified = server._uniprot_fetch_by_accession("P00533")
            self.assertTrue(verified["found"])
            self.assertEqual(verified["name"], "EGFR")
            self.assertEqual(verified["sequence_length"], 1210)
            self.assertEqual(verified["sequence_status"], "provided")
        malformed_sequence = dict(valid_record)
        malformed_sequence["sequence"] = {"length": 4, "value": "ACD!"}
        with patch("backend.mcp.web_mcp.urllib.request.urlopen", return_value=io.BytesIO(json.dumps(malformed_sequence).encode())):
            fetched = server._uniprot_fetch_by_accession("P00533")
            self.assertTrue(fetched["found"])
            self.assertEqual(fetched["sequence_status"], "malformed_sequence")
        with patch("backend.mcp.web_mcp.urllib.request.urlopen", return_value=io.BytesIO(b"not json")):
            self.assertEqual(server._uniprot_fetch_by_accession("P00533")["status"], "malformed_response")
        with patch("backend.mcp.web_mcp.urllib.request.urlopen", return_value=io.BytesIO(b'{"proteinDescription": {}}')):
            self.assertEqual(server._uniprot_fetch_by_accession("P00533")["status"], "malformed_response")
        with patch("backend.mcp.web_mcp.urllib.request.urlopen", return_value=io.BytesIO(
            b'{"primaryAccession":"P56817","proteinDescription":{}}'
        )):
            self.assertEqual(server._uniprot_fetch_by_accession("P00533")["status"], "accession_mismatch")
        not_found = urllib.error.HTTPError("url", 404, "missing", {}, None)
        with patch("backend.mcp.web_mcp.urllib.request.urlopen", side_effect=not_found):
            self.assertEqual(server._uniprot_fetch_by_accession("P00533")["status"], "not_found")
        result = resolve_target_identity(parse_pdb_identity([self.pdb_atom("A")]), None, "P00533", {
            "found": False, "status": "timeout",
        })
        self.assertEqual(result["identity_state"], "unresolved")


class EndpointSmokeTests(unittest.TestCase):
    @staticmethod
    async def asgi_request(app, method, path, body=b"", content_type=None):
        messages = []
        first = True
        async def receive():
            nonlocal first
            if first:
                first = False
                return {"type": "http.request", "body": body, "more_body": False}
            return {"type": "http.disconnect"}
        async def send(message):
            messages.append(message)
        headers = [(b"content-length", str(len(body)).encode())]
        if content_type:
            headers.append((b"content-type", content_type.encode()))
        scope = {
            "type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1",
            "method": method, "scheme": "http", "path": path, "raw_path": path.encode(),
            "query_string": b"", "headers": headers, "server": ("test", 80),
            "client": ("test", 123),
        }
        await app(scope, receive, send)
        status = next(message["status"] for message in messages if message["type"] == "http.response.start")
        payload = b"".join(message.get("body", b"") for message in messages if message["type"] == "http.response.body")
        return status, payload

    def test_health_discovery_3d_and_benchmark_endpoint_functions(self):
        import asyncio
        import io
        import tempfile
        from unittest.mock import patch
        from starlette.datastructures import UploadFile

        from backend import main
        from backend.services.molecule_3d import MoleculeRequest, generate_3d_structure

        self.assertEqual(asyncio.run(main.health())["status"], "healthy")
        self.assertEqual(generate_3d_structure(MoleculeRequest(smiles="CCO"))["structure_status"], "generated_computational_conformer")
        from backend.services.benchmark_api import get_egfr_benchmark_data
        self.assertEqual(get_egfr_benchmark_data()["dataset"]["evaluated_compounds"], 2995)

        with tempfile.TemporaryDirectory() as directory:
            pdb = "HEADER    EGFR TEST                                  1ABC\nDBREF  1ABC A    1   100  UNP    P00533   EGFR_HUMAN      1    100\nATOM      1  CA  ALA A   1       0.000   0.000   0.000  1.00 20.00           C\n"
            upload = UploadFile(filename="input.pdb", file=io.BytesIO(pdb.encode()))
            with patch.object(main, "UPLOAD_DIR", directory), \
                 patch.object(main, "parse_pdb_file", return_value={"protein": {}, "metadata": {}}), \
                 patch.object(main.orchestrator, "run_pipeline", return_value={"status": "success"}) as run_pipeline:
                response = asyncio.run(main.discover(upload, target_uniprot_id="P00533", target_chain_id=None))
            self.assertEqual(response["status"], "success")
            metadata = run_pipeline.call_args.kwargs["protein_metadata"]
            self.assertEqual(metadata["dbref_uniprot_accessions"], ["P00533"])
            self.assertEqual(metadata["selected_uniprot_id"], "P00533")

    def test_real_asgi_health_and_discovery_requests(self):
        import asyncio
        import json
        import tempfile
        from unittest.mock import patch
        from backend import main

        status, payload = asyncio.run(self.asgi_request(main.app, "GET", "/api/health"))
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(payload)["status"], "healthy")

        pdb_line = [" "] * 80
        pdb_line[0:6] = "DBREF "
        pdb_line[7:11] = "1ABC"
        pdb_line[12] = "A"
        pdb_line[14:18] = "   1"
        pdb_line[20:24] = " 100"
        pdb_line[26:32] = "UNP   "
        pdb_line[33:41] = "P00533  "
        atom_line = [" "] * 80
        atom_line[0:6] = "ATOM  "
        atom_line[12:16] = " CA "
        atom_line[17:20] = "ALA"
        atom_line[21] = "A"
        atom_line[22:26] = "   1"
        pdb_content = "".join(pdb_line) + "\n" + "".join(atom_line) + "\n"
        boundary = "----curegenix-target-test"
        body = (
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"test.pdb\"\r\n"
            "Content-Type: chemical/x-pdb\r\n\r\n" + pdb_content + "\r\n"
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"target_uniprot_id\"\r\n\r\nP00533\r\n"
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"target_chain_id\"\r\n\r\nA\r\n"
            f"--{boundary}--\r\n"
        ).encode()
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(main, "UPLOAD_DIR", directory), \
             patch.object(main, "parse_pdb_file", return_value={"protein": {}, "metadata": {}}), \
             patch.object(main.orchestrator, "run_pipeline", return_value={"status": "ok"}) as pipeline:
            status, payload = asyncio.run(self.asgi_request(
                main.app, "POST", "/api/discover", body,
                f"multipart/form-data; boundary={boundary}",
            ))
        self.assertEqual(status, 200, payload.decode())
        posted_metadata = pipeline.call_args.kwargs["protein_metadata"]
        self.assertEqual(posted_metadata["selected_chain_id"], "A")
        self.assertEqual(posted_metadata["structure_identity_evidence"]["chain_accessions"], {"A": ["P00533"]})
        self.assertEqual(posted_metadata["structure_identity_evidence"]["chain_sequences"]["A"]["sequence"], "A")

    def test_orchestrator_preserves_identity_evidence_and_generation_warning(self):
        from backend.orchestrator import Orchestrator

        class PipelineMemory:
            def __init__(self): self.values = {}
            def init_pipeline(self, *args): self.values.clear()
            def _store(self, key, value): self.values[key] = value
            def _retrieve(self, key): return {"value": self.values.get(key)}

        class CaptureAgent:
            name = "Target Agent"
            def __init__(self, memory): self.memory = memory
            def execute(self, context):
                self.memory._store("protein_info", {"protein_name": "PDB title", "target_identity": {
                    "identity_state": "ambiguous", "warnings": ["Select a chain."],
                    "chain_accessions": {"A": ["P00533"], "B": ["P56817"]},
                }})
                self.memory._store("candidate_generation_status", {"warning": "No candidates."})
                self.memory._store("final_decisions", [])
                self.memory._store("highlights", {})
                return {"agent_name": self.name, "data": {}}

        memory = PipelineMemory()
        orchestrator = Orchestrator.__new__(Orchestrator)
        orchestrator.mcp_servers = {"memory": memory}
        orchestrator.agents = [CaptureAgent(memory)]
        orchestrator.get_mcp_stats = lambda: {}
        evidence = {"chain_ids": ["A", "B"], "chain_accessions": {"A": ["P00533"], "B": ["P56817"]}}
        result = orchestrator.run_pipeline(
            {"protein": {"name": "PDB title"}, "metadata": {}},
            {"base_name": "PDB title", "structure_identity_evidence": evidence,
             "selected_chain_id": "B", "selected_uniprot_id": "P56817"},
        )
        self.assertEqual(memory.values["target_selection"]["selected_chain_id"], "B")
        self.assertEqual(memory.values["target_selection"]["structure_identity_evidence"], evidence)
        self.assertEqual(result["protein_info"]["target_identity"]["identity_state"], "ambiguous")
        self.assertEqual(result["candidate_generation"]["warning"], "No candidates.")


if __name__ == "__main__":
    unittest.main()
