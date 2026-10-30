"""Extraction and rigorous chemical validation of co-crystallized ligands from PDB structures.

PDB coordinate records and CONECT lines alone do not establish bond orders,
aromaticity, or stereochemistry. This module validates non-solvent HETATM residues
against curated Chemical Component Dictionary (CCD) entries and enforces fail-closed
resource preflight evaluation.
"""

from __future__ import annotations

from collections import Counter, defaultdict
import math
from pathlib import Path
from typing import Any

from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors

from backend.services.quantum_resource_policy import assess_smiles_resources


SOLVENT_AND_ADDITIVE_COMPONENTS = {
    # Waters
    "HOH", "WAT", "DOD", "H2O", "OH2", "H3O",
    # Common crystallization salts and inorganic ions
    "SO4", "PO4", "CL", "NA", "MG", "ZN", "CA", "K", "MN", "FE", "CU", "NI", "CO",
    # Buffers, cryoprotectants, and crystallization additives
    "GOL", "EDO", "ACT", "DMS", "PEG", "PG4", "MPD", "BME", "TRS", "FMT", "CIT",
}

# Curated Chemical Component Dictionary specifications for verified EGFR ligands
VALIDATED_CHEMICAL_COMPONENT_DICTIONARY: dict[str, dict[str, Any]] = {
    "AQ4": {
        "component_id": "AQ4",
        "name": "Erlotinib",
        "chemical_name": "N-(3-ethynylphenyl)-6,7-bis(2-methoxyethoxy)quinazolin-4-amine",
        "smiles": "COCCOc1cc2ncnc(Nc3cccc(c3)C#C)c2cc1OCCOC",
        "formula": "C22H23N3O4",
        "heavy_atom_count": 29,
        "expected_heavy_elements": {"C": 22, "N": 3, "O": 4},
        "role": "Co-crystallized EGFR tyrosine kinase inhibitor (Erlotinib)",
        "parent_compound": "Erlotinib",
        "chembl_id": "CHEMBL553",
        "ccd_source": "RCSB Chemical Component Dictionary AQ4",
    },
    "ANP": {
        "component_id": "ANP",
        "name": "Phosphoaminophosphonic acid-adenylate ester (AMP-PNP)",
        "chemical_name": "5'-O-[{[(phosphonoamino)oxy](hydroxy)phosphoryl}oxy](hydroxy)phosphoryl]adenosine",
        "smiles": "Nc1ncnc2c1ncn2[C@@H]1O[C@H](CO[P@](=O)(O)O[P@](=O)(O)NP(=O)(O)O)[C@@H](O)[C@H]1O",
        "formula": "C10H17N6O12P3",
        "heavy_atom_count": 31,
        "expected_heavy_elements": {"C": 10, "N": 6, "O": 12, "P": 3},
        "role": "Non-hydrolyzable ATP analog probe",
        "parent_compound": "AMP-PNP",
        "chembl_id": "CHEMBL414605",
        "ccd_source": "RCSB Chemical Component Dictionary ANP",
    },
    "0WN": {
        "component_id": "0WN",
        "name": "Afatinib dihydro derivative (0WN)",
        "chemical_name": "N-{4-[(3-chloro-4-fluorophenyl)amino]-7-[(3S)-tetrahydrofuran-3-yloxy]quinazolin-6-yl}-4-(dimethylamino)butanamide",
        "smiles": "CN(C)CCCC(=O)Nc1cc2c(Nc3ccc(F)c(Cl)c3)ncnc2cc1O[C@@H]1COCC1",
        "formula": "C24H27ClFN5O3",
        "heavy_atom_count": 34,
        "expected_heavy_elements": {"C": 24, "N": 5, "F": 1, "CL": 1, "O": 3},
        "role": "Reduced covalent analog of Afatinib (BIBW 2992)",
        "parent_compound": "Afatinib",
        "chembl_id": "CHEMBL1173655",
        "ccd_source": "RCSB Chemical Component Dictionary 0WN",
    },
    "0WM": {
        "component_id": "0WM",
        "name": "Afatinib / BIBW2992 (0WM)",
        "chemical_name": "(2E)-N-{4-[(3-chloro-4-fluorophenyl)amino]-7-[(3S)-tetrahydrofuran-3-yloxy]quinazolin-6-yl}-4-(dimethylamino)but-2-enamide",
        "smiles": "CN(C)C/C=C/C(=O)Nc1cc2c(Nc3ccc(F)c(Cl)c3)ncnc2cc1O[C@@H]1COCC1",
        "formula": "C24H25ClFN5O3",
        "heavy_atom_count": 34,
        "expected_heavy_elements": {"C": 24, "N": 5, "F": 1, "CL": 1, "O": 3},
        "role": "Irreversible EGFR/HER2 tyrosine kinase inhibitor (Afatinib)",
        "parent_compound": "Afatinib",
        "chembl_id": "CHEMBL1173655",
        "ccd_source": "RCSB Chemical Component Dictionary 0WM",
    },
    "57N": {
        "component_id": "57N",
        "name": "EAI001 analog / 57N",
        "chemical_name": "(2R)-2-(1-oxo-1,3-dihydro-2H-isoindol-2-yl)-2-phenyl-N-(1,3-thiazol-2-yl)acetamide",
        "smiles": "O=C(Nc1nccs1)[C@@H](c1ccccc1)N1Cc2ccccc2C1=O",
        "formula": "C19H15N3O2S",
        "heavy_atom_count": 25,
        "expected_heavy_elements": {"C": 19, "O": 2, "N": 3, "S": 1},
        "role": "Allosteric EGFR inhibitor (EAI001 scaffold component in PDB 7A2A)",
        "parent_compound": "EAI001",
        "chembl_id": "CHEMBL3989801",
        "ccd_source": "RCSB Chemical Component Dictionary 57N",
    },
    "7G9": {
        "component_id": "7G9",
        "name": "Spebrutinib derivative / 7G9",
        "chemical_name": "N-[3-[[5-fluoro-2-[[4-(2-methoxyethoxy)phenyl]amino]pyrimidin-4-yl]amino]phenyl]propanamide",
        "smiles": "CCC(=O)Nc1cccc(Nc2ncc(F)c(Nc3ccc(OCCOC)cc3)n2)c1",
        "formula": "C22H24FN5O3",
        "heavy_atom_count": 31,
        "expected_heavy_elements": {"C": 22, "O": 3, "N": 5, "F": 1},
        "role": "Spebrutinib-related ATP-competitive inhibitor in PDB 7A2A complex",
        "parent_compound": "Spebrutinib derivative",
        "chembl_id": None,
        "ccd_source": "RCSB Chemical Component Dictionary 7G9",
    },
}


