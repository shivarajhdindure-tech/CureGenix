"use client";

import { DESTINATIONS } from "./Sidebar";

export default function TopBar({
  activeWorkspace,
  onOpenMobile,
  phase = "idle",
  engine = "checking",
  targetInfo = null,
  onStartAnalysis = null,
  onReset = null,
  onCancel = null,
  canStart = false,
  onChangeStructure = null,
}) {
  const currentDest = DESTINATIONS.find((d) => d.id === activeWorkspace) || DESTINATIONS[0];

  const phaseConfig = {
    idle: { label: "Ready", pill: "bg-slate-100 text-slate-700 border-slate-200" },
    running: { label: "Pipeline Running", pill: "bg-teal-50 text-teal-800 border-teal-200 animate-pulse" },
    done: { label: "Analysis Complete", pill: "bg-emerald-50 text-emerald-800 border-emerald-200" },
    error: { label: "Execution Notice", pill: "bg-rose-50 text-rose-800 border-rose-200" },
  }[phase] || { label: "Idle", pill: "bg-slate-100 text-slate-700 border-slate-200" };

  return (
    <header className="sticky top-0 z-30 flex h-16 w-full items-center justify-between border-b border-slate-200/90 bg-white/95 px-4 sm:px-6 lg:px-8 backdrop-blur-md">
      {/* Left: Mobile Toggle + Breadcrumb */}
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onOpenMobile}
          aria-label="Open navigation menu"
          className="rounded-lg p-2 text-slate-600 hover:bg-slate-100 hover:text-slate-900 lg:hidden"
        >
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>

        <div className="flex items-center gap-2 text-sm">
          <span className="hidden font-medium text-slate-400 sm:inline">CureGenix Discovery</span>
          <span className="hidden text-slate-300 sm:inline">/</span>
          <h1 className="text-base font-semibold text-slate-900 sm:text-lg">
            {currentDest.label}
          </h1>
        </div>
      </div>

      {/* Right: Status Pill & Actions */}
      <div className="flex items-center gap-3">
        {/* Target Indicator */}
        <div className="hidden md:flex items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 px-3 py-1 text-xs">
          <span className="text-slate-500 font-medium">Target:</span>
          <span className="font-semibold text-slate-800 font-mono">
            {targetInfo?.pdbId ? `${targetInfo.pdbId} (Chain ${targetInfo.chain || "A"})` : "None"}
          </span>
          {onChangeStructure && (
            <button
              type="button"
              onClick={onChangeStructure}
              className="ml-1 text-[11px] font-bold text-teal-700 hover:text-teal-900 underline"
            >
              Change
            </button>
          )}
        </div>

        {/* Phase Pill */}
        <div className={`hidden sm:inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium ${phaseConfig.pill}`}>
          <span className={`h-1.5 w-1.5 rounded-full ${phase === "running" ? "bg-teal-500 animate-ping" : phase === "done" ? "bg-emerald-500" : "bg-slate-400"}`} />
          {phaseConfig.label}
        </div>

        {/* Action Button */}
        {phase === "running" ? (
          <button
            type="button"
            onClick={onCancel}
            className="rounded-lg border border-rose-300 bg-rose-50 px-3 py-1.5 text-xs font-semibold text-rose-700 hover:bg-rose-100 transition"
          >
            Cancel Run
          </button>
        ) : phase === "done" ? (
          <button
            type="button"
            onClick={onReset}
            className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 hover:border-slate-400 transition shadow-sm"
          >
            New Analysis
          </button>
        ) : (
          <button
            type="button"
            onClick={onStartAnalysis}
            disabled={!canStart}
            className="rounded-lg bg-teal-600 px-3.5 py-1.5 text-xs font-semibold text-white shadow-sm hover:bg-teal-700 disabled:opacity-40 disabled:cursor-not-allowed transition"
          >
            Run Pipeline
          </button>
        )}
      </div>
    </header>
  );
}
