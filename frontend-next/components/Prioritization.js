import { fmt, isNum } from "@/lib/analysis";
import { RISK_STYLES } from "./CandidateCard";

export default function Prioritization({ derived }) {
  const { bestNovel, bestNovelId, topCandidate } = derived;

  return (
    <section id="prioritization" className="scroll-mt-24">
      <div className="relative overflow-hidden rounded-3xl border border-emerald-400/25 bg-ink-800/80 p-6 md:p-8">
        <div
          aria-hidden="true"
          className="pointer-events-none absolute -right-20 -top-20 h-64 w-64 rounded-full bg-emerald-400/10 blur-3xl"
        />
        <div className="relative">
          <p className="eyebrow !text-emerald-300/80">Final result</p>
          <h2 className="section-title mt-2">Candidate Prioritization</h2>

          <div className="mt-6 grid gap-6 md:grid-cols-[1fr_1.2fr]">
            <div>
              <p className="metric-label">Best novel candidate</p>
              <p className="font-data mt-2 break-all text-3xl font-semibold text-emerald-300 md:text-4xl">
                {bestNovelId || "—"}
              </p>
              {bestNovel?.smiles && (
                <p className="font-data mt-3 break-all text-xs leading-5 text-slate-500">{bestNovel.smiles}</p>
              )}
              {!bestNovelId && (
                <p className="mt-2 text-sm text-slate-400">
                  No novel candidate was prioritized in this response.
                </p>
              )}
            </div>

            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
              <div className="metric">
                <p className="metric-label">Overall rank</p>
                <p className="font-data mt-2 text-xl font-semibold text-white">
                  {isNum(bestNovel?.rank) ? `#${bestNovel.rank}` : "—"}
                </p>
              </div>
              <div className="metric">
                <p className="metric-label">Adjusted score</p>
                <p className="font-data mt-2 text-xl font-semibold text-white">{fmt(bestNovel?.adjustedScore, 3)}</p>
              </div>
              <div className="metric">
                <p className="metric-label">Risk</p>
                <p className="mt-2">
                  {bestNovel?.riskLevel ? (
                    <span className={`badge ${RISK_STYLES[bestNovel.riskLevel] || RISK_STYLES.medium}`}>
                      {bestNovel.riskLevel}
                    </span>
                  ) : (
                    <span className="text-xl font-semibold text-white">—</span>
                  )}
                </p>
              </div>
            </div>
          </div>

          {topCandidate?.drug_name && (
            <p className="mt-5 text-sm text-slate-400">
              Highest-ranked overall:{" "}
              <span className="font-data text-slate-200">{topCandidate.drug_name}</span>
              {topCandidate.category ? ` (${topCandidate.category})` : ""}
            </p>
          )}

          <p className="mt-6 border-t border-white/[0.08] pt-4 text-sm leading-6 text-slate-400">
            Prioritized using the combined analysis pipeline: a risk-adjusted
            screening score, with quantum-derived descriptors reported
            alongside. This is a computational ranking and does not indicate
            that the molecule is an effective drug.
          </p>
        </div>
      </div>
    </section>
  );
}
