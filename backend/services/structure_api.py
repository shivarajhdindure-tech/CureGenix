"""Curated and custom PDB analysis endpoints, separate from discovery runs."""

from __future__ import annotations

import hashlib
import re
import uuid
from pathlib import Path
from pathlib import PurePosixPath
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from backend.services.structure_analysis import analyze_pdb_file
from backend.services.structure_registry import (
    get_curated_collection_metadata,
    get_curated_structure,
    load_structure_manifest,
)
from backend.services.ligand_extractor import extract_pdb_ligands


router = APIRouter(prefix="/api/structures", tags=["PDB structure analysis"])
UPLOAD_STORAGE_DIR = Path(__file__).resolve().parents[1] / "structure_uploads"
MAX_PDB_UPLOAD_BYTES = 20 * 1024 * 1024
_UPLOAD_ID = re.compile(r"^[0-9a-f]{32}$")
_CHUNK_BYTES = 64 * 1024


def _public_curated_entry(entry: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in entry.items() if key != "local_path"}


def _curated_or_http_error(pdb_id: str) -> dict[str, Any]:
    try:
        return get_curated_structure(pdb_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="PDB ID is not in the curated structure registry.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Curated structure file is missing.") from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail="Curated structure integrity check failed.") from exc


def _custom_upload_path(upload_id: str) -> Path:
    if not _UPLOAD_ID.fullmatch(upload_id or ""):
        raise HTTPException(status_code=422, detail="Invalid custom structure upload ID.")
    root = UPLOAD_STORAGE_DIR.resolve()
    path = (root / f"{upload_id}.pdb").resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid custom structure upload ID.") from exc
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Custom structure upload was not found.")
    return path


def _with_structure_source(analysis: dict[str, Any], *, source_kind: str, pdb_id: str | None,
                           file_url: str, sha256: str, source_url: str | None,
                           relative_path: str | None = None) -> dict[str, Any]:
    return {
        **analysis,
        "source": {
            "kind": source_kind,
            "pdb_id": pdb_id,
            "relative_path": relative_path,
            "sha256": sha256,
            "source_url": source_url,
            "file_url": file_url,
        },
    }


@router.get("/curated")
def list_curated_structures():
    """List only manifest-defined IDs and their root-relative provenance."""
    structures = []
    for entry in load_structure_manifest().get("structures", []):
        verified = _curated_or_http_error(str(entry.get("pdb_id") or ""))
        structures.append(_public_curated_entry(verified))
    return {
        "collection": get_curated_collection_metadata(),
        "structures": structures,
    }


@router.get("/curated/{pdb_id}/ligands")
def get_curated_structure_ligands(pdb_id: str, chain_id: str | None = None):
    """Return validated co-crystallized ligands for a curated EGFR structure."""
    entry = _curated_or_http_error(pdb_id)
    ligands = extract_pdb_ligands(entry["local_path"], selected_chain_id=chain_id)
    return {
        "pdb_id": entry["pdb_id"],
        "selected_chain_id": chain_id,
        "collection": get_curated_collection_metadata(),
        "ligands": ligands,
        "co_crystallized_drug_candidates": [l for l in ligands if l["is_drug_candidate"]],
    }


@router.get("/curated/{pdb_id}/file")
def get_curated_structure_file(pdb_id: str):
    entry = _curated_or_http_error(pdb_id)
    return FileResponse(
        path=entry["local_path"],
        media_type="chemical/x-pdb",
        filename=f"{entry['pdb_id']}.pdb",
    )


