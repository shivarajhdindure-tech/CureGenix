"""Integrity tests for the local EGFR PDB registry and viewer preset labels."""

import hashlib
import json
import re
import unittest
from pathlib import Path

from backend.services.structure_registry import (
    PROJECT_ROOT,
    get_curated_structure,
    load_structure_manifest,
)


EXPECTED_IDS = {"1M17", "2ITX", "4G5J", "7A2A"}
NON_LIGAND_COMPONENTS = {"HOH", "WAT", "DOD", "SO4", "PO4", "CL", "NA", "MG", "ZN", "CA", "K"}
THREE_TO_ONE = {
    "ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C",
    "GLN": "Q", "GLU": "E", "GLY": "G", "HIS": "H", "ILE": "I",
    "LEU": "L", "LYS": "K", "MET": "M", "PHE": "F", "PRO": "P",
    "SER": "S", "THR": "T", "TRP": "W", "TYR": "Y", "VAL": "V",
}


class StructureRegistryTests(unittest.TestCase):
    def test_manifest_has_all_curated_structures_and_verified_files(self):
        manifest = load_structure_manifest()
        entries = manifest["structures"]
        self.assertEqual({entry["pdb_id"] for entry in entries}, EXPECTED_IDS)
        self.assertEqual(len(entries), len(EXPECTED_IDS))

        for entry in entries:
            with self.subTest(pdb_id=entry["pdb_id"]):
                relative = Path(entry["relative_path"])
                self.assertFalse(relative.is_absolute())
                self.assertNotIn("..", relative.parts)
                path = (PROJECT_ROOT / relative).resolve()
                path.relative_to(PROJECT_ROOT.resolve())
                self.assertTrue(path.is_file())
                self.assertEqual(
                    hashlib.sha256(path.read_bytes()).hexdigest(), entry["sha256"]
                )
                self.assertEqual(entry["file_format"], "PDB")
                self.assertEqual(entry["target_accession"], "P00533")
                self.assertEqual(
                    entry["source_url"],
                    f"https://files.rcsb.org/download/{entry['pdb_id']}.pdb",
                )

    def test_manifest_chains_accessions_and_ligand_components_match_pdb_records(self):
        for entry in load_structure_manifest()["structures"]:
            with self.subTest(pdb_id=entry["pdb_id"]):
                lines = (PROJECT_ROOT / entry["relative_path"]).read_text(
                    encoding="ascii", errors="replace"
                ).splitlines()
                atom_chains = sorted({line[21:22].strip() for line in lines if line.startswith("ATOM  ") and line[21:22].strip()})
                self.assertEqual(atom_chains, entry["protein_chains"])

                dbref_accessions = {
                    token for line in lines if line.startswith("DBREF")
                    for token in re.findall(r"\bP\d{5}\b", line)
                }
                self.assertEqual(dbref_accessions, {entry["target_accession"]})

                annotated_components = {
                    line[7:10].strip() for line in lines if line.startswith("HET    ")
                }
                ligand_components = annotated_components - NON_LIGAND_COMPONENTS
                self.assertEqual(ligand_components, set(entry["ligand_component_ids"]))

    def test_verified_mutations_match_seqadv_annotations(self):
        entry = next(
            item for item in load_structure_manifest()["structures"]
            if item["pdb_id"] == "7A2A"
        )
        lines = (PROJECT_ROOT / entry["relative_path"]).read_text(
            encoding="ascii", errors="replace"
        ).splitlines()
        observed = {}
        for line in lines:
            fields = line.split()
            if len(fields) >= 11 and fields[0] == "SEQADV" and fields[-2:] == ["ENGINEERED", "MUTATION"]:
                _, pdb_id, observed_residue, chain, _pdb_position, database, accession, reference_residue, uniprot_position, *_ = fields
                if pdb_id != entry["pdb_id"] or database != "UNP" or accession != entry["target_accession"]:
                    continue
                variant = (
                    f"{THREE_TO_ONE[reference_residue]}{uniprot_position}"
                    f"{THREE_TO_ONE[observed_residue]}"
                )
                observed.setdefault(variant, set()).add(chain)
        expected = {item["variant"]: set(item["chains"]) for item in entry["verified_mutations"]}
        self.assertEqual(observed, expected)

        other_entries = [item for item in load_structure_manifest()["structures"] if item["pdb_id"] != "7A2A"]
        for item in other_entries:
            with self.subTest(pdb_id=item["pdb_id"]):
                pdb_lines = (PROJECT_ROOT / item["relative_path"]).read_text(
                    encoding="ascii", errors="replace"
                ).splitlines()
                mutation_lines = [line for line in pdb_lines if line.startswith("SEQADV") and "ENGINEERED MUTATION" in line]
                self.assertFalse(item["verified_mutations"])
                self.assertEqual(mutation_lines, [])

    def test_registry_resolves_allowlisted_ids_not_client_paths(self):
        self.assertEqual(get_curated_structure("1m17")["pdb_id"], "1M17")
        with self.assertRaises(ValueError):
            get_curated_structure("../../outside")
        with self.assertRaises(KeyError):
            get_curated_structure("9ZZZ")

    def test_frontend_descriptions_match_curated_structure_metadata(self):
        frontend = (PROJECT_ROOT / "frontend-next/components/ProteinPDBViewer.js").read_text(encoding="utf-8")
        for entry in load_structure_manifest()["structures"]:
            with self.subTest(pdb_id=entry["pdb_id"]):
                pattern = rf'id:\s*"{entry["pdb_id"]}"[^\n]*description:\s*"([^"]*)"'
                match = re.search(pattern, frontend)
                self.assertIsNotNone(match)
                self.assertEqual(match.group(1), entry["verified_structure_description"])
        self.assertNotIn("T790M + Gefitinib", frontend)
        self.assertNotIn("C797S + Osimertinib", frontend)


if __name__ == "__main__":
    unittest.main()
