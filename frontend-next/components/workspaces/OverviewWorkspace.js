"use client";

import { isNum } from "@/lib/analysis";
import {
  PipelineStageTimingChart,
  QuantumOutcomeDistributionChart,
} from "../charts/ScientificCharts";

function KpiCard({ title, value, subtitle, accent = "text-slate-900", badge = null }) {
  return (
    <div className="rounded-xl border border-slate-200/90 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between">
        <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">{title}</p>
        {badge && (
          <span className="rounded bg-teal-50 text-teal-800 border border-teal-200/80 px-2 py-0.5 text-[10px] font-semibold">
            {badge}
          </span>
        )}
      </div>
      <p className={`font-data mt-3 text-2xl font-bold tracking-tight sm:text-3xl ${accent}`}>
        {value}
      </p>
      {subtitle && <p className="mt-1 text-xs text-slate-500">{subtitle}</p>}
    </div>
  );
}

export default function OverviewWorkspace({
  result,
  derived,
  onNavigate,
  onStartAnalysis,
}) {
  const isDone = Boolean(result && derived);

  const summary = derived?.summaryCounts || {
    analyzed: 0,
    quantumEvaluated: 0,
    quantumTargeted: 0,
  };

  const proteinInfo = derived?.proteinInfo || {};
  const durationMs = derived?.durationMs;
  const bestNovelId = derived?.bestNovelId;
  const bestNovelIsTie = derived?.bestNovelIsTie;
  const candidates = derived?.candidates || [];
  const vqeMolecules = derived?.vqeMolecules || [];
  const resourceSkippedMolecules = derived?.resourceSkippedMolecules || [];

  return (
    <div className="space-y-8">
      {/* Workspace Header */}
      <div className="rounded-2xl border border-slate-200/80 bg-gradient-to-r from-slate-900 to-[#0B132B] p-6 sm:p-8 text-white shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="max-w-3xl">
            <div className="flex items-center gap-2">
              <span className="rounded bg-teal-400/20 text-teal-300 border border-teal-400/30 px-2 py-0.5 text-xs font-semibold uppercase tracking-wider">
                Discovery Console
              </span>
              <span className="text-xs text-slate-400">
                {isDone ? "Pipeline Execution Complete" : "Target Ready for Pipeline Execution"}
              </span>
            </div>
            <h2 className="mt-3 text-2xl font-bold tracking-tight text-white sm:text-3xl">
              {result?.protein_name || result?.protein?.name || "EGFR Kinase Domain Discovery"}
            </h2>
            <p className="mt-2 text-sm text-slate-300 leading-relaxed">
              Target-aware molecular candidate generation, classical &amp; quantum scoring, and scaffold-disjoint validation across verified biological benchmarks.
            </p>
          </div>

          <div className="flex flex-wrap gap-2.5">
            <button
              type="button"
              onClick={() => onNavigate("target-analysis")}
              className="rounded-lg bg-teal-600 px-4 py-2 text-xs font-semibold text-white shadow-sm hover:bg-teal-700 transition"
            >
              Target Analysis &rarr;
            </button>
            <button
              type="button"
              onClick={() => onNavigate("benchmarks")}
              className="rounded-lg border border-slate-700 bg-slate-800/80 px-4 py-2 text-xs font-semibold text-slate-200 hover:bg-slate-700 transition"
            >
              View Benchmarks
            </button>
          </div>
        </div>

        {/* Target Meta Chips */}
        <div className="mt-6 flex flex-wrap gap-2 border-t border-slate-800 pt-4 text-xs">
          <span className="rounded-md bg-slate-800/90 border border-slate-700/80 px-2.5 py-1 text-slate-300">
            PDB: <strong className="text-white font-mono">{result?.protein?.pdb_id || "1M17 / 1XKK"}</strong>
          </span>
          <span className="rounded-md bg-slate-800/90 border border-slate-700/80 px-2.5 py-1 text-slate-300">
            UniProt: <strong className="text-teal-300 font-mono">P00533 (EGFR_HUMAN)</strong>
          </span>
          <span className="rounded-md bg-slate-800/90 border border-slate-700/80 px-2.5 py-1 text-slate-300">
            Target Chain: <strong className="text-white font-mono">A (Kinase Domain)</strong>
          </span>
          <span className="rounded-md bg-slate-800/90 border border-slate-700/80 px-2.5 py-1 text-slate-300">
            Active Space: <strong className="text-white font-mono">(4e, 4o) STO-3G PySCF</strong>
          </span>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <KpiCard
          title="Candidates Analyzed"
          value={isDone ? summary.analyzed : "8 Identified"}
          subtitle={isDone ? "Novel & reference structures" : "Target-aware generation pool"}
          badge="Chemical Space"
        />
        <KpiCard
          title="Quantum Evaluated"
          value={isDone ? summary.quantumEvaluated : "Active VQE"}
          accent="text-teal-700"
          subtitle={
            isDone && summary.quantumTargeted != null
              ? `of ${summary.quantumTargeted} novel candidates`
              : "PySCF WSL 2.14.0 solver"
          }
          badge="Quantum State"
        />
        <KpiCard
          title={bestNovelIsTie ? "Top Score · Tied" : "Top Candidate"}
          value={bestNovelId || (isDone ? "Tied Score" : "CAN-001")}
          accent="text-indigo-600"
          subtitle={bestNovelIsTie ? "Equal adjusted scores" : "Prioritized novel derivative"}
          badge="Ranking"
        />
        <KpiCard
          title="Total Pipeline Time"
          value={isNum(durationMs) ? `${(durationMs / 1000).toFixed(1)}s` : "16.1s (nominal)"}
          subtitle="Wall-clock autonomous execution"
          badge="Latency"
        />
      </div>

      {/* Primary Visualizations */}
      <div className="grid gap-8 lg:grid-cols-2">
        {/* Visualization 3: Pipeline Stage Timing Chart */}
        <PipelineStageTimingChart steps={derived?.steps || []} />

        {/* Visualization 5: Quantum Execution Outcomes */}
        <QuantumOutcomeDistributionChart
          candidateCount={candidates.length}
          vqeCount={vqeMolecules.length}
          skippedCount={resourceSkippedMolecules.length}
        />
      </div>

      {/* Model Benchmark Highlights Grid */}
      <div className="rounded-xl border border-slate-200/90 bg-white p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-slate-100 pb-4">
          <div>
            <h3 className="text-base font-semibold text-slate-900">
              Verified Scientific Benchmark Highlights
            </h3>
            <p className="text-xs text-slate-500">
              Scaffold-disjoint classical regression, 16D statevector quantum pilot, and retrospective activity proxies.
            </p>
          </div>
          <button
            type="button"
            onClick={() => onNavigate("benchmarks")}
            className="text-xs font-semibold text-teal-700 hover:text-teal-800"
          >
            Explore Full Validation Suite &rarr;
          </button>
        </div>

        <div className="mt-5 grid gap-4 md:grid-cols-3">
          {/* Highlight A */}
          <div className="rounded-xl border border-slate-200 bg-slate-50/70 p-4">
            <span className="rounded bg-emerald-100 text-emerald-800 text-[10px] font-bold uppercase tracking-wider px-2 py-0.5">
              5-Split Classical Scaffold
            </span>
            <p className="mt-2 text-sm font-bold text-slate-900">RBF-SVR vs Random Forest</p>
            <div className="mt-3 space-y-1 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-500">RBF-SVR MAE:</span>
                <span className="font-data font-semibold text-slate-800">0.5607 ± 0.0689</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Random Forest MAE:</span>
                <span className="font-data font-semibold text-slate-800">0.5270 ± 0.0672</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Dataset Scope:</span>
                <span className="font-semibold text-slate-700">2,995 EGFR compounds</span>
              </div>
            </div>
          </div>

          {/* Highlight B */}
          <div className="rounded-xl border border-slate-200 bg-slate-50/70 p-4">
            <span className="rounded bg-amber-100 text-amber-800 text-[10px] font-bold uppercase tracking-wider px-2 py-0.5">
              Matched 16D Pilot
            </span>
            <p className="mt-2 text-sm font-bold text-slate-900">Quantum Kernel SVR (Single Split)</p>
            <div className="mt-3 space-y-1 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-500">Quantum MAE:</span>
                <span className="font-data font-semibold text-violet-700">0.9435</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Classical RBF MAE:</span>
                <span className="font-data font-semibold text-slate-800">0.6476</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Evaluation Mode:</span>
                <span className="text-slate-700">16D Statevector Sim</span>
              </div>
            </div>
          </div>

          {/* Highlight C */}
          <div className="rounded-xl border border-slate-200 bg-slate-50/70 p-4">
            <span className="rounded bg-sky-100 text-sky-800 text-[10px] font-bold uppercase tracking-wider px-2 py-0.5">
              Activity Proxy AI
            </span>
            <p className="mt-2 text-sm font-bold text-slate-900">VQC vs QGNN vs Classical</p>
            <div className="mt-3 space-y-1 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-500">Classical Balanced Acc:</span>
                <span className="font-data font-semibold text-sky-800">85.0%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">VQC Balanced Acc:</span>
                <span className="font-data font-semibold text-teal-700">64.8%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">QGNN Balanced Acc:</span>
                <span className="font-data font-semibold text-violet-700">59.4%</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
