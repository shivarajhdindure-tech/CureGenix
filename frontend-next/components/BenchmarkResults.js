"use client";

import { useEffect, useState } from "react";
import { STATIC_BENCHMARK_DATA, METRIC_EXPLANATIONS } from "@/lib/benchmarkData";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function StatusBadge({ type, text }) {
  if (type === "complete") {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-400/30 bg-emerald-400/10 px-3 py-1 text-xs font-medium text-emerald-300">
        <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
        {text}
      </span>
    );
  }
  if (type === "pending") {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full border border-amber-400/30 bg-amber-400/10 px-3 py-1 text-xs font-medium text-amber-300">
        <span className="h-1.5 w-1.5 rounded-full bg-amber-400 animate-pulse" />
        {text}
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full border border-cyan-400/30 bg-cyan-400/10 px-3 py-1 text-xs font-medium text-cyan-300">
      <span className="h-1.5 w-1.5 rounded-full bg-cyan-400" />
      {text}
    </span>
  );
}

function MetricBox({ title, subtitle, mae, rmse, r2, color = "border-white/10" }) {
  return (
    <div className={`rounded-2xl border ${color} bg-ink-900/60 p-5 shadow-sm transition hover:border-white/20`}>
      <div className="flex items-start justify-between gap-2">
        <div>
          <h4 className="text-base font-semibold text-white">{title}</h4>
          {subtitle && <p className="mt-0.5 text-xs text-slate-400">{subtitle}</p>}
        </div>
      </div>
      <div className="mt-4 grid grid-cols-3 gap-2 border-t border-white/[0.06] pt-3">
        <div>
          <p className="text-[10px] font-medium uppercase tracking-wider text-slate-400">MAE (pIC50)</p>
          <p className="font-data mt-1 text-lg font-bold text-white sm:text-xl">{mae}</p>
          <p className="text-[10px] text-slate-400">Lower is better</p>
        </div>
        <div>
          <p className="text-[10px] font-medium uppercase tracking-wider text-slate-400">RMSE</p>
          <p className="font-data mt-1 text-lg font-bold text-white sm:text-xl">{rmse}</p>
          <p className="text-[10px] text-slate-400">Lower is better</p>
        </div>
        <div>
          <p className="text-[10px] font-medium uppercase tracking-wider text-slate-400">R² Score</p>
          <p className={`font-data mt-1 text-lg font-bold sm:text-xl ${String(r2).startsWith("-") ? "text-red-400" : "text-emerald-300"}`}>
            {r2}
          </p>
          <p className="text-[10px] text-slate-400">Higher is better</p>
        </div>
      </div>
    </div>
  );
}

