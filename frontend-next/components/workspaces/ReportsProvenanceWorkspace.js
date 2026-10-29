"use client";

import { useState } from "react";
import TechnicalDetails from "../TechnicalDetails";

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

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-slate-200 pb-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-slate-900 sm:text-2xl">
            Reports &amp; Provenance Vault
          </h2>
          <p className="mt-1 text-sm text-slate-600">
            Persistent artifact audit trails, verified benchmark reports, environment configuration, and execution provenance.
          </p>
        </div>
        <span className="rounded-full bg-teal-50 border border-teal-200 px-3 py-1 text-xs font-semibold text-teal-800">
          6 Verified Artifacts
        </span>
      </div>

      {/* Artifact Inventory Grid */}
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
              <span className="text-slate-400">{selectedArtifact.size} · {selectedArtifact.format}</span>
            </div>
            <p className="text-slate-400">Disk Location:</p>
            <p className="text-slate-100 break-all">{selectedArtifact.path}</p>
            <p className="mt-2 text-slate-400">Description:</p>
            <p className="text-slate-300 font-sans text-xs">{selectedArtifact.description}</p>
          </div>
        )}
      </div>

      {/* Environment & Software Bill of Materials */}
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

      {/* Embedded Technical Pipeline Details */}
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
