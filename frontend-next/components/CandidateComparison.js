import { fmt, isNum } from "@/lib/analysis";

// Neutral horizontal bars. Bar length is |value| relative to the largest |value|
// in the set; the signed value is always printed. No ranking is implied.
function BarChart({ title, note, rows, unit, digits = 4, color }) {
  const max = Math.max(...rows.map((r) => (isNum(r.value) ? Math.abs(r.value) : 0)), 0);
  return (
    <div className="metric">
      <p className="text-sm font-medium text-white">{title}</p>
      {note && <p className="mt-0.5 text-[11px] text-slate-500">{note}</p>}
      <div className="mt-4 space-y-3.5">
        {rows.map((r) => {
          const pct = max > 0 && isNum(r.value) ? (Math.abs(r.value) / max) * 100 : 0;
          return (
            <div key={r.id}>
              <div className="flex items-baseline justify-between gap-3 text-xs">
                <span className="font-data truncate text-slate-300" title={r.id}>{r.id}</span>
                <span className="font-data text-slate-100">
                  {fmt(r.value, digits)}{unit ? ` ${unit}` : ""}
                </span>
              </div>
              <div className="mt-1.5 h-2 overflow-hidden rounded-full bg-white/[0.06]">
                <div
                  className={`h-full origin-left animate-barGrow rounded-full ${color}`}
                  style={{ width: `${pct}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function CandidateComparison({ derived }) {
  const { vqeMolecules, candidates } = derived;

  const gapRows = vqeMolecules.map((m) => ({
    id: m.name,
    value: m.quantum_analysis?.homo_lumo_gap_hartree,
  }));
  const energyRows = vqeMolecules.map((m) => ({
    id: m.name,
    value: m.quantum_analysis?.vqe?.electronic_energy_hartree,
  }));
  const scoreRows = candidates
    .filter((c) => isNum(c.adjustedScore))
    .map((c) => ({ id: c.id, value: c.adjustedScore }));

  if (gapRows.length === 0 && scoreRows.length === 0) return null;

  return (
    <section id="comparison" className="scroll-mt-24">
      <div className="mb-5">
        <h2 className="section-title">Candidate Comparison</h2>
        <p className="mt-1.5 max-w-2xl text-sm text-slate-400">
          Metrics are shown as reported by the pipeline. Values are compared
          side by side without interpretation; no ranking is implied by bar
          length.
        </p>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        {gapRows.length > 0 && (
          <BarChart
            title="HOMO-LUMO gap"
            note="Quantum-analyzed candidates"
            rows={gapRows}
            unit="Ha"
            color="bg-gradient-to-r from-cyan-400/80 to-sky-400/80"
          />
        )}
        {energyRows.length > 0 && (
          <BarChart
            title="VQE electronic energy"
            note="Bar length shows magnitude; sign shown in value"
            rows={energyRows}
            unit="Ha"
            color="bg-gradient-to-r from-violet-400/80 to-fuchsia-400/80"
          />
        )}
        {scoreRows.length > 0 && (
          <BarChart
            title="Adjusted pipeline score"
            note="Risk-adjusted screening score, all candidates"
            rows={scoreRows}
            digits={3}
            color="bg-gradient-to-r from-emerald-400/80 to-teal-400/80"
          />
        )}
      </div>

      {candidates.length > 0 && (
        <div className="panel mt-4 overflow-x-auto">
          <table className="w-full min-w-[640px] text-left text-sm">
            <caption className="sr-only">Candidate comparison table</caption>
            <thead>
              <tr className="border-b border-white/[0.06] text-[11px] uppercase tracking-wider text-slate-500">
                <th scope="col" className="px-4 py-3 font-medium">Rank</th>
                <th scope="col" className="px-4 py-3 font-medium">Candidate</th>
                <th scope="col" className="px-4 py-3 font-medium">Type</th>
                <th scope="col" className="px-4 py-3 font-medium">Quantum</th>
                <th scope="col" className="px-4 py-3 text-right font-medium">Gap (Ha)</th>
                <th scope="col" className="px-4 py-3 text-right font-medium">Energy (Ha)</th>
                <th scope="col" className="px-4 py-3 text-right font-medium">Score</th>
              </tr>
            </thead>
            <tbody>
              {candidates.map((c) => {
                const q = c.quantumState === "vqe" ? c.quantum : null;
                const stateLabel = {
                  vqe: "Analyzed",
                  lightweight: "Descriptor mode",
                  skipped: "Skipped",
                  failed: "Failed",
                  none: "—",
                }[c.quantumState];
                return (
                  <tr key={c.id} className={`border-b border-white/[0.04] last:border-0 ${c.isBestNovel ? "bg-emerald-400/[0.05]" : ""}`}>
                    <td className="font-data px-4 py-3 text-slate-400">{isNum(c.rank) ? `#${c.rank}` : "—"}</td>
                    <td className="font-data px-4 py-3 text-slate-100">{c.id}</td>
                    <td className="px-4 py-3 capitalize text-slate-300">{c.category || "—"}</td>
                    <td className="px-4 py-3 text-slate-300">{stateLabel}</td>
                    <td className="font-data px-4 py-3 text-right text-slate-200">{q ? fmt(q.homo_lumo_gap_hartree) : "—"}</td>
                    <td className="font-data px-4 py-3 text-right text-slate-200">{q ? fmt(q.vqe?.electronic_energy_hartree) : "—"}</td>
                    <td className="font-data px-4 py-3 text-right text-slate-200">{fmt(c.adjustedScore, 3)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