@router.get("/curated/{pdb_id}")
def analyze_curated_structure(pdb_id: str, chain_id: str | None = None):
    entry = _curated_or_http_error(pdb_id)
    try:
        analysis = analyze_pdb_file(entry["local_path"], selected_chain_id=chain_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if analysis.get("pdb_id") and analysis["pdb_id"] != entry["pdb_id"]:
        validation = analysis["validation"]
        validation["status"] = "header_id_mismatch"
        validation["warnings"] = list(validation["warnings"]) + [
            f"PDB HEADER ID {analysis['pdb_id']} does not match curated registry ID {entry['pdb_id']}."
        ]
    return _with_structure_source(
        analysis,
        source_kind="curated_local",
        pdb_id=entry["pdb_id"],
        file_url=f"/api/structures/curated/{entry['pdb_id']}/file",
        sha256=entry["sha256"],
        source_url=entry["source_url"],
        relative_path=entry["relative_path"],
    )


@router.post("/uploads")
async def upload_custom_structure(file: UploadFile = File(...), chain_id: str | None = Form(default=None)):
    """Store a validated custom PDB under a generated ID and return its analysis."""
    filename = PurePosixPath((file.filename or "").replace("\\", "/")).name
    if not filename or not filename.lower().endswith(".pdb"):
        raise HTTPException(status_code=415, detail="Only PDB files with a .pdb filename are supported.")
    if file.size is not None and file.size > MAX_PDB_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"PDB upload exceeds the {MAX_PDB_UPLOAD_BYTES // (1024 * 1024)} MiB limit.")

    UPLOAD_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    upload_id = uuid.uuid4().hex
    saved_path = UPLOAD_STORAGE_DIR / f"{upload_id}.pdb"
    digest = hashlib.sha256()
    total_bytes = 0
    created_path = False
    try:
        with saved_path.open("xb") as output:
            created_path = True
            while True:
                chunk = await file.read(_CHUNK_BYTES)
                if not chunk:
                    break
                total_bytes += len(chunk)
                if total_bytes > MAX_PDB_UPLOAD_BYTES:
                    raise HTTPException(status_code=413, detail=f"PDB upload exceeds the {MAX_PDB_UPLOAD_BYTES // (1024 * 1024)} MiB limit.")
                digest.update(chunk)
                output.write(chunk)
        if total_bytes == 0:
            raise HTTPException(status_code=422, detail="PDB upload is empty.")
        analysis = analyze_pdb_file(saved_path, selected_chain_id=chain_id)
    except HTTPException:
        if created_path:
            saved_path.unlink(missing_ok=True)
        raise
    except ValueError as exc:
        if created_path:
            saved_path.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception:
        if created_path:
            saved_path.unlink(missing_ok=True)
        raise
    finally:
        await file.close()

    result = _with_structure_source(
        analysis,
        source_kind="custom_upload",
        pdb_id=analysis.get("pdb_id"),
        file_url=f"/api/structures/uploads/{upload_id}/file",
        sha256=digest.hexdigest(),
        source_url=None,
    )
    result["upload_id"] = upload_id
    result["original_filename"] = filename
    result["stored_size_bytes"] = total_bytes
    return result


@router.get("/uploads/{upload_id}/file")
def get_custom_structure_file(upload_id: str):
    path = _custom_upload_path(upload_id)
    return FileResponse(path=path, media_type="chemical/x-pdb", filename=f"custom-{upload_id}.pdb")


@router.get("/uploads/{upload_id}")
def analyze_custom_structure(upload_id: str, chain_id: str | None = None):
    path = _custom_upload_path(upload_id)
    try:
        analysis = analyze_pdb_file(path, selected_chain_id=chain_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Stored PDB upload could not be analyzed.") from exc
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    result = _with_structure_source(
        analysis,
        source_kind="custom_upload",
        pdb_id=analysis.get("pdb_id"),
        file_url=f"/api/structures/uploads/{upload_id}/file",
        sha256=digest,
        source_url=None,
    )
    result["upload_id"] = upload_id
    return result


@router.get("/uploads/{upload_id}/ligands")
def get_custom_structure_ligands(upload_id: str, chain_id: str | None = None):
    """Return extracted co-crystallized ligands for a custom PDB upload."""
    path = _custom_upload_path(upload_id)
    ligands = extract_pdb_ligands(path, selected_chain_id=chain_id)
    return {
        "upload_id": upload_id,
        "selected_chain_id": chain_id,
        "ligands": ligands,
        "co_crystallized_drug_candidates": [l for l in ligands if l["is_drug_candidate"]],
    }
