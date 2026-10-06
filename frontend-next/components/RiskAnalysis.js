import { isNum } from "@/lib/analysis";
import { RISK_STYLES } from "./CandidateCard";

const LEVELS = [
  { key: "low", label: "Low", text: "text-emerald-300", bar: "bg-emerald-400", ring: "border-emerald-400/25 bg-emerald-400/[0.06]" },
  { key: "medium", label: "Medium", text: "text-amber-300", bar: "bg-amber-400", ring: "border-amber-400/25 bg-amber-400/[0.06]" },
  { key: "high", label: "High", text: "text-red-300", bar: "bg-red-400", ring: "border-red-400/25 bg-red-400/[0.06]" },
];

export default function RiskAnalysis({ derived }) {
  const { riskDistribution: dist, candidates, riskStep } = derived;

  if (!dist) {
    return (
      <section id="risk" className="scroll-mt-24">
        <h2 className="section-title">Risk Analysis</h2>
        <div className="panel mt-4 p-5 text-sm text-slate-400">
          {riskStep?.status === "error"
            ? `The risk stage reported an error: ${riskStep?.data?.error || "no detail returned"}`
            : "No risk distribution was returned in this response."}
        </div>
      </section>
    );
  }

  const total = LEVELS.reduce((sum, l) => sum + (isNum(dist[l.key]) ? dist[l.key] : 0), 0);
  const withRisk = candidates.filter((c) => c.riskLevel);

  return (
    <section id="risk" className="scroll-mt-24">
      <div className="mb-5">
        <h2 className="section-title">Risk Analysis</h2>
        <p className="mt-1.5 max-w-2xl text-sm text-slate-400">
          Computationally predicted risk profile with structural alerts. These
          are in-silico estimates, not toxicity measurements.
        </p>
      </div>

      <div className="panel p-5 md:p-6">
        <div className="grid gap-3 sm:grid-cols-3">
          {LEVELS.map((l) => (
            <div key={l.key} className={`rounded-xl border p-4 ${l.ring}`}>
              <p className="metric-label">{l.label} risk</p>
              <p className={`font-data mt-2 text-4xl font-semibold ${l.text}`}>
                {isNum(dist[l.key]) ? dist[l.key] : 0}
              </p>
              <p className="mt-1 text-[11px] text-slate-500">
                {total > 0 ? `${Math.round(((dist[l.key] || 0) / total) * 100)}% of candidates` : "—"}
              </p>
            </div>
          ))}
        </div>

        {total > 0 && (
          <div
            className="mt-5 flex h-2.5 overflow-hidden rounded-full bg-white/[0.06]"
            role="img"
            aria-label={`Risk distribution: ${dist.low || 0} low, ${dist.medium || 0} medium, ${dist.high || 0} high`}
          >
            {LEVELS.map((l) =>
              (dist[l.key] || 0) > 0 ? (
                <div key={l.key} className={`${l.bar} h-full`} style={{ width: `${((dist[l.key] || 0) / total) * 100}%` }} />
              ) : null,
            )}
          </div>
        )}

        {withRisk.length > 0 && (
          <ul className="mt-6 divide-y divide-white/[0.05] border-t border-white/[0.06]">
            {withRisk.map((c) => (
              <li key={c.id} className="flex flex-wrap items-start justify-between gap-3 py-3">
                <div className="min-w-0">
                  <p className="font-data text-sm text-slate-100">{c.id}</p>
                  {c.riskFlags.length > 0 && (
                    <p className="mt-1 max-w-xl text-xs leading-5 text-slate-500">
                      {c.riskFlags.slice(0, 3).join(" · ")}
                    </p>
                  )}
                </div>
                <span className={`badge ${RISK_STYLES[c.riskLevel] || RISK_STYLES.medium}`}>{c.riskLevel}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}
