"""API and UI integration regressions for local/custom PDB analysis."""

import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from starlette.exceptions import HTTPException

from backend.main import app
from backend.services import structure_api
from backend.services.structure_api import _custom_upload_path


def _pdb_atom(record: str, serial: int, atom: str, residue: str, chain: str, residue_number: int, element: str) -> str:
    line = list(" " * 80)
    line[0:6] = record
    line[6:11] = f"{serial:5d}"
    line[12:16] = f"{atom:>4s}"[-4:]
    line[17:20] = f"{residue:>3s}"[-3:]
    line[21] = chain
    line[22:26] = f"{residue_number:4d}"
    line[30:38] = f"{0.0:8.3f}"
    line[38:46] = f"{1.0:8.3f}"
    line[46:54] = f"{2.0:8.3f}"
    line[54:60] = f"{1.0:6.2f}"
    line[60:66] = f"{20.0:6.2f}"
    line[76:78] = f"{element:>2s}"[-2:]
    return "".join(line)


def _minimal_pdb(chain_ids=("A",)) -> bytes:
    lines = ["HEADER    CUSTOM EGFR TEST                           01-JAN-25   1ABC"]
    for chain in chain_ids:
        lines.append(f"DBREF  1ABC {chain}    1   100  UNP    P00533   EGFR_HUMAN      1    100")
    for serial, chain in enumerate(chain_ids, start=1):
        lines.append(_pdb_atom("ATOM  ", serial, "CA", "ALA", chain, 1, "C"))
    lines.extend([
        _pdb_atom("HETATM", 20, "O", "HOH", chain_ids[0], 101, "O"),
        _pdb_atom("HETATM", 21, "C1", "LIG", chain_ids[0], 102, "C"),
        "END",
    ])
    return ("\n".join(lines) + "\n").encode("ascii")


