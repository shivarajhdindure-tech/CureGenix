import { STAGES, fmtClock, fmtSeconds } from "@/lib/analysis";

// What the quantum stage computes, in order. These are descriptions of the
// method, NOT progress claims: the API does not report sub-stage progress.
const QUANTUM_OPERATIONS = [
  "Molecular geometry preparation (RDKit)",
  "Active-space construction (HOMO-LUMO)",
  "Fermionic Hamiltonian generation (PySCF)",
  "Jordan-Wigner qubit mapping",
  "VQE optimization (statevector simulation)",
];

function OrbitalLoader() {
  return (
    <div className="relative h-28 w-28 shrink-0" aria-hidden="true">
      <div className="absolute inset-0 rounded-full bg-cyan-400/10 blur-xl animate-pulseGlow" />
      <svg viewBox="0 0 100 100" className="relative h-full w-full">
        <g className="animate-spinSlow" style={{ transformOrigin: "50px 50px", animationDuration: "6s" }}>
          <ellipse cx="50" cy="50" rx="42" ry="16" fill="none" stroke="#22d3ee" strokeOpacity="0.5" />
          <circle cx="92" cy="50" r="2.8" fill="#22d3ee" />
        </g>
        <g className="animate-spinSlowReverse" style={{ transformOrigin: "50px 50px", animationDuration: "9s" }}>
          <ellipse cx="50" cy="50" rx="42" ry="16" fill="none" stroke="#8b5cf6" strokeOpacity="0.5" transform="rotate(60 50 50)" />
          <circle cx="29" cy="13.6" r="2.6" fill="#8b5cf6" />
        </g>
        <g className="animate-spinSlow" style={{ transformOrigin: "50px 50px", animationDuration: "12s" }}>
          <ellipse cx="50" cy="50" rx="42" ry="16" fill="none" stroke="#22d3ee" strokeOpacity="0.3" transform="rotate(120 50 50)" />
        </g>
        <circle cx="50" cy="50" r="4" fill="#e0f2fe" />
      </svg>
    </div>
  );
}

function StatusIcon({ state }) {
  if (state === "completed")
    return (
      <span className="flex h-6 w-6 items-center justify-center rounded-full bg-emerald-400/15 text-emerald-300" aria-label="Completed">
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true">
          <path d="m2.5 6.2 2.3 2.3 4.7-5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </span>
    );
  if (state === "error")
    return (
      <span className="flex h-6 w-6 items-center justify-center rounded-full bg-red-400/15 text-xs font-bold text-red-300" aria-label="Error">
        !
      </span>
    );
  return (
    <span className="flex h-6 w-6 items-center justify-center rounded-full border border-white/15 text-slate-600" aria-hidden="true">
      <span className="h-1.5 w-1.5 rounded-full bg-slate-500" />
    </span>
  );
}

