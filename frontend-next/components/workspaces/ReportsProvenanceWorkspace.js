"use client";

import { useState } from "react";
import TechnicalDetails from "../TechnicalDetails";
import {
  CANONICAL_EXPERIMENT_RESULTS,
  SUPPORTING_DIAGNOSTIC_ARTIFACTS,
  SCIENTIFIC_DISCLOSURES,
  downloadSingleRecordJson,
  downloadSupportingArtifactJson,
  downloadConsolidatedResultsJson,
  downloadExperimentSummaryCsv,
} from "@/lib/experimentResultsData";

const SAVED_ARTIFACTS = [
  {
    name: "EGFR Scaffold Validation Report",
    path: "benchmark_reports/egfr_regression/scaffold_validation/report.md",
    format: "Markdown",
    size: "6.8 KB",
    description: "Detailed scientific report on 5-split repeated Murcko scaffold validation across 2,995 EGFR compounds.",
    status: "Verified On Disk",
    type: "report",
  },
  {
    name: "Scaffold Validation Structured Metrics",
    path: "benchmark_reports/egfr_regression/scaffold_validation/results.json",
    format: "JSON",
    size: "18.4 KB",
    description: "Complete machine-readable test and validation metrics, per-split scores, hyperparameters, and environment info.",
    status: "Verified On Disk",
    type: "data",
  },
  {
    name: "Split Membership Audit Trail",
    path: "benchmark_reports/egfr_regression/scaffold_validation/split_membership_audit.csv",
    format: "CSV",
    size: "245.2 KB",
    description: "Auditable per-compound scaffold group assignment verifying 0.00% scaffold overlap across all 5 seeds.",
    status: "Verified On Disk",
    type: "audit",
  },
  {
    name: "Matched 16D Pilot Comparison Report",
    path: "benchmark_reports/egfr_regression/classical_quantum_comparison_16d_pilot/comparison_report.md",
    format: "Markdown",
    size: "8.2 KB",
    description: "Methodological comparison between 16D quantum-kernel SVR and classical baselines on matched test split (seed 42).",
    status: "Verified On Disk",
    type: "report",
  },
  {
    name: "Matched 16D Pilot Results JSON",
    path: "benchmark_reports/egfr_regression/classical_quantum_comparison_16d_pilot/comparison_results.json",
    format: "JSON",
    size: "12.1 KB",
    description: "Exact MAE, RMSE, and R2 values for quantum and classical models on the single matched pilot split.",
    status: "Verified On Disk",
    type: "data",
  },
  {
    name: "Classical Pilot Test Predictions",
    path: "benchmark_reports/egfr_regression/classical_quantum_comparison_16d_pilot/test_predictions_classical.csv",
    format: "CSV",
    size: "48.6 KB",
    description: "Per-compound test predictions for RBF-SVR and Random Forest on the 598 held-out pilot test molecules.",
    status: "Verified On Disk",
    type: "predictions",
  },
];

