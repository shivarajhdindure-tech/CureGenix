import assert from "node:assert/strict";
import test from "node:test";

import {
  resolveActiveCandidateReport,
  validateCandidateSelection,
  generateMarkdownRiskReport,
} from "../lib/molecularRiskLogic.mjs";

test("candidate selection validation rejects missing candidate or empty SMILES", () => {
  assert.equal(validateCandidateSelection(null).valid, false);
  assert.equal(validateCandidateSelection({ id: "C1" }).valid, false);
  assert.equal(validateCandidateSelection({ id: "C1", smiles: "   " }).valid, false);
  assert.equal(validateCandidateSelection({ id: "C1", smiles: "CCO" }).valid, true);
});

test("candidate switching isolates previous report and requires new analysis", () => {
  const activeReport = { report_id: "REP-1", candidate_id: "GEN-A" };
  const history = [
    activeReport,
    { report_id: "REP-2", candidate_id: "GEN-B" },
  ];

  // If selected candidate is GEN-A, activeReport matches
  const resA = resolveActiveCandidateReport("GEN-A", activeReport, history);
  assert.equal(resA.activeReport.report_id, "REP-1");
  assert.equal(resA.mustRunNewAnalysis, false);

  // If user switches to GEN-B, previous report GEN-A is NOT displayed
  const resB = resolveActiveCandidateReport("GEN-B", activeReport, history);
  assert.equal(resB.activeReport, null);
  assert.equal(resB.hasMatchingHistorical, true);
  assert.equal(resB.matchingHistoryCount, 1);
  assert.equal(resB.latestHistoricalReport.report_id, "REP-2");
  assert.equal(resB.mustRunNewAnalysis, true);

  // If user switches to unanalyzed GEN-C
  const resC = resolveActiveCandidateReport("GEN-C", activeReport, history);
  assert.equal(resC.activeReport, null);
  assert.equal(resC.hasMatchingHistorical, false);
  assert.equal(resC.mustRunNewAnalysis, true);
});

test("markdown report generator formats candidate identity, 5 dimensions, and scientific disclosures", () => {
  const mockReport = {
    report_id: "RISK-CHEMBL553-12345",
    candidate_id: "CHEMBL553",
    candidate: {
      drug_name: "Erlotinib",
      canonical_smiles: "COCCOc1cc2ncnc(Nc3cccc(c3)C#C)c2cc1OCCOC",
      molecular_formula: "C22H23N3O4",
      category: "approved",
      target_name: "EGFR",
      pdb_id: "1M17",
      chain_id: "A",
      descriptors: {
        molecular_weight: 393.44,
        logp: 2.8,
        tpsa: 74.7,
        hbd: 1,
        hba: 7,
      },
    },
    execution_status: "completed",
    runtime_ms: 1250,
    created_at: "2026-10-30T12:00:00Z",
    scoring_policy_disclosure: "CureGenix reports five independent risk dimensions without computing an arbitrary combined risk score.",
    dimensions: {
      admet_risk: {
        risk_category: "low",
        calculation_status: "completed",
        evidence_type: "computed_descriptor",
        evidence_source: "RDKit",
        prediction_or_simulation_method: "QSPR descriptors",
        confidence_or_uncertainty: "Moderate",
        result_summary: "Acceptable drug-like properties",
        limitations: ["No in vitro confirmation"],
      },
      binding_stability: {
        risk_category: "insufficient_evidence",
        calculation_status: "prepared_only",
        evidence_type: "simulated",
        evidence_source: "RDKit ETKDGv3",
        prediction_or_simulation_method: "Static cleft mapping",
        confidence_or_uncertainty: "Limited (No MD)",
        result_summary: "Conformer prepared; dynamic MD not run",
        limitations: ["Dynamic trajectory not configured"],
      },
    },
    scientific_disclosures: [
      "Predictions do not establish clinical safety.",
    ],
  };

  const md = generateMarkdownRiskReport(mockReport);
  assert.match(md, /Candidate Molecular Risk & Digital Twin Report/);
  assert.match(md, /RISK-CHEMBL553-12345/);
  assert.match(md, /COCCOc1cc2ncnc/);
  assert.match(md, /scoring_policy_disclosure|arbitrary combined risk score/i);
  assert.match(md, /A\. Molecular Developability & ADMET Risk/);
  assert.match(md, /B\. Binding Stability & Protein–Ligand Interaction Risk/);
  assert.match(md, /Dynamic trajectory not configured/);
});
