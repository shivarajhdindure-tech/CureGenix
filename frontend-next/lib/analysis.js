// Helpers for safely reading the /api/discover response.
// Every field here was verified against backend/orchestrator.py and the agent
// sources. Nothing is invented: missing data stays missing.
import { deriveCandidateTieDisplay } from "./candidateTransparency.mjs";

export const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// The real quantum run takes ~4 minutes on CPU hosting. Allow far more.
export const REQUEST_TIMEOUT_MS = 15 * 60 * 1000;

// Backend agent name -> display label. Order matches the backend pipeline.
export const STAGES = [
  {
    agent: "Target Agent",
    label: "Target Identification",
    blurb: "Parses the PDB structure and resolves the protein target",
  },
  {
    agent: "Research Agent",
    label: "Research",
    blurb: "Checks structure sources and searches for known binders",
  },
  {
    agent: "Molecule Agent",
    label: "Candidate Generation",
    blurb: "Generates novel analogs and collects reference compounds",
  },
  {
    agent: "Quantum Analysis Agent",
    label: "Quantum Analysis",
    blurb: "VQE-based active-space calculation on novel candidates",
  },
  {
    agent: "Screening Agent",
    label: "Molecular Screening",
    blurb: "Drug-likeness, BBB permeability and toxicity screening",
  },
  {
    agent: "Risk Agent",
    label: "Risk Analysis",
    blurb: "Computational risk profile and structural alerts",
  },
  {
    agent: "Decision Agent",
    label: "Final Prioritization",
    blurb: "Ranks candidates by risk-adjusted screening score",
  },
];

export const isNum = (v) => typeof v === "number" && Number.isFinite(v);

export function fmt(v, digits = 4) {
  return isNum(v) ? v.toFixed(digits) : "—";
}

export function fmtClock(totalSeconds) {
  const s = Math.max(0, Math.floor(totalSeconds));
  const mm = String(Math.floor(s / 60)).padStart(2, "0");
  const ss = String(s % 60).padStart(2, "0");
  return `${mm}:${ss}`;
}

