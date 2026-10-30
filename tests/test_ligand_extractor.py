"""Tests for PDB ligand extraction, CCD validation, and EGFR collection labeling."""

from pathlib import Path
import unittest

from backend.services.ligand_extractor import (
    extract_pdb_ligands,
    get_curated_pdb_ligands,
    VALIDATED_CHEMICAL_COMPONENT_DICTIONARY,
)
from backend.services.structure_registry import (
    get_curated_collection_metadata,
    load_structure_manifest,
)
from backend.services.structure_analysis import analyze_pdb_file
from backend.services.structure_api import router
from fastapi.testclient import TestClient
from fastapi import FastAPI


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class LigandExtractorTests(unittest.TestCase):
    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(router)
        self.client = TestClient(self.app)

    def test_egfr_collection_metadata_is_explicitly_labeled(self):
        """Requirement 1: Curated collection is explicitly labeled as EGFR-focused."""
        meta = get_curated_collection_metadata()
        self.assertIn("EGFR-Focused", meta["collection_name"])
        self.assertEqual(meta["target_accession"], "P00533")
        self.assertIn("EGFR", meta["target_name"])
        self.assertIn("do not represent four independent protein targets", meta["collection_description"])

        manifest = load_structure_manifest()
        self.assertEqual(manifest["collection_id"], "egfr_focused_curated_v1")
        for struct in manifest["structures"]:
            self.assertEqual(struct["target_accession"], "P00533")
            self.assertIn("EGFR", struct["target_name"])

    def test_1m17_extracts_and_validates_erlotinib_aq4(self):
        """1M17: Extracts Erlotinib (AQ4) and excludes water solvent."""
        ligands = extract_pdb_ligands(PROJECT_ROOT / "data" / "structures" / "egfr" / "1M17.pdb")
        drugs = [l for l in ligands if l["is_drug_candidate"]]
        solvents = [l for l in ligands if not l["is_drug_candidate"]]

        self.assertEqual(len(drugs), 1)
        aq4 = drugs[0]
        self.assertEqual(aq4["component_id"], "AQ4")
        self.assertEqual(aq4["chain_id"], "A")
        self.assertEqual(aq4["residue_number"], "999")
        self.assertEqual(aq4["name"], "Erlotinib")
        self.assertEqual(aq4["heavy_atom_count"], 29)
        self.assertEqual(aq4["formula"], "C22H23N3O4")
        self.assertEqual(aq4["verification_status"], "verified_ccd")
        self.assertIsNotNone(aq4["smiles"])
        self.assertTrue(aq4["has_conect_records"])

        # Requirement 3: Honest resource preflight (29 heavy atoms > 20 limit)
        preflight = aq4["resource_preflight"]
        self.assertEqual(preflight["status"], "skipped_resource_limit")
        self.assertTrue(any("29 exceeds configured limit 20" in r for r in preflight["reasons"]))
        self.assertTrue(any("Estimated STO-3G basis-function" in r for r in preflight["reasons"]))

        # Waters are marked as solvent_or_additive
        self.assertGreater(len(solvents), 0)
        self.assertTrue(all(s["category"] == "solvent_or_additive" for s in solvents))

    def test_2itx_extracts_and_validates_amp_pnp_anp(self):
        """2ITX: Extracts AMP-PNP (ANP) and validates CCD data."""
        ligands = extract_pdb_ligands(PROJECT_ROOT / "data" / "structures" / "egfr" / "2ITX.pdb")
        drugs = [l for l in ligands if l["is_drug_candidate"]]

        self.assertEqual(len(drugs), 1)
        anp = drugs[0]
        self.assertEqual(anp["component_id"], "ANP")
        self.assertEqual(anp["chain_id"], "A")
        self.assertEqual(anp["residue_number"], "2020")
        self.assertEqual(anp["heavy_atom_count"], 31)
        self.assertEqual(anp["formula"], "C10H17N6O12P3")
        self.assertEqual(anp["verification_status"], "verified_ccd")

        # Preflight: 31 heavy atoms > 20 limit
        preflight = anp["resource_preflight"]
        self.assertEqual(preflight["status"], "skipped_resource_limit")
        self.assertTrue(any("31 exceeds configured limit 20" in r for r in preflight["reasons"]))

    def test_4g5j_extracts_afatinib_derivatives_0wm_and_0wn(self):
        """4G5J: Extracts Afatinib components 0WN and 0WM."""
        ligands = extract_pdb_ligands(PROJECT_ROOT / "data" / "structures" / "egfr" / "4G5J.pdb")
        drugs = [l for l in ligands if l["is_drug_candidate"]]

        self.assertEqual(len(drugs), 3)
        components = {d["component_id"] for d in drugs}
        self.assertEqual(components, {"0WN", "0WM"})

        for d in drugs:
            self.assertEqual(d["heavy_atom_count"], 34)
            self.assertEqual(d["verification_status"], "verified_ccd")
            self.assertEqual(d["resource_preflight"]["status"], "skipped_resource_limit")
            self.assertTrue(any("34 exceeds configured limit 20" in r for r in d["resource_preflight"]["reasons"]))

    def test_7a2a_extracts_spebrutinib_and_eai001_and_excludes_salts(self):
        """7A2A: Extracts 57N and 7G9 across both chains A & B, excludes SO4 and CL."""
        ligands = extract_pdb_ligands(PROJECT_ROOT / "data" / "structures" / "egfr" / "7A2A.pdb")
        drugs = [l for l in ligands if l["is_drug_candidate"]]
        solvents = [l for l in ligands if not l["is_drug_candidate"]]

        # 2 copies of 57N (chains A, B) + 2 copies of 7G9 (chains A, B)
        self.assertEqual(len(drugs), 4)
        drug_res = {(d["component_id"], d["chain_id"]) for d in drugs}
        self.assertEqual(drug_res, {("57N", "A"), ("57N", "B"), ("7G9", "A"), ("7G9", "B")})

        for d in drugs:
            self.assertEqual(d["verification_status"], "verified_ccd")
            self.assertEqual(d["resource_preflight"]["status"], "skipped_resource_limit")

        # SO4 and CL must be classified as solvent/additive
        solvent_comps = {s["component_id"] for s in solvents}
        self.assertIn("SO4", solvent_comps)
        self.assertIn("CL", solvent_comps)
        self.assertIn("HOH", solvent_comps)

    def test_chain_filtering_identifies_chain_match(self):
        """Selected chain matching is recorded accurately."""
        chain_a_ligands = extract_pdb_ligands(
            PROJECT_ROOT / "data" / "structures" / "egfr" / "7A2A.pdb",
            selected_chain_id="A",
        )
        for lig in chain_a_ligands:
            if lig["chain_id"] == "A":
                self.assertTrue(lig["is_chain_matched"])
            else:
                self.assertFalse(lig["is_chain_matched"])

    def test_unverified_custom_hetatm_withholds_smiles(self):
        """Requirement 2: Uncurated/unknown HETATM records withhold SMILES fail-closed."""
        fake_pdb_lines = [
            "ATOM      1  N   ALA A   1      11.104  13.207  10.000  1.00 10.00           N  ",
            "ATOM      2  CA  ALA A   1      12.000  14.000  10.000  1.00 10.00           C  ",
            "HETATM   10  C1  UNK A 500      20.000  20.000  20.000  1.00 20.00           C  ",
            "HETATM   11  C2  UNK A 500      21.000  20.000  20.000  1.00 20.00           C  ",
            "HETATM   12  N1  UNK A 500      22.000  20.000  20.000  1.00 20.00           N  ",
            "CONECT   10   11",
            "CONECT   11   10   12",
            "CONECT   12   11",
            "END",
        ]
        ligands = extract_pdb_ligands(fake_pdb_lines)
        drugs = [l for l in ligands if l["is_drug_candidate"]]
        self.assertEqual(len(drugs), 1)
        unk = drugs[0]
        self.assertEqual(unk["component_id"], "UNK")
        self.assertEqual(unk["verification_status"], "unverified_raw_pdb_coordinates")
        self.assertIsNone(unk["smiles"])  # Must not invent canonical SMILES
        self.assertEqual(unk["resource_preflight"]["status"], "unverified")
        self.assertTrue(any("canonical SMILES is withheld" in w for w in unk["verification_warnings"]))

    def test_crambin_1crn_has_no_drug_ligands(self):
        """1CRN contains only protein ATOM records; no drug ligands are reported."""
        ligands = extract_pdb_ligands(PROJECT_ROOT / "1crn.pdb")
        drugs = [l for l in ligands if l["is_drug_candidate"]]
        self.assertEqual(len(drugs), 0)

    def test_structure_analysis_and_endpoints_integrate_ligands(self):
        """Structure analysis API and HTTP endpoints return extracted ligands."""
        analysis = analyze_pdb_file(PROJECT_ROOT / "data" / "structures" / "egfr" / "1M17.pdb")
        self.assertIn("co_crystallized_ligands", analysis)
        drugs = [l for l in analysis["co_crystallized_ligands"] if l["is_drug_candidate"]]
        self.assertEqual(len(drugs), 1)
        self.assertEqual(drugs[0]["component_id"], "AQ4")

        # Test curated structure ligands endpoint
        res = self.client.get("/api/structures/curated/1M17/ligands")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["pdb_id"], "1M17")
        self.assertEqual(len(data["co_crystallized_drug_candidates"]), 1)
        self.assertEqual(data["co_crystallized_drug_candidates"][0]["component_id"], "AQ4")
        self.assertIn("collection", data)
        self.assertIn("EGFR-Focused", data["collection"]["collection_name"])


if __name__ == "__main__":
    unittest.main()
