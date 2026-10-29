"use client";

import { PilotMatchedComparatorChart } from "../charts/ScientificCharts";
import BenchmarkResults from "../BenchmarkResults";

export default function BenchmarksWorkspace() {
  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-slate-200 pb-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-slate-900 sm:text-2xl">
            Benchmarks &amp; Scientific Validation
          </h2>
          <p className="mt-1 text-sm text-slate-600">
            Rigorous scaffold-disjoint evaluation across 2,995 EGFR compounds and matched classical vs. quantum comparisons.
          </p>
        </div>

        {/* Status Indicators */}
        <div className="flex flex-wrap items-center gap-2">
          <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-300 bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-800">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
            Classical scaffold validation complete
          </span>
          <span className="inline-flex items-center gap-1.5 rounded-full border border-amber-300 bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-800">
            <span className="h-1.5 w-1.5 rounded-full bg-amber-500 animate-pulse" />
            Repeated scaffold-split quantum validation pending
          </span>
        </div>
      </div>

      {/* Classical 5-Split Summary Banner */}
      <div className="rounded-xl border border-slate-200/90 bg-white p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-slate-100 pb-3">
          <div>
            <h3 className="text-base font-semibold text-slate-900">
              Full-Cohort Classical Scaffold Validation (5 Seeds · 2,995 Compounds)
            </h3>
            <p className="text-xs text-slate-500">
              Evaluated across 1,129 unique Murcko scaffold groups with zero scaffold overlap between train, validation, and test sets.
            </p>
          </div>
          <span className="rounded bg-teal-50 text-teal-800 border border-teal-200 px-2.5 py-0.5 text-xs font-semibold">
            Mean &plusmn; Sample Std Dev
          </span>
        </div>

        <div className="mt-5 grid gap-4 md:grid-cols-2">
          {/* RBF-SVR */}
          <div className="rounded-xl border border-slate-200 bg-slate-50/70 p-5">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-bold text-slate-900">RBF-SVR (Classical Baseline)</h4>
              <span className="rounded bg-slate-200 text-slate-700 text-[10px] font-semibold px-2 py-0.5">
                128-dim TruncatedSVD
              </span>
            </div>
            <div className="mt-4 grid grid-cols-3 gap-2 border-t border-slate-200 pt-3">
              <div>
                <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500">MAE (pIC50)</p>
                <p className="font-data mt-1 text-base font-bold text-slate-900">0.5607 ± 0.0689</p>
                <p className="text-[10px] text-slate-400">Lower is better</p>
              </div>
              <div>
                <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500">RMSE</p>
                <p className="font-data mt-1 text-base font-bold text-slate-900">0.7609 ± 0.0883</p>
                <p className="text-[10px] text-slate-400">Lower is better</p>
              </div>
              <div>
                <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500">R² Score</p>
                <p className="font-data mt-1 text-base font-bold text-emerald-700">0.6061 ± 0.0496</p>
                <p className="text-[10px] text-slate-400">Higher is better</p>
              </div>
            </div>
          </div>

          {/* Random Forest */}
          <div className="rounded-xl border border-slate-200 bg-slate-50/70 p-5">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-bold text-slate-900">Random Forest (Classical Baseline)</h4>
              <span className="rounded bg-slate-200 text-slate-700 text-[10px] font-semibold px-2 py-0.5">
                2048 Morgan Fingerprint
              </span>
            </div>
            <div className="mt-4 grid grid-cols-3 gap-2 border-t border-slate-200 pt-3">
              <div>
                <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500">MAE (pIC50)</p>
                <p className="font-data mt-1 text-base font-bold text-slate-900">0.5270 ± 0.0672</p>
                <p className="text-[10px] text-slate-400">Lower is better</p>
              </div>
              <div>
                <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500">RMSE</p>
                <p className="font-data mt-1 text-base font-bold text-slate-900">0.7286 ± 0.0758</p>
                <p className="text-[10px] text-slate-400">Lower is better</p>
              </div>
              <div>
                <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500">R² Score</p>
                <p className="font-data mt-1 text-base font-bold text-emerald-700">0.6386 ± 0.0394</p>
                <p className="text-[10px] text-slate-400">Higher is better</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Visualization 2: Matched 16D Quantum-Kernel Pilot Charts */}
      <PilotMatchedComparatorChart />

      {/* Deep Interactive Classical & Quantum Drill-Down (Embeds BenchmarkResults) */}
      <div className="rounded-xl border border-slate-200/90 bg-white p-6 shadow-sm">
        <h3 className="text-base font-semibold text-slate-900 mb-2">
          Full Interactive Benchmark Reports &amp; Split Inspector
        </h3>
        <p className="text-xs text-slate-500 mb-6">
          Detailed per-split metrics across all five seeds (11, 23, 42, 87, 101), dataset curation criteria, and scientific methodology.
        </p>

        <BenchmarkResults />
      </div>
    </div>
  );
}
