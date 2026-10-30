"""Pydantic data models for the Molecular Risk & Digital Twin workspace.

Enforces strict candidate identity binding, explicit separation of the five risk
dimensions (without arbitrary combined risk scores), and clear distinction
between measured, predicted, simulated, heuristic, and unavailable evidence.
"""

from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field


EvidenceType = Literal[
    "measured",
    "predicted",
    "simulated",
    "computed_descriptor",
    "rule_based_heuristic",
    "unavailable",
]

CalculationStatus = Literal[
    "completed",
    "partial",
    "prepared_only",
    "not_configured",
    "not_evaluated",
    "skipped_resource_limit",
    "failed",
    "cancelled",
]

RiskCategory = Literal[
    "low",
    "moderate",
    "elevated",
    "high",
    "not_evaluated",
    "insufficient_evidence",
    "skipped_resource_limit",
    "failed",
]


class RiskAnalysisConfig(BaseModel):
    """User-configurable analysis settings and resource guardrails."""

    enable_admet: bool = True
    enable_binding_stability: bool = True
    enable_off_target: bool = True
    enable_mutation_robustness: bool = True
    enable_synthetic_feasibility: bool = True
    target_uniprot_id: str = Field(default="P00533", min_length=1, max_length=32)
    target_name: str = Field(
        default="Epidermal growth factor receptor (EGFR)", max_length=200
    )
    target_pdb_id: str | None = Field(default="1M17", max_length=16)
    target_chain_id: str | None = Field(default="A", max_length=4)
    max_heavy_atoms: int | None = Field(default=None, ge=1, le=500)
    max_total_atoms: int | None = Field(default=None, ge=1, le=1000)
    max_conformer_iterations: int = Field(default=200, ge=10, le=2000)
    subprocess_timeout_seconds: float = Field(default=10.0, ge=1.0, le=120.0)
    attempt_external_md: bool = False
    attempt_external_retrosynthesis: bool = False


class RiskAnalyzeRequest(BaseModel):
    """Explicit manual request to analyze a single selected candidate."""

    candidate_id: str = Field(min_length=1, max_length=128)
    smiles: str | None = Field(default=None, max_length=2000)
    drug_name: str | None = Field(default=None, max_length=200)
    category: str | None = Field(default=None, max_length=64)
    source: str | None = Field(default=None, max_length=200)
    manual_trigger: bool = Field(
        default=True,
        description="Must be True; automated batch risk execution is prohibited.",
    )
    run_async: bool = Field(
        default=False,
        description="If True, schedules execution in background thread and returns report_id immediately.",
    )
    config: RiskAnalysisConfig = Field(default_factory=RiskAnalysisConfig)


class CandidateDescriptorSummary(BaseModel):
    """Standard 2D physicochemical descriptors computed via RDKit."""

    molecular_weight: float
    exact_molecular_weight: float
    logp: float
    tpsa: float
    hbd: int
    hba: int
    rotatable_bonds: int
    heavy_atom_count: int
    total_atom_count: int
    ring_count: int
    aromatic_ring_count: int
    fraction_csp3: float
    qed: float
    molar_refractivity: float
    formal_charge: int


class RiskCandidateRecord(BaseModel):
    """Validated candidate identity record bound to every risk report."""

    candidate_id: str
    drug_name: str
    canonical_smiles: str
    input_smiles: str
    inchi_key: str
    molecular_formula: str
    category: str = "novel"
    target_uniprot_id: str = "P00533"
    target_name: str = "Epidermal growth factor receptor (EGFR)"
    pdb_id: str | None = "1M17"
    chain_id: str | None = "A"
    source: str = "CureGenix Candidate Registry"
    verification_status: str = "not_verified"
    target_association_verified: bool = False
    descriptors: CandidateDescriptorSummary
    provenance: dict[str, Any] = Field(default_factory=dict)


class DimensionAssessment(BaseModel):
    """Independent assessment for one of the five required risk dimensions."""

    dimension_id: str
    title: str
    risk_category: RiskCategory
    result_summary: str
    evidence_source: str
    evidence_type: EvidenceType
    prediction_or_simulation_method: str
    confidence_or_uncertainty: str
    uncertainty_details: dict[str, Any] = Field(default_factory=dict)
    calculation_status: CalculationStatus
    model_version: str
    timestamp: str
    limitations: list[str] = Field(default_factory=list)
    applicability_domain: dict[str, Any] = Field(default_factory=dict)
    details: dict[str, Any] = Field(default_factory=dict)


class MolecularRiskReport(BaseModel):
    """Candidate-specific integrated risk report across five independent dimensions."""

    report_id: str
    candidate_id: str
    candidate: RiskCandidateRecord
    execution_status: Literal[
        "queued",
        "running",
        "completed",
        "partial",
        "failed",
        "skipped_resource_limit",
        "cancelled",
    ]
    progress_percent: int = Field(ge=0, le=100)
    current_stage: str
    manual_trigger_verified: bool = True
    combined_risk_score: None = None
    scoring_policy_disclosure: str = (
        "CureGenix reports five independent risk dimensions without computing an "
        "arbitrary combined risk score. Missing, skipped, or unconfigured analyses "
        "are reported separately and never treated as low risk."
    )
    created_at: str
    completed_at: str | None = None
    runtime_ms: int | None = None
    config: RiskAnalysisConfig
    resource_assessment: dict[str, Any] = Field(default_factory=dict)
    dimensions: dict[str, DimensionAssessment] = Field(default_factory=dict)
    provenance: dict[str, Any] = Field(default_factory=dict)
    scientific_disclosures: list[str] = Field(default_factory=list)
