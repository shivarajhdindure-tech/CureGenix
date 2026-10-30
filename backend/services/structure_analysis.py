"""PDB header and atom-record analysis only; no ligand chemistry is inferred."""

from __future__ import annotations

from collections import defaultdict
import math
from pathlib import Path
from typing import Any

from backend.services.target_identity import parse_pdb_identity
from backend.services.target_sequence import extract_pdb_chain_sequences
from backend.services.ligand_extractor import extract_pdb_ligands


WATER_COMPONENTS = {"HOH", "WAT", "DOD", "H2O", "OH2", "H3O"}


def _chain_id(value: str) -> str:
    return value.strip() or "_"


def _parse_sequence_annotations(lines: list[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    seqres_by_chain: dict[str, dict[str, Any]] = {}
    sequence_variants = []
    for line_number, line in enumerate(lines, start=1):
        record = line[:6]
        if record == "SEQRES" and len(line) >= 20:
            chain = _chain_id(line[11:12])
            entry = seqres_by_chain.setdefault(chain, {"chain_id": chain, "declared_residue_count": None, "residues": []})
            try:
                entry["declared_residue_count"] = int(line[13:17].strip())
            except ValueError:
                pass
            entry["residues"].extend(line[19:70].split())
        elif record == "SEQADV":
            fields = line.split()
            annotation: dict[str, Any] = {"line_number": line_number, "raw_record": line.rstrip()}
            if len(fields) >= 6:
                annotation.update({"pdb_id": fields[1], "observed_residue": fields[2], "chain_id": fields[3], "pdb_residue_number": fields[4]})
                if len(fields) >= 9 and fields[5] == "UNP":
                    annotation.update({"database": fields[5], "accession": fields[6], "reference_residue": fields[7], "reference_residue_number": fields[8]})
                annotation["annotation"] = " ".join(fields[9:]) if len(fields) > 9 else ""
                annotation["is_engineered_mutation"] = "ENGINEERED MUTATION" in annotation["annotation"]
            sequence_variants.append(annotation)
    return [seqres_by_chain[key] for key in sorted(seqres_by_chain)], sequence_variants


def _parse_non_water_hetatm(lines: list[str]) -> list[dict[str, Any]]:
    residues: dict[tuple[str, str, str, str], int] = defaultdict(int)
    for line in lines:
        if not line.startswith("HETATM") or len(line) < 27:
            continue
        component = line[17:20].strip().upper()
        if not component or component in WATER_COMPONENTS:
            continue
        key = (component, _chain_id(line[21:22]), line[22:26].strip(), line[26:27].strip())
        residues[key] += 1
    return [
        {"component_id": component, "chain_id": chain, "residue_number": number,
         "insertion_code": insertion or None, "atom_count": atom_count}
        for (component, chain, number, insertion), atom_count in sorted(residues.items())
    ]


def analyze_pdb_file(path: str | Path, selected_chain_id: str | None = None) -> dict[str, Any]:
    """Analyze a PDB file and report annotations without authorizing chemistry."""
    pdb_path = Path(path)
    raw = pdb_path.read_bytes()
    if not raw or b"\x00" in raw:
        raise ValueError("The uploaded file is empty or is not plain-text PDB content.")
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError as exc:
        raise ValueError("PDB input must contain ASCII PDB records.") from exc
    lines = text.splitlines()
    atom_lines = [line for line in lines if line.startswith("ATOM  ")]
    if not atom_lines:
        raise ValueError("PDB input must contain protein ATOM coordinate records.")
    valid_coordinate_count = 0
    for line in atom_lines:
        if len(line) < 54:
            continue
        try:
            coordinates = [float(line[start:start + 8]) for start in (30, 38, 46)]
        except ValueError:
            continue
        if all(math.isfinite(value) for value in coordinates):
            valid_coordinate_count += 1
    if not valid_coordinate_count:
        raise ValueError("PDB input has no valid fixed-column ATOM coordinates.")

    structure_evidence = parse_pdb_identity(lines)
    coordinate_chains = structure_evidence["chain_ids"]
    observed_sequences = extract_pdb_chain_sequences(lines, coordinate_chains)
    chains = sorted(
        chain for chain in coordinate_chains
        if (observed_sequences.get(chain) or {}).get("sequence")
    )
    if not chains:
        raise ValueError("No protein chains were found in PDB ATOM records.")
    seqres_annotations, sequence_variants = _parse_sequence_annotations(lines)
    warnings = list(structure_evidence.get("warnings") or [])
    malformed_coordinate_count = len(atom_lines) - valid_coordinate_count
    if malformed_coordinate_count:
        warnings.append(f"{malformed_coordinate_count} ATOM record(s) have malformed or non-finite coordinates.")

    selection = _chain_id(selected_chain_id) if selected_chain_id else None
    if len(chains) > 1 and not selection:
        validation_status = "chain_selection_required"
        warnings.append("This structure contains multiple protein chains. Select a chain to continue structure analysis.")
    elif selection and selection not in chains:
        validation_status = "invalid_chain_selection"
        warnings.append(f"Selected chain {selection} is not present in the protein ATOM records.")
    else:
        if selection is None:
            selection = chains[0]
        selected_accessions = structure_evidence.get("chain_accessions", {}).get(selection, [])
        if len(selected_accessions) > 1:
            validation_status = "ambiguous_chain_accession"
            warnings.append(f"Chain {selection} has multiple DBREF accessions; identity is ambiguous.")
        elif not selected_accessions:
            validation_status = "identity_unresolved"
            warnings.append(f"No usable UniProt DBREF accession was found for chain {selection}.")
        else:
            validation_status = "valid_structure_annotation_only"

    if not any(line.startswith("HEADER") for line in lines):
        warnings.append("No PDB HEADER record was found; the PDB ID is unresolved from file annotations.")
    header_pdb_id = next((line[62:66].strip().upper() for line in lines if line.startswith("HEADER") and len(line) >= 66 and line[62:66].strip()), None)
    title = " ".join(line[10:].strip() for line in lines if line.startswith("TITLE ")).strip() or None
    chain_sequences = {}
    for chain in chains:
        sequence = observed_sequences.get(chain) or {}
        chain_sequences[chain] = {
            "observed_residue_count": sequence.get("observed_residue_count", len(sequence.get("sequence", ""))),
            "sequence": sequence.get("sequence", ""),
            "warnings": sequence.get("warnings", []),
        }
    selected_accessions = (
        structure_evidence.get("chain_accessions", {}).get(selection, [])
        if selection in chains else []
    )
    return {
        "pdb_id": header_pdb_id,
        "title": title,
        "protein_chains": chains,
        "selected_chain_id": selection if selection in chains else None,
        "chain_accessions": structure_evidence.get("chain_accessions", {}),
        "dbref_records": structure_evidence.get("dbref_records", []),
        "sequence_annotations": {
            "seqres": seqres_annotations,
            "seqadv": sequence_variants,
            "observed_chains": chain_sequences,
        },
        "mutation_annotations": [item for item in sequence_variants if item.get("is_engineered_mutation")],
        "non_water_hetatm_residues": _parse_non_water_hetatm(lines),
        "co_crystallized_ligands": extract_pdb_ligands(lines, selected_chain_id=selection),
        "target_identity": {
            "status": "structure_annotation_only" if len(selected_accessions) == 1 else "unresolved_or_ambiguous",
            "accession": selected_accessions[0] if len(selected_accessions) == 1 else None,
            "verified": False,
            "authorized_for_calculation": False,
            "note": "DBREF is a structure annotation; sequence validation and calculation authorization are not performed by this analysis endpoint.",
        },
        "validation": {
            "status": validation_status,
            "pdb_coordinate_records_valid": True,
            "warnings": list(dict.fromkeys(warnings)),
        },
        "scientific_limitations": [
            "Non-water HETATM records are a residue inventory only; they do not establish molecular connectivity, bond orders, or ligand identity.",
            "No SMILES, binding affinity, efficacy, or target engagement is inferred.",
            "No PySCF, Qiskit, or IBM Quantum calculation is run by this endpoint.",
        ],
    }
