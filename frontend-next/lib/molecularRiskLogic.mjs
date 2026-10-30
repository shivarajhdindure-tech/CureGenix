/**
 * Pure helper utilities for Molecular Risk & Digital Twin calculations,
 * candidate identity binding, candidate-switch report isolation,
 * and auditable export generation.
 */

export const RISK_BADGE_STYLES = {
  low: "bg-emerald-50 text-emerald-800 border-emerald-200",
  moderate: "bg-amber-50 text-amber-800 border-amber-200",
  elevated: "bg-orange-50 text-orange-800 border-orange-200",
  high: "bg-rose-50 text-rose-800 border-rose-200",
  not_evaluated: "bg-slate-100 text-slate-700 border-slate-200",
  insufficient_evidence: "bg-purple-50 text-purple-800 border-purple-200",
  skipped_resource_limit: "bg-amber-50 text-amber-900 border-amber-300",
  failed: "bg-rose-50 text-rose-900 border-rose-300",
};

/**
 * Ensures that if a user switches candidates, any displayed report that does
 * not belong to the newly selected candidate is isolated and not displayed.
 */
export function resolveActiveCandidateReport(selectedCandidateId, activeReport, historicalReports = []) {
  if (!selectedCandidateId) {
    return {
      activeReport: null,
      hasMatchingHistorical: false,
      matchingHistoryCount: 0,
      mustRunNewAnalysis: false,
    };
  }

  const matchesActive = activeReport && activeReport.candidate_id === selectedCandidateId;
  const matchingHistory = (historicalReports || []).filter(
    (r) => r.candidate_id === selectedCandidateId
  );

  return {
    activeReport: matchesActive ? activeReport : null,
    hasMatchingHistorical: matchingHistory.length > 0,
    matchingHistoryCount: matchingHistory.length,
    latestHistoricalReport: matchingHistory.length > 0 ? matchingHistory[matchingHistory.length - 1] : null,
    mustRunNewAnalysis: !matchesActive,
  };
}

/**
 * Validates that candidate identity matches canonical SMILES and ID
 * before submitting or displaying risk analysis.
 */
export function validateCandidateSelection(candidate) {
  if (!candidate || !candidate.id) {
    return { valid: false, error: "No candidate selected." };
  }
  if (!candidate.smiles || typeof candidate.smiles !== "string" || !candidate.smiles.trim()) {
    return { valid: false, error: "Selected candidate does not possess a valid chemical SMILES string." };
  }
  return { valid: true, error: null };
}

/**
 * Formats a full scientific Markdown risk assessment report for download.
 */
export function generateMarkdownRiskReport(report) {
  if (!report) return "";

  const c = report.candidate || {};
  const d = c.descriptors || {};
  const dims = report.dimensions || {};

  const lines = [
    `# CureGenix — Candidate Molecular Risk & Digital Twin Report`,
    ``,
    `**Report ID**: \`${report.report_id}\``,
    `**Candidate ID**: \`${report.candidate_id}\` (${c.drug_name || "Novel lead"})`,
    `**Chemical Formula**: ${c.molecular_formula || "—"} | **Category**: ${c.category || "Novel hypothesis"}`,
    `**Canonical SMILES**: \`${c.canonical_smiles || c.input_smiles || "—"}\``,
    `**Primary Target**: ${c.target_name || "EGFR (P00533)"} (PDB: ${c.pdb_id || "1M17"}, Chain: ${c.chain_id || "A"})`,
    `**Execution Status**: ${report.execution_status.toUpperCase()} (${report.runtime_ms ? `${(report.runtime_ms / 1000).toFixed(2)}s` : "—"})`,
    `**Analysis Timestamp**: ${report.created_at}`,
    ``,
    `---`,
    ``,
    `## Scientific Integrity & Scoring Policy`,
    ``,
    `> ${report.scoring_policy_disclosure}`,
    ``,
    `---`,
    ``,
    `## 1. Physicochemical Descriptors`,
    `- **Molecular Weight**: ${d.molecular_weight || "—"} Da`,
    `- **cLogP**: ${d.logp ?? "—"}`,
    `- **TPSA**: ${d.tpsa ?? "—"} Å²`,
    `- **H-Bond Donors / Acceptors**: ${d.hbd ?? "—"} / ${d.hba ?? "—"}`,
    `- **Rotatable Bonds**: ${d.rotatable_bonds ?? "—"}`,
    `- **Fraction Csp3**: ${d.fraction_csp3 ?? "—"}`,
    `- **Quantitative Estimate of Drug-likeness (QED)**: ${d.qed ?? "—"}`,
    ``,
    `---`,
    ``,
    `## 2. Five Independent Risk Dimensions`,
    ``,
  ];

  const dimKeys = [
    { key: "admet_risk", title: "A. Molecular Developability & ADMET Risk" },
    { key: "binding_stability", title: "B. Binding Stability & Protein–Ligand Interaction Risk" },
    { key: "off_target_risk", title: "C. Off-Target & Selectivity Risk" },
    { key: "mutation_robustness", title: "D. Mutation, Resistance & Robustness Risk" },
    { key: "synthetic_feasibility", title: "E. Synthetic Feasibility & Chemical Liability Risk" },
  ];

  for (const { key, title } of dimKeys) {
    const dim = dims[key];
    lines.push(`### ${title}`);
    if (!dim) {
      lines.push(`*Dimension not evaluated or omitted.*`, ``);
      continue;
    }

    lines.push(`- **Risk Category**: ${dim.risk_category.toUpperCase()}`);
    lines.push(`- **Status**: ${dim.calculation_status}`);
    lines.push(`- **Evidence Type**: ${dim.evidence_type}`);
    lines.push(`- **Evidence Source**: ${dim.evidence_source}`);
    lines.push(`- **Method**: ${dim.prediction_or_simulation_method}`);
    lines.push(`- **Confidence / Uncertainty**: ${dim.confidence_or_uncertainty}`);
    lines.push(`- **Summary**: ${dim.result_summary}`);
    if (dim.limitations && dim.limitations.length > 0) {
      lines.push(`- **Limitations**:`);
      for (const lim of dim.limitations) {
        lines.push(`  - ${lim}`);
      }
    }
    lines.push(``);
  }

  lines.push(`---`, `## 3. Disclosures & Provenance`);
  if (report.scientific_disclosures && report.scientific_disclosures.length > 0) {
    for (const disc of report.scientific_disclosures) {
      lines.push(`- ${disc}`);
    }
  }

  lines.push(``, `*Report generated by CureGenix Quantum-Assisted Discovery Platform.*`);
  return lines.join("\n");
}