export default function ReportsProvenanceWorkspace({ derived }) {
  const [selectedArtifact, setSelectedArtifact] = useState(SAVED_ARTIFACTS[0]);
  const [experimentFilter, setExperimentFilter] = useState("all"); // "all" | "hardware" | "local"
  const [expandedExperimentId, setExpandedExperimentId] = useState(null);
  const [expandedSupportingId, setExpandedSupportingId] = useState(null);
  const [downloadNotice, setDownloadNotice] = useState("");

  function triggerNotice(msg) {
    setDownloadNotice(msg);
    setTimeout(() => {
      setDownloadNotice((prev) => (prev === msg ? "" : prev));
    }, 4000);
  }

  const filteredExperiments = CANONICAL_EXPERIMENT_RESULTS.filter((exp) => {
    if (experimentFilter === "hardware") {
      return exp.executionType.includes("IBM") || exp.executionType.includes("Hardware");
    }
    if (experimentFilter === "local") {
      return exp.executionType.includes("Local");
    }
    return true;
  });

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-slate-200 pb-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-slate-900 sm:text-2xl">
            Reports &amp; Provenance Vault
          </h2>
          <p className="mt-1 text-sm text-slate-600">
            Persistent artifact audit trails, verified quantum hardware experiment results, benchmark reports, and environment provenance.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="rounded-full bg-teal-50 border border-teal-200 px-3 py-1 text-xs font-semibold text-teal-800">
            6 Benchmark Artifacts
          </span>
          <span className="rounded-full bg-indigo-50 border border-indigo-200 px-3 py-1 text-xs font-semibold text-indigo-800">
            6 Canonical Experiment Runs
          </span>
        </div>
      </div>

      {/* Download Notice Toast */}
      {downloadNotice && (
        <div className="rounded-xl border border-teal-200 bg-teal-50 p-4 shadow-sm flex items-center justify-between transition-all animate-fadeIn">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-teal-600 text-white">
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <div>
              <p className="text-xs font-bold text-teal-900">Export Generated Successfully</p>
              <p className="text-xs text-teal-700">{downloadNotice}</p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => setDownloadNotice("")}
            className="text-xs font-semibold text-teal-700 hover:text-teal-900"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* =========================================================================
          SECTION 1: Quantum Experiment & Hardware Results Vault (Download Center)
          ========================================================================= */}
      <div className="rounded-xl border border-slate-200/90 bg-white p-6 shadow-sm">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 border-b border-slate-100 pb-5">
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-semibold text-slate-900 sm:text-lg">
                Quantum Experiment &amp; Hardware Results
              </h3>
              <span className="rounded bg-indigo-100 text-indigo-800 border border-indigo-200 px-2 py-0.5 text-[10px] font-bold tracking-wider uppercase">
                IBM Fez &middot; PySCF WSL
              </span>
            </div>
            <p className="mt-1 text-xs text-slate-500 max-w-2xl">
              Downloadable canonical experiment runs executed on IBM Quantum physical hardware (<code className="font-mono text-indigo-700">ibm_fez</code>) and local exact reference simulations. All metrics reflect immutable on-disk artifacts in <code className="font-mono text-slate-700">experiments/ibm_results/</code>.
            </p>
          </div>

          {/* Top-Level Export Action Buttons */}
          <div className="flex flex-wrap items-center gap-2.5">
            <button
              type="button"
              onClick={() => {
                downloadConsolidatedResultsJson();
                triggerNotice("Downloaded consolidated results as curegenix_consolidated_experiment_results.json");
              }}
              className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-3.5 py-2 text-xs font-semibold text-white shadow-sm hover:bg-indigo-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 transition"
              title="Download consolidated JSON containing all verified experiment records, parameters, and scientific disclosures"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              <span>Download Consolidated JSON</span>
            </button>

            <button
              type="button"
              onClick={() => {
                downloadExperimentSummaryCsv();
                triggerNotice("Downloaded tabular experiment summary as curegenix_experiment_summary.csv");
              }}
              className="inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 shadow-sm hover:bg-slate-50 hover:border-slate-400 focus:outline-none focus-visible:ring-2 focus-visible:ring-teal-500 transition"
              title="Download structured summary table in CSV format with UTF-8 encoding"
            >
              <svg className="w-4 h-4 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <span>Download Summary CSV</span>
            </button>
          </div>
        </div>

        {/* Experiment KPI Ribbon */}
        <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
          <div className="rounded-lg border border-slate-100 bg-slate-50/80 p-3">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Canonical Records</span>
            <p className="font-data mt-1 text-lg font-bold text-slate-900">{CANONICAL_EXPERIMENT_RESULTS.length}</p>
            <p className="text-[10px] text-slate-500">Allowlisted on-disk files</p>
          </div>
          <div className="rounded-lg border border-indigo-100 bg-indigo-50/40 p-3">
            <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-700">IBM Fez QPU Runs</span>
            <p className="font-data mt-1 text-lg font-bold text-indigo-900">4</p>
            <p className="text-[10px] text-indigo-700">Physical Heron processor</p>
          </div>
          <div className="rounded-lg border border-teal-100 bg-teal-50/40 p-3">
            <span className="text-[10px] font-bold uppercase tracking-wider text-teal-700">Exact / VQE References</span>
            <p className="font-data mt-1 text-lg font-bold text-teal-900">2</p>
            <p className="text-[10px] text-teal-700">Local ground truth baselines</p>
          </div>
          <div className="rounded-lg border border-amber-100 bg-amber-50/40 p-3">
            <span className="text-[10px] font-bold uppercase tracking-wider text-amber-700">Diagnostic Artifacts</span>
            <p className="font-data mt-1 text-lg font-bold text-amber-900">{SUPPORTING_DIAGNOSTIC_ARTIFACTS.length}</p>
            <p className="text-[10px] text-amber-700">Intermediate specifications</p>
          </div>
        </div>

        {/* Filter Tabs */}
        <div className="mt-5 flex items-center justify-between flex-wrap gap-2">
          <div className="inline-flex rounded-lg border border-slate-200 bg-slate-100 p-0.5 text-xs">
            <button
              type="button"
              onClick={() => setExperimentFilter("all")}
              className={`rounded-md px-3 py-1 font-medium transition ${
                experimentFilter === "all"
                  ? "bg-white text-slate-900 shadow-sm"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              All Records ({CANONICAL_EXPERIMENT_RESULTS.length})
            </button>
            <button
              type="button"
              onClick={() => setExperimentFilter("hardware")}
              className={`rounded-md px-3 py-1 font-medium transition ${
                experimentFilter === "hardware"
                  ? "bg-white text-indigo-900 shadow-sm font-semibold"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              IBM QPU Hardware (4)
            </button>
            <button
              type="button"
              onClick={() => setExperimentFilter("local")}
              className={`rounded-md px-3 py-1 font-medium transition ${
                experimentFilter === "local"
                  ? "bg-white text-teal-900 shadow-sm font-semibold"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Local Simulation &amp; VQE (2)
            </button>
          </div>

          <span className="text-xs text-slate-500 font-mono">
            Format: Native JSON &middot; Sanitized client-side Blob
          </span>
        </div>

        {/* Experiment Records List */}
        <div className="mt-4 space-y-3">
          {filteredExperiments.map((exp) => {
            const isExpanded = expandedExperimentId === exp.id;
            const isHardware = exp.executionType.includes("IBM") || exp.executionType.includes("Hardware");

            return (
              <div
                key={exp.id}
                className="rounded-xl border border-slate-200 bg-slate-50/60 p-4 transition hover:border-slate-300"
              >
                <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-3">
                  {/* Left Column: Metadata */}
                  <div className="space-y-1.5 flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-semibold text-sm text-slate-900">
                        {exp.name}
                      </span>

                      {/* Execution Type Tag */}
                      <span
                        className={`rounded px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider border ${
                          isHardware
                            ? "bg-indigo-50 text-indigo-800 border-indigo-200"
                            : "bg-teal-50 text-teal-800 border-teal-200"
                        }`}
                      >
                        {exp.executionType}
                      </span>

                      {/* Status / Hardware Fidelity Badge (Neutral / Amber for noisy hardware) */}
                      {exp.statusType === "hardware-noisy" ? (
                        <span className="rounded bg-amber-50 text-amber-800 border border-amber-300 px-2 py-0.5 text-[10px] font-semibold flex items-center gap-1">
                          <span className="h-1.5 w-1.5 rounded-full bg-amber-500" />
                          Physical QPU (Decoherence Observed)
                        </span>
                      ) : exp.statusType === "hardware-done" ? (
                        <span className="rounded bg-indigo-50 text-indigo-800 border border-indigo-200 px-2 py-0.5 text-[10px] font-semibold flex items-center gap-1">
                          <span className="h-1.5 w-1.5 rounded-full bg-indigo-500" />
                          QPU Done (256 Shots)
                        </span>
                      ) : exp.statusType === "diagnostic" ? (
                        <span className="rounded bg-slate-100 text-slate-700 border border-slate-300 px-2 py-0.5 text-[10px] font-semibold flex items-center gap-1">
                          <span className="h-1.5 w-1.5 rounded-full bg-slate-500" />
                          Circuit Diagnostic
                        </span>
                      ) : (
                        <span className="rounded bg-emerald-50 text-emerald-800 border border-emerald-200 px-2 py-0.5 text-[10px] font-semibold flex items-center gap-1">
                          <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                          {exp.status}
                        </span>
                      )}
                    </div>

                    <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-500">
                      <span>
                        Target: <strong className="text-slate-800 font-medium">{exp.targetOrMolecule}</strong>
                      </span>
                      <span>
                        Backend: <code className="font-mono text-slate-800 font-semibold">{exp.backend}</code>
                      </span>
                      {exp.jobId && (
                        <span>
                          Job ID: <code className="font-mono text-indigo-700">{exp.jobId}</code>
                        </span>
                      )}
                      <span>
                        Qubits: <strong className="font-data text-slate-800">{exp.qubits}</strong>
                      </span>
                      {exp.shots && (
                        <span>
                          Shots: <strong className="font-data text-slate-800">{exp.shots}</strong>
                        </span>
                      )}
                    </div>

                    {/* Metric Highlights Grid */}
                    <div className="mt-2 grid grid-cols-1 sm:grid-cols-3 gap-2 rounded-lg border border-slate-200/80 bg-white p-2.5 text-xs">
                      <div>
                        <span className="text-[10px] uppercase font-bold text-slate-500">{exp.primaryMetricLabel}</span>
                        <p className="font-data font-bold text-slate-900 mt-0.5 truncate">{exp.primaryMetricValue}</p>
                      </div>
                      <div>
                        <span className="text-[10px] uppercase font-bold text-slate-500">Reference Benchmark</span>
                        <p className="font-data text-slate-700 mt-0.5 truncate">{exp.referenceValue}</p>
                      </div>
                      <div>
                        <span className="text-[10px] uppercase font-bold text-slate-500">Uncertainty / Deviation</span>
                        <p className="font-data text-amber-700 font-medium mt-0.5 truncate">{exp.uncertaintyOrDelta}</p>
                      </div>
                    </div>

                    <p className="text-[11px] text-slate-600 italic">
                      &bull; {exp.summaryNotes}
                    </p>
                  </div>

                  {/* Right Column: Actions */}
                  <div className="flex sm:flex-col items-center sm:items-end justify-between sm:justify-start gap-2 shrink-0">
                    <button
                      type="button"
                      onClick={() => {
                        downloadSingleRecordJson(exp);
                        triggerNotice(`Downloaded ${exp.filename}`);
                      }}
                      className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-800 shadow-sm hover:bg-slate-50 hover:border-slate-400 focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 transition"
                      title={`Download individual JSON: ${exp.filename}`}
                    >
                      <svg className="w-3.5 h-3.5 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                      </svg>
                      <span>Download JSON</span>
                    </button>

                    <button
                      type="button"
                      onClick={() => setExpandedExperimentId(isExpanded ? null : exp.id)}
                      className="text-xs font-medium text-slate-600 hover:text-slate-900 underline underline-offset-2 flex items-center gap-1"
                    >
                      <span>{isExpanded ? "Hide Payload" : "Inspect Payload"}</span>
                      <span aria-hidden="true">{isExpanded ? "▴" : "▾"}</span>
                    </button>
                  </div>
                </div>

                {/* Collapsible Raw JSON & Limitation Inspector */}
                {isExpanded && (
                  <div className="mt-3 rounded-lg border border-slate-300 bg-slate-900 p-4 text-xs font-mono text-slate-200 space-y-3">
                    <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                      <span className="text-teal-400 font-bold">{exp.filename}</span>
                      <span className="text-slate-400">{exp.backend} &middot; {exp.executionType}</span>
                    </div>

                    <div>
                      <p className="text-[10px] uppercase font-bold text-amber-400 font-sans">
                        Scientific Disclosures &amp; Limitations:
                      </p>
                      <p className="text-slate-300 font-sans text-xs mt-1 leading-relaxed">
                        {exp.scientificLimitations}
                      </p>
                    </div>

                    <div>
                      <p className="text-[10px] uppercase font-bold text-slate-400 font-sans mb-1">
                        Verified Raw Payload Preview:
                      </p>
                      <pre className="overflow-x-auto max-h-56 p-2 rounded bg-slate-950 text-slate-300 text-[11px] leading-tight">
                        {JSON.stringify(exp.rawData, null, 2)}
                      </pre>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* =========================================================================
          SECTION 2: Supporting Diagnostic Artifacts (Separated from Canonical)
          ========================================================================= */}
      <div className="rounded-xl border border-slate-200/90 bg-white p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-slate-100 pb-4">
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-semibold text-slate-900">
                Supporting Diagnostic &amp; Hamiltonian Artifacts
              </h3>
              <span className="rounded bg-slate-100 text-slate-700 border border-slate-300 px-2 py-0.5 text-[10px] font-bold tracking-wider uppercase">
                Non-Canonical Intermediate Specifications
              </span>
            </div>
            <p className="mt-1 text-xs text-slate-500">
              Diagnostic input parameters, model circuit definitions, and operator decompositions. These artifacts provide technical provenance for hardware runs and are categorized separately from experimental evaluations.
            </p>
          </div>
          <span className="rounded-full bg-slate-100 border border-slate-300 px-3 py-1 text-xs font-semibold text-slate-700 shrink-0">
            {SUPPORTING_DIAGNOSTIC_ARTIFACTS.length} Intermediate Artifacts
          </span>
        </div>

        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          {SUPPORTING_DIAGNOSTIC_ARTIFACTS.map((artifact) => {
            const isExpanded = expandedSupportingId === artifact.id;

            return (
              <div
                key={artifact.id}
                className="rounded-xl border border-slate-200 bg-slate-50/70 p-4 transition hover:border-slate-300 flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between">
                    <span className="rounded bg-slate-200/80 px-2 py-0.5 font-mono text-[10px] font-semibold text-slate-700 uppercase">
                      JSON Specification
                    </span>
                    <span className="text-[10px] font-medium text-slate-500">
                      {artifact.category}
                    </span>
                  </div>

                  <h4 className="mt-2 text-xs font-bold text-slate-900">
                    {artifact.name}
                  </h4>
                  <p className="mt-0.5 font-mono text-[10px] text-slate-500 truncate" title={artifact.filename}>
                    experiments/ibm_results/{artifact.filename}
                  </p>
                  <p className="mt-2 text-xs text-slate-600 leading-relaxed">
                    {artifact.description}
                  </p>
                </div>

                <div className="mt-4 border-t border-slate-200 pt-3 flex items-center justify-between">
                  <button
                    type="button"
                    onClick={() => setExpandedSupportingId(isExpanded ? null : artifact.id)}
                    className="text-[11px] font-medium text-slate-600 hover:text-slate-900 underline underline-offset-2"
                  >
                    {isExpanded ? "Hide Spec" : "Preview Spec"}
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      downloadSupportingArtifactJson(artifact);
                      triggerNotice(`Downloaded ${artifact.filename}`);
                    }}
                    className="inline-flex items-center gap-1 rounded border border-slate-300 bg-white px-2.5 py-1 text-[11px] font-semibold text-slate-700 hover:bg-slate-50 transition"
                  >
                    <svg className="w-3 h-3 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                    </svg>
                    <span>Download JSON</span>
                  </button>
                </div>

                {isExpanded && (
                  <div className="mt-3 rounded-lg border border-slate-300 bg-slate-900 p-3 text-[11px] font-mono text-slate-200">
                    <pre className="overflow-x-auto max-h-44 p-1 text-slate-300">
                      {JSON.stringify(artifact.rawData, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* =========================================================================
          SECTION 3: Scientific Limitations & Disclosures Callout
          ========================================================================= */}
      <div className="rounded-xl border border-amber-200 bg-amber-50/70 p-6 shadow-sm">
        <div className="flex items-center gap-2 border-b border-amber-200/80 pb-3">
          <svg className="h-5 w-5 text-amber-700 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
          <h3 className="text-base font-bold text-amber-950">
            Mandatory Scientific Disclosures &amp; Algorithmic Limitations
          </h3>
        </div>

        <p className="mt-2 text-xs text-amber-900 leading-relaxed font-medium">
          In compliance with computational chemistry standards and empirical reproducibility rules, all quantum experiment records must be interpreted under the following physical constraints:
        </p>

        <div className="mt-4 space-y-3">
          {SCIENTIFIC_DISCLOSURES.map((item, idx) => (
            <div key={idx} className="rounded-lg border border-amber-200/80 bg-white/80 p-3.5 text-xs">
              <span className="font-bold text-amber-950 block">
                {idx + 1}. {item.topic}
              </span>
              <p className="mt-1 text-slate-700 leading-relaxed">
                {item.disclosure}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* =========================================================================
          SECTION 4: Verified Saved Benchmark Artifacts (Preserved from baseline)
          ========================================================================= */}
      <div className="rounded-xl border border-slate-200/90 bg-white p-6 shadow-sm">
        <h3 className="text-base font-semibold text-slate-900 mb-2">
          Verified Saved Benchmark Artifacts
        </h3>
        <p className="text-xs text-slate-500 mb-4">
          All benchmark runs generate immutable, reproducible disk artifacts in <code className="font-mono text-teal-700">benchmark_reports/egfr_regression/</code>.
        </p>

        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {SAVED_ARTIFACTS.map((artifact) => {
            const isSelected = selectedArtifact?.path === artifact.path;
            return (
              <button
                key={artifact.path}
                type="button"
                onClick={() => setSelectedArtifact(artifact)}
                className={`rounded-xl border p-4 text-left transition ${
                  isSelected
                    ? "border-teal-500 bg-teal-50/40 ring-1 ring-teal-500"
                    : "border-slate-200 bg-slate-50/70 hover:bg-slate-50 hover:border-slate-300"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="rounded bg-slate-200/80 px-2 py-0.5 font-mono text-[10px] font-semibold text-slate-700 uppercase">
                    {artifact.format}
                  </span>
                  <span className="text-[10px] text-emerald-600 font-semibold flex items-center gap-1">
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                    {artifact.status}
                  </span>
                </div>
                <h4 className="mt-2 text-xs font-bold text-slate-900 truncate" title={artifact.name}>
                  {artifact.name}
                </h4>
                <p className="mt-1 font-mono text-[10px] text-slate-500 truncate" title={artifact.path}>
                  {artifact.path}
                </p>
                <p className="mt-2 text-[11px] text-slate-600 line-clamp-2">
                  {artifact.description}
                </p>
              </button>
            );
          })}
        </div>

        {/* Selected Artifact Inspection Box */}
        {selectedArtifact && (
          <div className="mt-5 rounded-lg border border-slate-200 bg-slate-900 p-4 text-xs font-mono text-slate-200">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2 mb-3">
              <span className="text-teal-400 font-bold">{selectedArtifact.name}</span>
              <span className="text-slate-400">{selectedArtifact.size} &middot; {selectedArtifact.format}</span>
            </div>
            <p className="text-slate-400">Disk Location:</p>
            <p className="text-slate-100 break-all">{selectedArtifact.path}</p>
            <p className="mt-2 text-slate-400">Description:</p>
            <p className="text-slate-300 font-sans text-xs">{selectedArtifact.description}</p>
          </div>
        )}
      </div>

      {/* =========================================================================
          SECTION 5: Environment & Computational Provenance (Preserved)
          ========================================================================= */}
      <div className="rounded-xl border border-slate-200/90 bg-white p-6 shadow-sm">
        <h3 className="text-base font-semibold text-slate-900 mb-2">
          Environment &amp; Computational Provenance
        </h3>
        <p className="text-xs text-slate-500 mb-4">
          Software bill of materials and adapter architecture powering the CureGenix discovery platform.
        </p>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Host Architecture</span>
            <p className="mt-1 font-semibold text-slate-900 text-sm">Windows 11 x86_64</p>
            <p className="mt-0.5 text-xs text-slate-500">FastAPI backend on port 8000</p>
          </div>

          <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">WSL Quantum Adapter</span>
            <p className="mt-1 font-semibold text-teal-800 text-sm">Ubuntu 22.04 WSL 2</p>
            <p className="mt-0.5 text-xs text-slate-500">PySCF 2.14.0 in Linux venv</p>
          </div>

          <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Quantum Libraries</span>
            <p className="mt-1 font-semibold text-slate-900 text-sm">Qiskit 2.5.2 &amp; Nature</p>
            <p className="mt-0.5 text-xs text-slate-500">Jordan-Wigner mapper + VQE</p>
          </div>

          <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Cheminformatics</span>
            <p className="mt-1 font-semibold text-slate-900 text-sm">RDKit 2026.09.1</p>
            <p className="mt-0.5 text-xs text-slate-500">Morgan fingerprints &amp; Murcko</p>
          </div>
        </div>
      </div>

      {/* =========================================================================
          SECTION 6: Embedded Technical Pipeline Details (Preserved)
          ========================================================================= */}
      <div className="rounded-xl border border-slate-200/90 bg-white p-6 shadow-sm">
        <h3 className="text-base font-semibold text-slate-900 mb-2">
          Pipeline Agent Latencies &amp; Execution Tree
        </h3>
        <p className="text-xs text-slate-500 mb-4">
          Detailed agent-by-agent execution trace and run parameters.
        </p>

        <TechnicalDetails derived={derived || { vqeMolecules: [], steps: [] }} />
      </div>
    </div>
  );
}