export function fmtBytes(bytes) {
  if (!isNum(bytes)) return "";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

export function fmtSeconds(ms) {
  return isNum(ms) ? `${(ms / 1000).toFixed(ms < 10000 ? 2 : 1)}s` : "—";
}

// ---------------------------------------------------------------------------
// PDB validation (client side, mirrors backend: .pdb only)
// ---------------------------------------------------------------------------

export async function validatePdb(file) {
  if (!file) return { status: "invalid", message: "No file selected." };

  if (!file.name.toLowerCase().endsWith(".pdb")) {
    return {
      status: "invalid",
      message: "Unsupported file type. Please upload a .pdb file.",
    };
  }
  if (file.size === 0) {
    return { status: "invalid", message: "This file is empty." };
  }

  try {
    const head = await file.slice(0, 5 * 1024 * 1024).text();
    if (!/^(ATOM  |HETATM)/m.test(head)) {
      return {
        status: "invalid",
        message:
          "No ATOM or HETATM records found. This does not look like a PDB structure file.",
      };
    }
  } catch {
    return { status: "invalid", message: "The file could not be read." };
  }

  return { status: "valid", message: "Valid PDB structure" };
}

// ---------------------------------------------------------------------------
// Response derivation
// ---------------------------------------------------------------------------

const BAD_NAMES = new Set(["", "N/A", "n/a", "NA"]);

export function deriveResults(result) {
  const steps = Array.isArray(result?.steps) ? result.steps : [];
  const step = (name) => steps.find((s) => s?.agent_name === name);

  const quantumStep = step("Quantum Analysis Agent");
  const riskStep = step("Risk Agent");
  const decisionStep = step("Decision Agent");

  const quantumData = quantumStep?.data || {};
  const riskData = riskStep?.data || {};
  const decisionData = decisionStep?.data || {};

  const molecules = Array.isArray(quantumData.molecules)
    ? quantumData.molecules
    : [];
  const quantumByName = {};
  molecules.forEach((m) => {
    if (m?.name) quantumByName[m.name] = m;
  });

  const hasVqe = (m) =>
    m?.quantum_analysis?.status === "success" &&
    isNum(m?.quantum_analysis?.vqe?.electronic_energy_hartree);

  const vqeMolecules = molecules.filter(hasVqe);
  const lightMolecules = molecules.filter(
    (m) =>
      m?.quantum_analysis?.status === "success" &&
      m?.quantum_analysis?.mode === "lightweight",
  );
  const failedMolecules = molecules.filter(
    (m) => m?.quantum_analysis?.status === "failed",
  );
  const resourceSkippedMolecules = molecules.filter(
    (m) => m?.quantum_analysis?.status === "skipped_resource_limit",
  );

  const recommendations = Array.isArray(decisionData.recommendations)
    ? decisionData.recommendations
    : Array.isArray(result?.decisions)
      ? result.decisions
      : [];

  const demonstrationReferences = Array.isArray(
    decisionData.demonstration_references,
  )
    ? decisionData.demonstration_references
    : [];

  const highlights = result?.highlights || decisionData.highlights || {};
  const bestNovelRaw = highlights.best_novel_candidate;
  const bestNovelId = BAD_NAMES.has(bestNovelRaw ?? "") ? null : bestNovelRaw;

  const toCandidate = (r, demonstrationOnly = false) => ({
    id: r.drug_name,
    smiles: r.smiles,
    category: r.category,
    rank: demonstrationOnly ? null : r.rank,
    adjustedScore: r.adjusted_score,
    compositeScore: r.composite_score,
    riskLevel: r.risk_level,
    safetyEvidenceStatus: r.safety_evidence_status || "insufficient",
    structuralAlertCount: r.structural_alert_count ?? null,
    structuralAlerts: Array.isArray(r.structural_alerts)
      ? r.structural_alerts
      : [],
    riskDetails: r.risk_details || "",
    riskFlags: Array.isArray(r.risk_flags) ? r.risk_flags : [],
    confidence: r.confidence,
    screening: r.screening_details || null,
    reasoning: r.reasoning || "",
    verificationStatus: r.verification_status || "not_verified",
    targetAssociationVerified: r.target_association_verified === true,
    candidateMetadata: r.candidate_metadata || null,
    demonstrationOnly,
  });

  const rankedSource = recommendations
    .filter((r) => r.category !== "mock")
    .map((r) => toCandidate(r));

  const mockSource = [
    ...demonstrationReferences,
    ...recommendations.filter((r) => r.category === "mock"),
  ]
    .filter(
      (candidate, index, all) =>
        all.findIndex((item) => item.drug_name === candidate.drug_name) ===
        index,
    )
    .map((candidate) => toCandidate(candidate, true));

  const source = rankedSource.length
    ? rankedSource
    : recommendations.length
      ? []
      : molecules
          .filter((m) => m.category !== "mock")
          .map((m) => ({
            id: m.name,
            smiles: m.smiles,
            category: m.category,
            candidateMetadata: m.candidate_metadata || null,
          }));

  const unrankedCandidates = source.map((c) => {
    const q = quantumByName[c.id]?.quantum_analysis || null;
    let quantumState = "none";
    if (q) {
      if (q.status === "success" && isNum(q.vqe?.electronic_energy_hartree))
        quantumState = "vqe";
      else if (q.status === "success" && q.mode === "lightweight")
        quantumState = "lightweight";
      else if (q.status === "skipped_resource_limit") quantumState = "resource_skipped";
      else if (q.status === "skipped") quantumState = "skipped";
      else if (q.status === "failed") quantumState = "failed";
    }
    return {
      ...c,
      quantum: q,
      quantumState,
      isNovel: c.category === "novel",
      isBestNovel: bestNovelId != null && c.id === bestNovelId,
    };
  });

  const tieDisplay = deriveCandidateTieDisplay(unrankedCandidates, bestNovelId);
  const candidates = tieDisplay.candidates;

  const demonstrationCandidates = mockSource.map((c) => ({
    ...c,
    quantum: quantumByName[c.id]?.quantum_analysis || null,
    quantumState: "skipped",
    isNovel: false,
    isBestNovel: false,
  }));

  const riskDistribution = riskData.risk_distribution || null;
  const proteinInfo = result?.protein_info || {};

  return {
    steps,
    quantumStep,
    quantumData,
    vqeMolecules,
    lightMolecules,
    failedMolecules,
    resourceSkippedMolecules,
    candidates,
    recommendations,
    highlights,
    bestNovelId: tieDisplay.bestNovelId,
    bestNovel: tieDisplay.bestNovel,
    bestNovelCandidates: tieDisplay.bestNovelCandidates,
    bestNovelIsTie: tieDisplay.bestNovelIsTie,
    hasScoreTies: tieDisplay.hasScoreTies,
    topScoreIsTie: tieDisplay.topScoreIsTie,
    topScoreCandidateIds: tieDisplay.topScoreCandidateIds,
    topCandidate: result?.top_candidate
      ? {
          ...result.top_candidate,
          scoreTie: tieDisplay.topScoreIsTie,
          tiedCandidateIds: tieDisplay.topScoreCandidateIds,
        }
      : null,
    riskDistribution,
    riskStep,
    decisionStep,
    proteinInfo,
    durationMs: result?.pipeline_duration_ms,
    summaryCounts: {
      analyzed: isNum(quantumData.total_candidates)
        ? quantumData.total_candidates
        : candidates.length,
      quantumEvaluated: vqeMolecules.length,
      quantumTargeted: isNum(quantumData.quantum_candidates)
        ? quantumData.quantum_candidates
        : null,
      quantumSuccessful: isNum(quantumData.successful) ? quantumData.successful : vqeMolecules.length + lightMolecules.length,
      quantumFailed: isNum(quantumData.failed) ? quantumData.failed : failedMolecules.length,
      resourceSkipped: isNum(quantumData.skipped_resource_limit)
        ? quantumData.skipped_resource_limit
        : resourceSkippedMolecules.length,
    },
    demonstrationCandidates,
  };
}