class StructureAnalysisApiTests(unittest.TestCase):
    def test_curated_list_metadata_file_integrity_and_unknown_id(self):
        with TestClient(app) as client:
            listing = client.get("/api/structures/curated")
            self.assertEqual(listing.status_code, 200)
            structures = listing.json()["structures"]
            self.assertEqual({entry["pdb_id"] for entry in structures}, {"1M17", "2ITX", "4G5J", "7A2A"})
            for entry in structures:
                response = client.get(f"/api/structures/curated/{entry['pdb_id']}")
                self.assertEqual(response.status_code, 200)
                data = response.json()
                self.assertEqual(data["source"]["sha256"], entry["sha256"])
                self.assertEqual(data["source"]["kind"], "curated_local")
                self.assertEqual(data["target_identity"]["authorized_for_calculation"], False)
                file_response = client.get(data["source"]["file_url"])
                self.assertEqual(file_response.status_code, 200)
                self.assertEqual(hashlib.sha256(file_response.content).hexdigest(), entry["sha256"])
            self.assertEqual(client.get("/api/structures/curated/9ZZZ").status_code, 404)

    def test_checksum_mismatch_is_rejected(self):
        class WrongDigest:
            def hexdigest(self):
                return "0" * 64

        with TestClient(app) as client, patch("backend.services.structure_registry.hashlib.sha256", return_value=WrongDigest()):
            response = client.get("/api/structures/curated/1M17")
        self.assertEqual(response.status_code, 500)
        self.assertIn("integrity check failed", response.json()["detail"])

    def test_multichain_selection_mutations_and_nonwater_hetatm_inventory(self):
        with TestClient(app) as client:
            unresolved = client.get("/api/structures/curated/7A2A")
            self.assertEqual(unresolved.status_code, 200)
            self.assertEqual(unresolved.json()["validation"]["status"], "chain_selection_required")
            self.assertIsNone(unresolved.json()["selected_chain_id"])
            selected = client.get("/api/structures/curated/7A2A?chain_id=A").json()
        self.assertEqual(selected["selected_chain_id"], "A")
        self.assertEqual(selected["target_identity"]["accession"], "P00533")
        self.assertFalse(selected["target_identity"]["verified"])
        variants = {item["raw_record"] for item in selected["mutation_annotations"]}
        self.assertTrue(any("MET A  790" in line and "THR   790" in line for line in variants))
        self.assertTrue(any("ARG A  948" in line and "VAL   948" in line for line in variants))
        components = {item["component_id"] for item in selected["non_water_hetatm_residues"]}
        self.assertTrue({"57N", "7G9"}.issubset(components))
        self.assertNotIn("HOH", components)

    def test_custom_upload_is_unique_hashed_and_retrievable_without_discovery(self):
        from backend import main

        with tempfile.TemporaryDirectory() as directory:
            with patch.object(structure_api, "UPLOAD_STORAGE_DIR", Path(directory)), \
                 patch.object(main.orchestrator, "run_pipeline") as discovery, \
                 TestClient(app) as client:
                content = _minimal_pdb()
                first = client.post("/api/structures/uploads", files={"file": ("my-structure.pdb", content, "chemical/x-pdb")})
                second = client.post("/api/structures/uploads", files={"file": ("my-structure.pdb", content, "chemical/x-pdb")})
                self.assertEqual(first.status_code, 200, first.text)
                self.assertEqual(second.status_code, 200, second.text)
                first_data, second_data = first.json(), second.json()
                self.assertNotEqual(first_data["upload_id"], second_data["upload_id"])
                self.assertEqual(first_data["source"]["sha256"], hashlib.sha256(content).hexdigest())
                self.assertEqual(first_data["non_water_hetatm_residues"][0]["component_id"], "LIG")
                self.assertEqual(len(first_data["non_water_hetatm_residues"]), 1)
                downloaded = client.get(first_data["source"]["file_url"])
                self.assertEqual(downloaded.content, content)
                persisted = client.get(f"/api/structures/uploads/{first_data['upload_id']}?chain_id=A")
                self.assertEqual(persisted.status_code, 200)
                self.assertEqual(persisted.json()["selected_chain_id"], "A")
                discovery.assert_not_called()

    def test_custom_upload_rejects_bad_format_invalid_content_and_oversize(self):
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(structure_api, "UPLOAD_STORAGE_DIR", Path(directory)), \
             TestClient(app) as client:
            wrong_suffix = client.post("/api/structures/uploads", files={"file": ("input.cif", b"data_TEST", "chemical/x-cif")})
            malformed = client.post("/api/structures/uploads", files={"file": ("input.pdb", b"not a PDB file\n", "text/plain")})
            self.assertEqual(wrong_suffix.status_code, 415)
            self.assertEqual(malformed.status_code, 422)
            with patch.object(structure_api, "MAX_PDB_UPLOAD_BYTES", 32):
                oversized = client.post("/api/structures/uploads", files={"file": ("input.pdb", _minimal_pdb(), "chemical/x-pdb")})
            self.assertEqual(oversized.status_code, 413)
            self.assertEqual(list(Path(directory).glob("*.pdb")), [])

    def test_multi_chain_custom_upload_requires_selection_and_paths_are_not_accepted(self):
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(structure_api, "UPLOAD_STORAGE_DIR", Path(directory)), \
             TestClient(app) as client:
            uploaded = client.post("/api/structures/uploads", files={"file": ("multi.pdb", _minimal_pdb(("A", "B")), "chemical/x-pdb")})
            self.assertEqual(uploaded.status_code, 200, uploaded.text)
            self.assertEqual(uploaded.json()["validation"]["status"], "chain_selection_required")
            upload_id = uploaded.json()["upload_id"]
            self.assertEqual(client.get(f"/api/structures/uploads/{upload_id}?chain_id=B").json()["selected_chain_id"], "B")
            self.assertEqual(client.get("/api/structures/uploads/../../outside").status_code, 404)
            with self.assertRaises(HTTPException):
                _custom_upload_path("../../outside")


class StructureAnalysisFrontendIntegrationTests(unittest.TestCase):
    def test_target_analysis_contains_separate_structure_panel_and_reuses_viewer(self):
        root = Path(__file__).resolve().parents[1]
        target_workspace = (root / "frontend-next/components/workspaces/TargetAnalysisWorkspace.js").read_text(encoding="utf-8")
        panel = (root / "frontend-next/components/target-analysis/StructureAnalysisPanel.js").read_text(encoding="utf-8")
        discovery_workspace = (root / "frontend-next/components/workspaces/MoleculeDiscoveryWorkspace.js").read_text(encoding="utf-8")
        self.assertIn("<StructureAnalysisPanel file={file} validation={validation} />", target_workspace)
        self.assertIn("ProteinPDBViewer", panel)
        self.assertIn("sourceUrlForPdbId", panel)
        self.assertIn("compactLayout", panel)
        self.assertIn("/api/structures/curated", panel)
        self.assertIn("/api/structures/uploads", panel)
        self.assertNotIn('type="file"', panel)
        self.assertIn("file={file}", target_workspace)
        self.assertIn("validation={validation}", target_workspace)
        self.assertIn("lg:grid-cols-2", target_workspace)
        self.assertIn("does not start discovery", panel.lower())
        self.assertNotIn("/api/discover", target_workspace)
        self.assertIn("<ProteinPDBViewer", discovery_workspace)
        self.assertIn("chain_selection_required", panel)
        self.assertIn("authorized_for_calculation", (root / "backend/services/structure_analysis.py").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
