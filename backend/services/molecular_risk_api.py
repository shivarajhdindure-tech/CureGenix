"""FastAPI Router for the Molecular Risk & Digital Twin workspace.

Exposes endpoints for manual candidate risk assessment, status polling, report retrieval,
and cooperative cancellation.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from backend.models.molecular_risk_models import (
    MolecularRiskReport,
    RiskAnalyzeRequest,
    RiskCandidateRecord,
)
from backend.services.molecular_risk_service import molecular_risk_service


router = APIRouter(prefix="/api/molecular-risk", tags=["Molecular Risk & Digital Twin"])


class CancelResponse(BaseModel):
    report_id: str
    cancelled: bool
    message: str


@router.get("/candidates", response_model=list[RiskCandidateRecord])
def list_candidates():
    """List all registered candidate molecules available for risk assessment."""
    return molecular_risk_service.list_candidates()


@router.get("/candidates/{candidate_id}", response_model=RiskCandidateRecord)
def get_candidate(candidate_id: str):
    """Retrieve details and descriptors for a specific candidate ID."""
    candidate = molecular_risk_service.get_candidate(candidate_id)
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate '{candidate_id}' not found in registry.",
        )
    return candidate


@router.post("/analyze", response_model=MolecularRiskReport)
def run_risk_analysis(request: RiskAnalyzeRequest):
    """
    Run candidate-specific risk assessment across 5 independent dimensions.

    Enforces manual trigger only and prevents simultaneous duplicate runs.
    """
    if not request.manual_trigger:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Automated risk execution is disabled. Risk analysis requires manual user selection.",
        )

    try:
        report = molecular_risk_service.run_analysis(
            candidate_id=request.candidate_id,
            smiles=request.smiles,
            drug_name=request.drug_name,
            category=request.category,
            source=request.source,
            config=request.config,
            manual_trigger=request.manual_trigger,
            run_async=request.run_async,
        )
        return report
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Risk analysis execution error: {str(exc)}",
        ) from exc


@router.get("/reports", response_model=list[MolecularRiskReport])
def list_reports(candidate_id: str | None = Query(default=None)):
    """Retrieve all historical risk assessment reports, optionally filtered by candidate ID."""
    return molecular_risk_service.list_reports(candidate_id=candidate_id)


@router.get("/reports/{report_id}", response_model=MolecularRiskReport)
def get_report(report_id: str):
    """Retrieve a specific risk report by ID."""
    report = molecular_risk_service.get_report(report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report '{report_id}' not found.",
        )
    return report


@router.get("/reports/{report_id}/status")
def get_report_status(report_id: str):
    """Check the real-time execution status of an active or completed risk analysis."""
    report = molecular_risk_service.get_report(report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report '{report_id}' not found.",
        )
    return {
        "report_id": report.report_id,
        "candidate_id": report.candidate_id,
        "execution_status": report.execution_status,
        "progress_percent": report.progress_percent,
        "current_stage": report.current_stage,
        "completed_at": report.completed_at,
        "runtime_ms": report.runtime_ms,
    }


@router.post("/reports/{report_id}/cancel", response_model=CancelResponse)
def cancel_report(report_id: str):
    """Cooperatively cancel an actively running risk analysis."""
    success = molecular_risk_service.cancel_report(report_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Active report '{report_id}' not found or already completed.",
        )
    return CancelResponse(
        report_id=report_id,
        cancelled=True,
        message=f"Risk analysis '{report_id}' cancellation signal sent.",
    )