function MatchedBarChart({ label, note, items, lowerIsBetter = true }) {
  const numericValues = items.map((i) => Math.abs(i.value));
  const maxVal = Math.max(...numericValues, 1e-4);

  return (
    <div className="metric">
      <div className="flex items-baseline justify-between gap-2">
        <p className="text-sm font-semibold text-white">{label}</p>
        <span className="text-[11px] text-slate-400">{note}</span>
      </div>
      <div className="mt-4 space-y-3.5">
        {items.map((item) => {
          const widthPct = Math.max(5, Math.min(100, (Math.abs(item.value) / maxVal) * 100));
          return (
            <div key={item.name}>
              <div className="flex items-baseline justify-between gap-3 text-xs">
                <span className="truncate font-medium text-slate-300" title={item.name}>
                  {item.name}
                </span>
                <span className="font-data text-white font-semibold">
                  {typeof item.value === "number" ? item.value.toFixed(4) : item.value}
                </span>
              </div>
              <div className="mt-1.5 h-2.5 overflow-hidden rounded-full bg-white/[0.06]">
                <div
                  className={`h-full origin-left rounded-full transition-all duration-700 ${item.color}`}
                  style={{ width: `${widthPct}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
      <div className="mt-3 flex items-center justify-between text-[11px] text-slate-400">
        <span>{lowerIsBetter ? "← Shorter bar is better" : "→ Longer bar is better"}</span>
        <span>{items.find((i) => i.isBest)?.name ? `Best: ${items.find((i) => i.isBest).name}` : ""}</span>
      </div>
    </div>
  );
}

function ReportModal({ report, onClose }) {
  if (!report) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="report-modal-title"
      className="fixed inset-0 z-50 flex items-center justify-center bg-ink-950/80 p-4 backdrop-blur-md"
    >
      <div className="relative flex max-h-[88vh] w-full max-w-4xl flex-col rounded-3xl border border-white/15 bg-ink-900 shadow-2xl">
        <div className="flex items-start justify-between border-b border-white/10 p-6">
          <div>
            <span className="eyebrow">Benchmark Artifact</span>
            <h3 id="report-modal-title" className="mt-1 text-xl font-bold text-white">
              {report.title}
            </h3>
            {report.description && (
              <p className="mt-1 text-xs text-slate-400">{report.description}</p>
            )}
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close report modal"
            className="rounded-xl border border-white/10 bg-white/[0.04] p-2 text-slate-400 transition hover:bg-white/10 hover:text-white"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 6 6 18M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div className="overflow-y-auto p-6 font-data text-xs leading-relaxed text-slate-300">
          <pre className="whitespace-pre-wrap font-sans text-xs sm:text-sm text-slate-200">
            {report.content}
          </pre>
        </div>
        <div className="flex items-center justify-between border-t border-white/10 bg-ink-950/50 px-6 py-4">
          <span className="text-xs text-slate-400">File: {report.filename || "verified_report.md"}</span>
          <button type="button" onClick={onClose} className="btn-ghost !py-1.5 text-xs">
            Close Viewer
          </button>
        </div>
      </div>
    </div>
  );
}

export default function BenchmarkResults() {
  const [data, setData] = useState(STATIC_BENCHMARK_DATA);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [source, setSource] = useState("static"); // "live" | "static"
  const [activeReport, setActiveReport] = useState(null);
  const [reportLoading, setReportLoading] = useState(false);
  const [showGlossary, setShowGlossary] = useState(false);

  async function fetchBenchmarkData() {
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${API_URL}/api/benchmarks/egfr`);
      if (!res.ok) {
        throw new Error(`Server returned HTTP ${res.status}`);
      }
      const fetched = await res.json();
      setData(fetched);
      setSource("live");
    } catch (err) {
      console.warn("Could not fetch live benchmark data; using verified static dataset:", err);
      setError("Backend benchmark endpoint unreachable; displaying verified milestone dataset.");
      setData(STATIC_BENCHMARK_DATA);
      setSource("static");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchBenchmarkData();
  }, []);

  async function openReport(reportId) {
    setReportLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/benchmarks/egfr/reports/${reportId}`);
      if (res.ok) {
        const rep = await res.json();
        setActiveReport(rep);
        return;
      }
    } catch (err) {
      console.warn("Live report fetch failed, using fallback:", err);
    } finally {
      setReportLoading(false);
    }

    // Fallback if backend API report fetch is unavailable
    if (reportId === "scaffold_validation") {
      setActiveReport({
        title: "EGFR Scaffold-Aware Classical Validation Report",
        description: "Five-seed nested GroupShuffleSplit evaluation across 2,995 compounds and 1,129 scaffolds.",
        filename: "report.md",
        content: `# EGFR Scaffold-Aware Classical Validation

## Dataset and scaffold audit
- 2996 curated rows were present; 2995 were evaluated across 1129 recomputed Murcko scaffolds.
- 1 row was excluded because the SMILES was blank or invalid.
- RDKit non-isomeric canonical Murcko scaffold IDs matched all parseable saved group labels exactly (0 mismatches).

## Repeated scaffold validation (5 deterministic seeds: 11, 23, 42, 87, 101)
Approximately 60/20/20 by scaffold group with zero scaffold overlap across partitions.

### Test metrics across seeds (mean ± sample SD)
- RBF-SVR: MAE 0.5607 ± 0.0689; RMSE 0.7609 ± 0.0883; R² 0.6061 ± 0.0496
- Random Forest: MAE 0.5270 ± 0.0672; RMSE 0.7286 ± 0.0758; R² 0.6386 ± 0.0394

### Per-seed outcomes
- Seed 11: SVR test MAE 0.4990 | RF test MAE 0.4555
- Seed 23: SVR test MAE 0.6213 | RF test MAE 0.5873
- Seed 42: SVR test MAE 0.5477 | RF test MAE 0.5079
- Seed 87: SVR test MAE 0.4928 | RF test MAE 0.4771
- Seed 101: SVR test MAE 0.6428 | RF test MAE 0.6073

## Quantum comparability
The existing quantum pilot can be compared fairly ONLY on its original single matched split (256/64/64). It cannot be scored on the five new repeated splits without full quantum recomputation (~12.5h on simulator).`,
      });
    } else {
      setActiveReport({
        title: "EGFR 16D Pilot: Classical vs Quantum-Kernel Comparison Report",
        description: "Matched comparison on identical 256/64/64 compounds using saved 16D pilot representations.",
        filename: "comparison_report.md",
        content: `# EGFR 16D Pilot: Classical vs Quantum-Kernel Comparison

## Design and alignment
- Same exact pilot compounds and targets: 256 train, 64 validation, 64 test.
- Preprocessing: 16D SVD and scaling fit on training rows only.
- Classical models use the exact same 16-dimensional representation as the quantum feature map.

## Results
- Saved quantum Nyström SVR (4 landmarks): Test MAE 0.9435 | Test RMSE 1.1234 | Test R² -0.0531
- Classical RBF-SVR on same 16D features: Test MAE 0.6476 | Test RMSE 0.9045 | Test R² 0.3172
- Classical Random Forest on same 16D features: Test MAE 0.6166 | Test RMSE 0.7839 | Test R² 0.4872

Quantum minus matched classical RBF-SVR test MAE: +0.2959 pIC50.
These results do NOT support a quantum advantage.

## Execution Details
- Quantum kernel: 16D ZZFeatureMap fidelity kernel with 4 landmarks.
- Hardware: Qiskit StatevectorSampler (classical simulation, not physical quantum hardware).`,
      });
    }
  }

  const classicalModels = data.five_split_classical.models;
  const pilotModels = data.single_split_pilot_comparison.models;

  return (
    <section id="benchmarks" className="scroll-mt-24">
      <div className="panel-quantum p-6 md:p-8 space-y-8">
        {/* Section Header & Status Badges */}
        <div className="flex flex-wrap items-start justify-between gap-4 border-b border-white/[0.08] pb-6">
          <div className="max-w-3xl">
            <p className="eyebrow">Model Evaluation & Validation</p>
            <h2 className="section-title mt-2">EGFR Benchmark & Validation Milestone</h2>
            <p className="mt-2 text-sm leading-6 text-slate-300">
              Rigorous empirical evaluation on {data.dataset.evaluated_compounds.toLocaleString()} curated EGFR
              biochemical measurements across {data.dataset.unique_murcko_scaffolds.toLocaleString()} Murcko scaffolds.
              Evaluates generalization under scaffold distribution shifts and reports transparent quantum simulator baselines.
            </p>
          </div>
          <div className="flex flex-col items-end gap-2">
            <div className="flex flex-wrap gap-2">
              <StatusBadge
                type="complete"
                text={data.status_indicators?.classical_validation || "Classical scaffold validation complete"}
              />
              <StatusBadge
                type="pending"
                text={data.status_indicators?.quantum_validation || "Repeated scaffold-split quantum validation pending"}
              />
            </div>
            <div className="flex items-center gap-2 pt-1 text-xs text-slate-400">
              <span>Source: {source === "live" ? "Live Backend API" : "Verified Milestone Artifact"}</span>
              <button
                type="button"
                onClick={fetchBenchmarkData}
                disabled={loading}
                className="text-cyan-300 hover:underline disabled:opacity-50"
              >
                {loading ? "Refreshing…" : "Refresh"}
              </button>
            </div>
          </div>
        </div>

        {error && (
          <div role="status" className="rounded-xl border border-amber-400/30 bg-amber-400/[0.05] p-3.5 text-xs text-amber-200">
            {error}
          </div>
        )}

        {/* Dataset Summary Pill Grid */}
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <div className="rounded-xl border border-white/[0.07] bg-ink-900/50 p-4">
            <p className="metric-label">Evaluated Compounds</p>
            <p className="font-data mt-1.5 text-2xl font-bold text-white">
              {data.dataset.evaluated_compounds.toLocaleString()}
            </p>
            <p className="mt-1 text-[11px] text-slate-400">Curated ChEMBL IC50 / pIC50</p>
          </div>
          <div className="rounded-xl border border-white/[0.07] bg-ink-900/50 p-4">
            <p className="metric-label">Murcko Scaffolds</p>
            <p className="font-data mt-1.5 text-2xl font-bold text-cyan-300">
              {data.dataset.unique_murcko_scaffolds.toLocaleString()}
            </p>
            <p className="mt-1 text-[11px] text-slate-400">Independent scaffold groups</p>
          </div>
          <div className="rounded-xl border border-white/[0.07] bg-ink-900/50 p-4">
            <p className="metric-label">Classical Folds</p>
            <p className="font-data mt-1.5 text-2xl font-bold text-violet-300">5 Splits</p>
            <p className="mt-1 text-[11px] text-slate-400">Seeds 11, 23, 42, 87, 101</p>
          </div>
          <div className="rounded-xl border border-white/[0.07] bg-ink-900/50 p-4">
            <p className="metric-label">Excluded Row</p>
            <p className="font-data mt-1.5 text-2xl font-bold text-amber-300">1 Row</p>
            <p className="mt-1 text-[11px] text-slate-400" title="Blank SMILES prevented scaffold audit">
              Blank SMILES audit exclusion
            </p>
          </div>
        </div>

        {/* =========================================================================
            SECTION 1: 5-SPLIT SCAFFOLD-DISJOINT CLASSICAL VALIDATION
            ========================================================================= */}
        <div className="rounded-3xl border border-violet-400/25 bg-ink-950/40 p-6 md:p-8 space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="badge border-violet-400/40 bg-violet-400/10 text-violet-300">
                  Full Cohort · 5-Fold Cross-Validation
                </span>
                <span className="badge border-emerald-400/30 bg-emerald-400/10 text-emerald-300">
                  Mean ± Sample SD
                </span>
              </div>
              <h3 className="mt-2 text-xl font-bold text-white">
                1. Five-Split Scaffold-Disjoint Classical Evaluation
              </h3>
              <p className="mt-1 text-xs text-slate-400 max-w-2xl">
                Trained and evaluated across 2,995 compounds grouped by Murcko scaffolds. GroupShuffleSplit ensured zero scaffold overlap
                across partitions. Models were selected solely on validation MAE and refit on train+validation before held-out test scoring.
              </p>
            </div>
            <button
              type="button"
              onClick={() => openReport("scaffold_validation")}
              disabled={reportLoading}
              className="btn-ghost !py-2 text-xs"
            >
              View Scaffold Audit Report →
            </button>
          </div>

          {/* Classical Models Metric Cards */}
          <div className="grid gap-5 md:grid-cols-2">
            <MetricBox
              title="Classical RBF-SVR"
              subtitle="128-component TruncatedSVD + StandardScaler fit on training only"
              mae="0.5607 ± 0.0689"
              rmse="0.7609 ± 0.0883"
              r2="0.6061 ± 0.0496"
              color="border-cyan-400/30"
            />
            <MetricBox
              title="Classical Random Forest"
              subtitle="Original 2048 Morgan bits · 200 trees · min_samples_leaf=2"
              mae="0.5270 ± 0.0672"
              rmse="0.7286 ± 0.0758"
              r2="0.6386 ± 0.0394"
              color="border-violet-400/30"
            />
          </div>

          {/* Per-Seed Breakdown Table */}
          <div className="overflow-x-auto rounded-2xl border border-white/[0.08] bg-ink-900/60 p-4">
            <div className="flex items-baseline justify-between mb-3 px-1">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-300">
                Per-Seed Split Outcomes & Compound Partitioning
              </h4>
              <span className="text-[11px] text-slate-400">Zero scaffold leakage across all partitions</span>
            </div>
            <table className="w-full text-left text-xs">
              <thead className="border-b border-white/10 text-slate-400 font-medium">
                <tr>
                  <th className="py-2 px-3">Seed</th>
                  <th className="py-2 px-3">Train n / Scaffolds</th>
                  <th className="py-2 px-3">Val n / Scaffolds</th>
                  <th className="py-2 px-3">Test n / Scaffolds</th>
                  <th className="py-2 px-3 font-data text-right">RBF-SVR Test MAE</th>
                  <th className="py-2 px-3 font-data text-right">Random Forest Test MAE</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.05] text-slate-200">
                {data.five_split_classical.per_seed_summary?.map((row) => (
                  <tr key={row.seed} className="hover:bg-white/[0.02]">
                    <td className="py-2.5 px-3 font-semibold text-white">Seed {row.seed}</td>
                    <td className="py-2.5 px-3 font-data text-slate-400">{row.train_n} / 677</td>
                    <td className="py-2.5 px-3 font-data text-slate-400">{row.val_n} / 226</td>
                    <td className="py-2.5 px-3 font-data text-slate-400">{row.test_n} / 226</td>
                    <td className="py-2.5 px-3 font-data text-right text-cyan-300 font-semibold">
                      {row.svr_test_mae.toFixed(4)}
                    </td>
                    <td className="py-2.5 px-3 font-data text-right text-violet-300 font-semibold">
                      {row.rf_test_mae.toFixed(4)}
                    </td>
                  </tr>
                ))}
              </tbody>
              <tfoot className="border-t border-white/10 font-semibold text-slate-100">
                <tr>
                  <td className="py-2.5 px-3">Mean ± SD</td>
                  <td className="py-2.5 px-3 font-data text-slate-400" colSpan={3}>
                    Full Cohort (2,995 compounds, 1,129 scaffolds)
                  </td>
                  <td className="py-2.5 px-3 font-data text-right text-cyan-300">0.5607 ± 0.0689</td>
                  <td className="py-2.5 px-3 font-data text-right text-violet-300">0.5270 ± 0.0672</td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>

        {/* =========================================================================
            CRITICAL METHODOLOGY DISTINCTION BANNER (Requirement 4 & 5)
            ========================================================================= */}
        <div
          role="note"
          className="rounded-2xl border border-amber-400/35 bg-gradient-to-r from-amber-500/[0.08] to-amber-400/[0.03] p-5 text-amber-100 space-y-2"
        >
          <div className="flex items-center gap-2">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-amber-400">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            <h4 className="text-sm font-bold text-amber-200">
              Methodology Separation & Simulator Disclosure
            </h4>
          </div>
          <p className="text-xs leading-relaxed text-amber-200/90">
            <strong>Cross-Split Distinction:</strong> The 5-split evaluation above evaluates the complete cohort (2,995 compounds)
            across five randomized scaffold folds. The quantum comparison below is restricted to a single matched 64-compound pilot test partition
            (384 compounds total). To avoid misleading comparisons, results from these different splits and feature spaces are strictly separated.
          </p>
          <p className="text-xs leading-relaxed text-amber-200/90">
            <strong>Simulator Disclosure:</strong> The quantum kernel was evaluated on a classical statevector simulator
            (Qiskit StatevectorSampler, 256 shots) with 16 features and 4 landmarks—<strong>not physical quantum hardware</strong>.
            No quantum advantage is claimed.
          </p>
        </div>

        {/* =========================================================================
            SECTION 2: SINGLE MATCHED 16D PILOT COMPARISON (Requirement 3)
            ========================================================================= */}
        <div className="rounded-3xl border border-cyan-400/25 bg-ink-950/40 p-6 md:p-8 space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <span className="badge border-cyan-400/40 bg-cyan-400/10 text-cyan-300">
                  Single Matched Pilot Split (Seed 42)
                </span>
                <span className="badge border-amber-400/30 bg-amber-400/10 text-amber-300">
                  Classical Statevector Simulator (No Hardware Run)
                </span>
                <span className="badge border-slate-400/30 bg-slate-400/10 text-slate-300">
                  16 Features · 4 Landmarks
                </span>
              </div>
              <h3 className="mt-2 text-xl font-bold text-white">
                2. Matched 16D Single-Split Pilot: Quantum vs. Classical Models
              </h3>
              <p className="mt-1 text-xs text-slate-400 max-w-2xl">
                Identical 256 training, 64 validation, and 64 held-out test compounds in identical row order.
                All three models evaluate the exact same 16-dimensional PCA/SVD representation (retaining 52.9% fingerprint variance).
              </p>
            </div>
            <button
              type="button"
              onClick={() => openReport("pilot_comparison")}
              disabled={reportLoading}
              className="btn-ghost !py-2 text-xs"
            >
              View Pilot Comparison Report →
            </button>
          </div>

          {/* Matched Model Cards Grid */}
          <div className="grid gap-4 sm:grid-cols-3">
            <MetricBox
              title="Quantum-Kernel SVR"
              subtitle="16D ZZFeatureMap · 4 landmarks · Simulator"
              mae="0.9435"
              rmse="1.1234"
              r2="−0.0531"
              color="border-cyan-400/40 bg-cyan-400/[0.04]"
            />
            <MetricBox
              title="Classical RBF-SVR"
              subtitle="Matched 16D pilot angles · C=10.0, eps=0.2"
              mae="0.6476"
              rmse="0.9045"
              r2="0.3172"
              color="border-violet-400/30"
            />
            <MetricBox
              title="Classical Random Forest"
              subtitle="Matched 16D pilot angles · 400 trees · min_leaf=2"
              mae="0.6166"
              rmse="0.7839"
              r2="0.4872"
              color="border-emerald-400/30"
            />
          </div>

          {/* Delta & Scientific Finding Highlight */}
          <div className="rounded-2xl border border-white/[0.08] bg-ink-900/60 p-5">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <p className="eyebrow text-cyan-300/80">Matched Error Difference</p>
                <p className="mt-1 text-base font-semibold text-white">
                  Quantum minus Matched Classical RBF-SVR:{" "}
                  <span className="font-data text-amber-300 font-bold">+0.2959 pIC50</span>
                </p>
                <p className="mt-1 text-xs text-slate-400 max-w-2xl leading-5">
                  Positive difference indicates higher prediction error for the quantum model on the held-out pilot test split.
                  Classical models (RBF-SVR and Random Forest) achieved lower error and higher explanatory power (R² = 0.3172 and 0.4872)
                  than the quantum-kernel model (R² = −0.0531).
                </p>
              </div>
              <div className="rounded-xl border border-white/10 bg-white/[0.03] p-3 text-right">
                <p className="text-[10px] uppercase tracking-wider text-slate-400">Quantum Pilot Cost</p>
                <p className="font-data text-lg font-bold text-white">1,168.6s (19.5 min)</p>
                <p className="text-[10px] text-slate-400">4 landmarks on 384 compounds</p>
              </div>
            </div>
          </div>

          {/* Direct Visual Charts for Matched Pilot Split */}
          <div className="grid gap-5 md:grid-cols-3">
            <MatchedBarChart
              label="Test MAE (pIC50)"
              note="Lower is better"
              lowerIsBetter={true}
              items={[
                { name: "Quantum SVR (4 LM)", value: 0.9435, color: "bg-cyan-400", isBest: false },
                { name: "Classical RBF-SVR", value: 0.6476, color: "bg-violet-400", isBest: false },
                { name: "Classical Random Forest", value: 0.6166, color: "bg-emerald-400", isBest: true },
              ]}
            />
            <MatchedBarChart
              label="Test RMSE"
              note="Lower is better"
              lowerIsBetter={true}
              items={[
                { name: "Quantum SVR (4 LM)", value: 1.1234, color: "bg-cyan-400", isBest: false },
                { name: "Classical RBF-SVR", value: 0.9045, color: "bg-violet-400", isBest: false },
                { name: "Classical Random Forest", value: 0.7839, color: "bg-emerald-400", isBest: true },
              ]}
            />
            <MatchedBarChart
              label="Test R² Score"
              note="Higher is better"
              lowerIsBetter={false}
              items={[
                { name: "Quantum SVR (4 LM)", value: -0.0531, color: "bg-red-400", isBest: false },
                { name: "Classical RBF-SVR", value: 0.3172, color: "bg-violet-400", isBest: false },
                { name: "Classical Random Forest", value: 0.4872, color: "bg-emerald-400", isBest: true },
              ]}
            />
          </div>
        </div>

        {/* =========================================================================
            SECTION 3: METRIC DEFINITIONS & ARTIFACT AUDIT
            ========================================================================= */}
        <div className="rounded-2xl border border-white/[0.08] bg-ink-900/40 p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-semibold text-white">Metric Glossary & Scientific Standards</h4>
            <button
              type="button"
              onClick={() => setShowGlossary(!showGlossary)}
              className="text-xs text-cyan-300 hover:underline"
            >
              {showGlossary ? "Hide Definitions" : "Show Definitions"}
            </button>
          </div>

          {showGlossary && (
            <div className="grid gap-3 pt-2 text-xs sm:grid-cols-2">
              {METRIC_EXPLANATIONS.map((item) => (
                <div key={item.term} className="rounded-xl border border-white/[0.06] bg-ink-950/60 p-3.5">
                  <p className="font-semibold text-cyan-200">{item.term}</p>
                  <p className="mt-1 leading-relaxed text-slate-300">{item.definition}</p>
                </div>
              ))}
            </div>
          )}

          <div className="flex flex-wrap items-center justify-between gap-3 border-t border-white/[0.06] pt-4 text-xs text-slate-400">
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-emerald-400" />
              <span>Full artifact provenance verified against recomputed Murcko scaffolds and ChEMBL curated source rows.</span>
            </div>
            <div className="flex gap-3">
              <button
                type="button"
                onClick={() => openReport("scaffold_validation")}
                className="text-cyan-300 hover:underline"
              >
                scaffold_validation/report.md
              </button>
              <span>·</span>
              <button
                type="button"
                onClick={() => openReport("pilot_comparison")}
                className="text-cyan-300 hover:underline"
              >
                classical_quantum_comparison_16d_pilot/comparison_report.md
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Full Report Modal */}
      {activeReport && <ReportModal report={activeReport} onClose={() => setActiveReport(null)} />}
    </section>
  );
}