// ---------------------------------------------------------------------------
// Running view: shown while the single blocking API request is in flight.
// ---------------------------------------------------------------------------
export function RunningPipeline({ elapsedSeconds, onCancel }) {
  return (
    <div className="panel overflow-hidden" aria-live="polite">
      {/* indeterminate activity bar: signals work without implying % complete */}
      <div className="relative h-1 w-full overflow-hidden bg-white/5" aria-hidden="true">
        <div className="absolute inset-y-0 left-0 w-1/3 bg-gradient-to-r from-transparent via-cyan-400 to-transparent animate-sweep" />
      </div>

      <div className="p-6 md:p-8">
        <div className="flex flex-col items-start gap-6 sm:flex-row sm:items-center">
          <OrbitalLoader />
          <div className="min-w-0 flex-1">
            <p className="eyebrow">Analysis in progress</p>
            <h2 className="mt-2 text-2xl font-semibold tracking-tight text-white md:text-3xl">
              Molecular analysis running
              <span className="mx-2 text-slate-600">·</span>
              <span className="font-data text-cyan-300">{fmtClock(elapsedSeconds)}</span>
            </h2>
            <p className="mt-3 max-w-xl text-sm leading-6 text-slate-400">
              Complex quantum simulations may take several minutes on CPU-based
              infrastructure. The first request may also include backend wake-up
              time. Please keep this tab open.
            </p>
          </div>
          <button type="button" onClick={onCancel} className="btn-ghost shrink-0">
            Cancel
          </button>
        </div>

        <div className="mt-8 grid gap-6 lg:grid-cols-[1.1fr_1fr]">
          {/* Stage rail */}
          <ol className="space-y-2" aria-label="Pipeline stages">
            {STAGES.map((stage, i) => {
              const isQuantum = stage.agent === "Quantum Analysis Agent";
              return (
                <li
                  key={stage.agent}
                  className={`flex items-center gap-3 rounded-xl border px-4 py-3 ${
                    isQuantum
                      ? "border-cyan-400/30 bg-cyan-400/[0.06]"
                      : "border-white/[0.06] bg-ink-900/40"
                  }`}
                >
                  <span className="font-data w-5 text-xs text-slate-600">{String(i + 1).padStart(2, "0")}</span>
                  <StatusIcon state="pending" />
                  <div className="min-w-0 flex-1">
                    <p className={`text-sm font-medium ${isQuantum ? "text-cyan-100" : "text-slate-200"}`}>
                      {stage.label}
                    </p>
                    <p className="truncate text-xs text-slate-500">{stage.blurb}</p>
                  </div>
                  {isQuantum && (
                    <span className="badge shrink-0 animate-pulseGlow border-cyan-400/40 bg-cyan-400/10 text-cyan-300">
                      Most compute-intensive
                    </span>
                  )}
                </li>
              );
            })}
          </ol>

          {/* Quantum stage explainer */}
          <div className="panel-quantum p-5">
            <div className="flex items-center gap-2.5">
              <span className="relative flex h-2.5 w-2.5">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-cyan-400/60" />
                <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-cyan-400" />
              </span>
              <h3 className="text-base font-semibold text-white">Quantum Analysis Stage</h3>
            </div>
            <p className="mt-2 text-sm text-slate-300">
              Running VQE-based active-space molecular calculation
            </p>

            <p className="mt-5 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              What this stage computes
            </p>
            <ol className="mt-3 space-y-2.5">
              {QUANTUM_OPERATIONS.map((op, i) => (
                <li key={op} className="flex items-start gap-3 text-sm text-slate-300">
                  <span className="font-data mt-px flex h-5 w-5 shrink-0 items-center justify-center rounded-md border border-cyan-400/25 bg-cyan-400/10 text-[10px] text-cyan-300">
                    {i + 1}
                  </span>
                  {op}
                </li>
              ))}
            </ol>

            <p className="mt-5 border-t border-white/10 pt-4 text-xs leading-5 text-slate-500">
              The analysis API returns one result when the full run finishes and
              does not report stage-level progress, so stages are marked
              complete only once the backend responds.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Completed view: driven entirely by the real `steps` array in the response.
// ---------------------------------------------------------------------------
export function CompletedPipeline({ steps }) {
  const byAgent = {};
  steps.forEach((s) => {
    if (s?.agent_name) byAgent[s.agent_name] = s;
  });

  return (
    <section className="panel p-5 md:p-6" aria-label="Pipeline summary">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-300">
          Pipeline
        </h2>
        <span className="text-xs text-slate-500">Reported by the backend</span>
      </div>
      <ol className="grid gap-2 sm:grid-cols-2 lg:grid-cols-7">
        {STAGES.map((stage, i) => {
          const s = byAgent[stage.agent];
          const state = !s ? "pending" : s.status === "completed" ? "completed" : "error";
          const isQuantum = stage.agent === "Quantum Analysis Agent";
          return (
            <li
              key={stage.agent}
              className={`rounded-xl border p-3 ${
                state === "error"
                  ? "border-red-400/30 bg-red-500/[0.05]"
                  : isQuantum
                    ? "border-cyan-400/25 bg-cyan-400/[0.05]"
                    : "border-white/[0.06] bg-ink-900/40"
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-data text-[10px] text-slate-600">{String(i + 1).padStart(2, "0")}</span>
                <StatusIcon state={state} />
              </div>
              <p className="mt-2 text-xs font-medium leading-4 text-slate-200">{stage.label}</p>
              <p className="font-data mt-1 text-[10px] text-slate-500">
                {s ? fmtSeconds(s.duration_ms) : "not reported"}
              </p>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