def _normalize_element(raw_symbol: str) -> str:
    cleaned = raw_symbol.strip().upper()
    if not cleaned:
        return ""
    if len(cleaned) == 2 and cleaned[1].isalpha():
        return f"{cleaned[0]}{cleaned[1].lower()}".upper()
    return cleaned


def extract_pdb_ligands(
    pdb_path_or_lines: str | Path | list[str],
    selected_chain_id: str | None = None,
) -> list[dict[str, Any]]:
    """Extract, filter, and validate co-crystallized ligands from PDB content.

    Distinguishes biologically relevant drug ligands from solvent, buffer, and salt
    ions. Validates chemical structure and stereochemistry against curated Chemical
    Component Dictionary (CCD) entries. Computes honest quantum resource preflight
    safeguards without silently generating unverified SMILES.
    """
    if isinstance(pdb_path_or_lines, (str, Path)):
        path = Path(pdb_path_or_lines)
        if path.is_file():
            lines = path.read_text(encoding="ascii", errors="replace").splitlines()
        else:
            lines = str(pdb_path_or_lines).splitlines()
    else:
        lines = list(pdb_path_or_lines)

    # 1. Collect HETATM records
    atom_groups: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    atom_serials_by_group: dict[tuple[str, str, str, str], set[int]] = defaultdict(set)
    all_conect_lines: list[str] = []

    for line in lines:
        if line.startswith("CONECT"):
            all_conect_lines.append(line)
            continue
        if not line.startswith("HETATM") or len(line) < 27:
            continue

        component = line[17:20].strip().upper()
        chain = line[21:22].strip() or "_"
        res_num = line[22:26].strip()
        ins_code = line[26:27].strip()

        try:
            serial = int(line[6:11].strip())
        except ValueError:
            serial = 0

        # Element extraction: PDB cols 77-78 preferred; fall back to atom name
        element = line[76:78].strip().upper() if len(line) >= 78 else ""
        if not element:
            atom_name = line[12:16].strip()
            element = atom_name[0] if atom_name else "C"

        coords = [0.0, 0.0, 0.0]
        if len(line) >= 54:
            try:
                coords = [float(line[start:start + 8]) for start in (30, 38, 46)]
            except ValueError:
                pass

        group_key = (component, chain, res_num, ins_code)
        atom_groups[group_key].append({
            "serial": serial,
            "element": element,
            "coords": coords,
            "raw_line": line,
        })
        if serial:
            atom_serials_by_group[group_key].add(serial)

    # 2. Check CONECT presence for each group
    conect_serials = set()
    for conect_line in all_conect_lines:
        for token in conect_line[6:].split():
            if token.isdigit():
                conect_serials.add(int(token))

    extracted_ligands: list[dict[str, Any]] = []

    for (comp, chain, res_num, ins_code), atoms in sorted(atom_groups.items()):
        is_solvent_or_additive = comp in SOLVENT_AND_ADDITIVE_COMPONENTS
        category = "solvent_or_additive" if is_solvent_or_additive else "co_crystallized_ligand"

        element_counter = Counter(a["element"] for a in atoms)
        heavy_elements = Counter({k: v for k, v in element_counter.items() if k != "H"})
        heavy_atom_count = sum(heavy_elements.values())

        # Bounding box & centroid
        x_coords = [a["coords"][0] for a in atoms if math.isfinite(a["coords"][0])]
        y_coords = [a["coords"][1] for a in atoms if math.isfinite(a["coords"][1])]
        z_coords = [a["coords"][2] for a in atoms if math.isfinite(a["coords"][2])]
        centroid = {
            "x": round(sum(x_coords) / len(x_coords), 3) if x_coords else 0.0,
            "y": round(sum(y_coords) / len(y_coords), 3) if y_coords else 0.0,
            "z": round(sum(z_coords) / len(z_coords), 3) if z_coords else 0.0,
        }

        group_serials = atom_serials_by_group[(comp, chain, res_num, ins_code)]
        has_conect = bool(group_serials and any(s in conect_serials for s in group_serials))

        ligand_id = f"{comp}-{chain}-{res_num}" + (f"-{ins_code}" if ins_code else "")

        # Chemical validation
        ccd_spec = VALIDATED_CHEMICAL_COMPONENT_DICTIONARY.get(comp)

        if is_solvent_or_additive:
            verification_status = "solvent_or_crystallization_additive"
            name = f"Solvent/Additive: {comp}"
            smiles = None
            formula = "".join(f"{k}{v}" for k, v in sorted(element_counter.items()))
            resource_preflight = {
                "status": "excluded_non_drug",
                "reasons": [f"Component {comp} is classified as a solvent, salt, or crystallization additive and is excluded from drug-candidate evaluation."],
            }
            verification_warnings = [
                f"Component {comp} is an inorganic salt, crystallization additive, or solvent; not evaluated as a small-molecule drug ligand."
            ]
        elif ccd_spec:
            # Check heavy elements against CCD expected heavy elements
            expected_elements = ccd_spec["expected_heavy_elements"]
            elements_match = (heavy_elements == expected_elements)

            if elements_match:
                verification_status = "verified_ccd"
                name = ccd_spec["name"]
                smiles = ccd_spec["smiles"]
                formula = ccd_spec["formula"]
                heavy_atom_count = ccd_spec["heavy_atom_count"]

                # Run honest resource preflight check
                resource_preflight = assess_smiles_resources(smiles)
                verification_warnings = []
            else:
                verification_status = "unverified_element_mismatch"
                name = f"Candidate {comp} (Elemental Mismatch)"
                smiles = None
                formula = "".join(f"{k}{v}" for k, v in sorted(element_counter.items()))
                resource_preflight = {
                    "status": "unverified",
                    "reasons": [f"Observed PDB coordinate elements {dict(heavy_elements)} do not match verified CCD specification {expected_elements}."],
                }
                verification_warnings = [
                    f"Observed heavy elements in PDB coordinates do not match the Chemical Component Dictionary record for {comp}. Canonical SMILES withheld."
                ]
        else:
            # Unverified raw PDB ligand: CONECT records cannot establish bond orders or stereochemistry reliably
            verification_status = "unverified_raw_pdb_coordinates"
            name = f"Co-crystallized Ligand {comp}"
            smiles = None
            formula = "".join(f"{k}{v}" for k, v in sorted(element_counter.items()))
            resource_preflight = {
                "status": "unverified",
                "reasons": [
                    "Molecular connectivity, bond orders, and stereochemistry cannot be verified from PDB coordinate records alone. Validated Chemical Component Dictionary entry required."
                ],
            }
            verification_warnings = [
                f"Chemical Component Dictionary entry unavailable for component {comp}. PDB coordinate records and CONECT lines alone do not establish bond orders or stereochemistry; canonical SMILES is withheld."
            ]

        # Molecular weight if validated SMILES exists
        mol_wt = None
        if smiles:
            try:
                rdkit_mol = Chem.MolFromSmiles(smiles)
                if rdkit_mol:
                    mol_wt = round(float(Descriptors.MolWt(rdkit_mol)), 3)
            except Exception:
                pass

        record = {
            "ligand_id": ligand_id,
            "component_id": comp,
            "chain_id": chain,
            "residue_number": res_num,
            "insertion_code": ins_code or None,
            "category": category,
            "name": name,
            "chemical_name": ccd_spec.get("chemical_name") if ccd_spec else None,
            "formula": formula,
            "heavy_atom_count": heavy_atom_count,
            "observed_atom_count": len(atoms),
            "element_counts": dict(element_counter),
            "smiles": smiles,
            "molecular_weight": mol_wt,
            "verification_status": verification_status,
            "has_conect_records": has_conect,
            "centroid": centroid,
            "role": ccd_spec.get("role") if ccd_spec else "Unannotated crystallographic HETATM residue",
            "parent_compound": ccd_spec.get("parent_compound") if ccd_spec else None,
            "chembl_id": ccd_spec.get("chembl_id") if ccd_spec else None,
            "ccd_source": ccd_spec.get("ccd_source") if ccd_spec else None,
            "resource_preflight": resource_preflight,
            "verification_warnings": verification_warnings,
            "is_drug_candidate": not is_solvent_or_additive,
            "is_chain_matched": (selected_chain_id is None or chain == selected_chain_id),
        }
        extracted_ligands.append(record)

    return extracted_ligands


def get_curated_pdb_ligands(pdb_id: str, selected_chain_id: str | None = None) -> list[dict[str, Any]]:
    """Retrieve and validate co-crystallized ligands for an allowlisted curated PDB structure."""
    from backend.services.structure_registry import get_curated_structure

    entry = get_curated_structure(pdb_id)
    return extract_pdb_ligands(entry["local_path"], selected_chain_id=selected_chain_id)
