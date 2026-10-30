"""Allowlisted access to the checked-in EGFR PDB structure registry."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = PROJECT_ROOT / "data" / "structures" / "egfr" / "manifest.json"
_PDB_ID = re.compile(r"^[0-9A-Z]{4}$")


def load_structure_manifest() -> dict[str, Any]:
    """Load the curated manifest from its fixed project-relative location."""
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def get_curated_collection_metadata() -> dict[str, Any]:
    """Return top-level curated collection metadata establishing the EGFR focus."""
    manifest = load_structure_manifest()
    return {
        "collection_id": manifest.get("collection_id", "egfr_focused_curated_v1"),
        "collection_name": manifest.get("collection_name", "CureGenix EGFR-Focused Curated Structure Collection"),
        "target_name": manifest.get("target_name", "Epidermal growth factor receptor (EGFR)"),
        "target_accession": manifest.get("target_accession", "P00533"),
        "collection_description": manifest.get("collection_description", ""),
        "total_structures": len(manifest.get("structures", [])),
    }


def get_curated_structure(pdb_id: str) -> dict[str, Any]:
    """Return one allowlisted structure after checking its path and digest.

    Callers select by PDB ID only. No caller-provided filesystem path is
    accepted or joined to the project root.
    """
    normalized_id = str(pdb_id or "").strip().upper()
    if not _PDB_ID.fullmatch(normalized_id):
        raise ValueError("PDB ID must be a four-character alphanumeric code.")

    entry = next(
        (item for item in load_structure_manifest().get("structures", [])
         if item.get("pdb_id") == normalized_id),
        None,
    )
    if entry is None:
        raise KeyError(f"PDB ID {normalized_id} is not in the curated structure registry.")

    relative_path = Path(entry["relative_path"])
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise ValueError("Curated structure paths must remain relative to the project root.")

    structure_path = (PROJECT_ROOT / relative_path).resolve()
    try:
        structure_path.relative_to(PROJECT_ROOT.resolve())
    except ValueError as exc:
        raise ValueError("Curated structure path escapes the project root.") from exc
    if not structure_path.is_file():
        raise FileNotFoundError(f"Curated structure file is missing for {normalized_id}.")

    actual_sha256 = hashlib.sha256(structure_path.read_bytes()).hexdigest()
    if actual_sha256 != str(entry.get("sha256", "")).lower():
        raise RuntimeError(f"SHA-256 mismatch for curated structure {normalized_id}.")

    return {**entry, "local_path": structure_path}
