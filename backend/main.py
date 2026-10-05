"""
FastAPI Entry Point — AI Drug Discovery Assistant API

Endpoints:
  POST /api/discover      — Upload PDB file and run the full drug discovery pipeline
  GET  /api/mcp-tools     — List all MCP tools (transparency)
  GET  /api/health        — Health check
"""

import os
import sys
import shutil
import re

# Add parent directory to path so imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.orchestrator import Orchestrator
from backend.services.pdb_parser import parse_pdb_file

PROTEIN_NAME_SCORE_SARS_COV = 8
PROTEIN_NAME_SCORE_SPIKE_GLYCO = 6
PROTEIN_NAME_SCORE_PENALTY_GENERIC = -5


app = FastAPI(
    title="AI Drug Discovery Assistant",
    description="MCP-powered multi-agent system for intelligent drug discovery from protein structures",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize orchestrator (singleton)
orchestrator = Orchestrator()

# Temp upload directory (inside the project)
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Mount frontend static files
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")


def _normalize_protein_name(name: str) -> str:
    cleaned = re.sub(r"\s+", " ", (name or "")).strip(" ;,.")
    cleaned = re.sub(r"(?i)^structure\s+of\s+", "", cleaned).strip()
    if cleaned.isupper():
        cleaned = cleaned.title()
    cleaned = cleaned.replace("Sars-Cov-2", "SARS-CoV-2")
    cleaned = cleaned.replace("Sars Cov 2", "SARS-CoV-2")
    return cleaned


def _extract_uploaded_protein_metadata(file_path: str, filename: str, parsed_protein: dict) -> dict:
    fallback_pdb_id = os.path.splitext(filename)[0].upper()
    parsed_name = (parsed_protein.get("protein", {}) or {}).get("name") or ""
    parsed_pdb_id = (parsed_protein.get("metadata", {}) or {}).get("protein_id") or ""

    header_name = ""
    compnd_name = ""
    title_lines = []
    header_pdb_id = ""

    with open(file_path, "r", encoding="utf-8", errors="ignore") as pdb_file:
        for line in pdb_file:
            record = line[:6]
            if record == "HEADER":
                header_name = line[10:50].strip() or header_name
                header_pdb_id = (line[62:66].strip() or header_pdb_id).upper()
            elif record == "COMPND":
                comp_match = re.search(r"MOLECULE:\s*(.*?);", line, re.IGNORECASE)
                if comp_match and comp_match.group(1).strip():
                    compnd_name = comp_match.group(1).strip()
            elif record == "TITLE ":
                title_text = line[10:].strip()
                if title_text:
                    title_lines.append(title_text)

    title_name = " ".join(title_lines).strip()
    candidates = [title_name, compnd_name, parsed_name, header_name]
    candidates = [c for c in candidates if c]

    def score_name(candidate: str) -> tuple[int, int]:
        """Return (quality_score, candidate_length) for metadata name selection."""
        lower = candidate.lower()
        score = len(candidate.split())
        if "sars-cov" in lower:
            score += PROTEIN_NAME_SCORE_SARS_COV
        if "spike glycoprotein" in lower:
            score += PROTEIN_NAME_SCORE_SPIKE_GLYCO
        if lower.strip() in {"viral protein", "protein", "unknown"}:
            score += PROTEIN_NAME_SCORE_PENALTY_GENERIC
        return score, len(candidate)

    selected_name = max(candidates, key=score_name) if candidates else fallback_pdb_id
    selected_name = _normalize_protein_name(selected_name)
    pdb_id = (parsed_pdb_id or header_pdb_id or fallback_pdb_id).upper()
    name_with_id = f"{selected_name} ({pdb_id})" if pdb_id else selected_name

    return {
        "name": name_with_id,
        "base_name": selected_name,
        "pdb_id": pdb_id,
        "source": "uploaded",
    }


@app.get("/")
async def serve_frontend():
    """Serve the frontend index.html."""
    index_path = os.path.join(frontend_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "AI Drug Discovery Assistant API", "docs": "/docs"}


@app.post("/api/discover")
async def discover(file: UploadFile = File(...)):
    """
    Upload a PDB file and run the full drug discovery pipeline.

    The file is parsed by the Node.js pdb2json-parser to produce
    AlphaFold-compatible JSON, which is then fed into the agent pipeline.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")

    if not file.filename.lower().endswith(".pdb"):
        raise HTTPException(status_code=400, detail="Only .pdb files are supported")

    # Save the uploaded file
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Parse PDB → AlphaFold-compatible JSON
        parsed_protein = parse_pdb_file(file_path)
        protein_metadata = _extract_uploaded_protein_metadata(file_path, file.filename, parsed_protein)
        parsed_protein.setdefault("protein", {})["name"] = protein_metadata["base_name"]
        parsed_protein.setdefault("metadata", {})["protein_id"] = protein_metadata["pdb_id"]

        # Run the agent pipeline with parsed protein data
        result = orchestrator.run_pipeline(parsed_protein, protein_metadata=protein_metadata)

        return result

    except RuntimeError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")
    finally:
        # Cleanup temp file
        if os.path.exists(file_path):
            os.remove(file_path)


@app.get("/api/mcp-tools")
async def list_mcp_tools():
    """List all MCP tools across all servers (for demo transparency)."""
    tools = orchestrator.get_mcp_tools()
    total = sum(len(t) for t in tools.values())
    return {"mcp_servers": tools, "total_tools": total}


@app.get("/api/health")
async def health():
    return {"status": "healthy", "service": "AI Drug Discovery Assistant", "version": "2.0.0"}
