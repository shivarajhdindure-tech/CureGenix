import { fmt, isNum } from "@/lib/analysis";
import { RISK_STYLES } from "./CandidateCard";

export default function Prioritization({ derived }) {
  const {
    bestNovel,
    bestNovelId,
    bestNovelCandidates = [],
    bestNovelIsTie = false,
    topCandidate,
  } = derived;

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
              <p className="metric-label">{bestNovelIsTie ? "Top-scored novel candidates · tie" : "Best novel candidate"}</p>
              <p className={`font-data mt-2 break-all text-3xl font-semibold md:text-4xl ${bestNovelIsTie ? "text-sky-200" : "text-emerald-300"}`}>
                {bestNovelIsTie
                  ? bestNovelCandidates.map((candidate) => candidate.id).join(" / ")
                  : bestNovelId || "—"}
              </p>
              {bestNovel?.smiles && (
                <p className="font-data mt-3 break-all text-xs leading-5 text-slate-500">
                  {bestNovel.smiles}
                </p>
              )}
              {bestNovelIsTie && (
                <p className="mt-2 text-sm text-sky-100/80">
                  These candidates share the same adjusted score; the pipeline provides no secondary scientific tie-breaker.
                </p>
              )}
              {!bestNovelId && !bestNovelIsTie && (
                <p className="mt-2 text-sm text-slate-400">
                  No novel candidate was prioritized in this response.
                </p>
              )}
            </div>

            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
              <div className="metric">
                <p className="metric-label">Overall rank</p>
                <p className="font-data mt-2 text-xl font-semibold text-white">
                  {bestNovelIsTie ? "Tie" : isNum(bestNovel?.rank) ? `#${bestNovel.rank}` : "—"}
                </p>
              </div>
              <div className="metric">
                <p className="metric-label">Adjusted score</p>
                <p className="font-data mt-2 text-xl font-semibold text-white">
                  {fmt(bestNovelIsTie ? bestNovelCandidates[0]?.adjustedScore : bestNovel?.adjustedScore, 3)}
                </p>
              </div>
              <div className="metric">
                <p className="metric-label">Risk</p>
                <p className="mt-2">
                  {!bestNovelIsTie && bestNovel?.riskLevel ? (
                    <span
                      className={`badge ${RISK_STYLES[bestNovel.riskLevel] || RISK_STYLES.medium}`}>
                      {bestNovel.riskLevel}
                    </span>
                  ) : (
                    <span className="text-xl font-semibold text-white">—</span>
                  )}
                </p>
              </div>
            </div>
          </div>

          {topCandidate?.drug_name && topCandidate?.category !== "mock" && (
            <p className="mt-5 text-sm text-slate-400">
              {topCandidate.scoreTie ? "Top adjusted score · tie group:" : "Highest-ranked overall:"}{" "}
              <span className="font-data text-slate-200">
                {topCandidate.scoreTie
                  ? (topCandidate.tiedCandidateIds || [topCandidate.drug_name]).join(" / ")
                  : topCandidate.drug_name}
              </span>
              {topCandidate.category ? ` (${topCandidate.category})` : ""}
            </p>
          )}

          <p className="mt-6 border-t border-white/[0.08] pt-4 text-sm leading-6 text-slate-400">
            Candidate scores use screening inputs (drug-likeness, BBB score, a heuristic potency proxy, and toxicity freedom), then a rule-based risk penalty. VQE outputs are separate and are not inputs to this scoring path. This computational prioritization does not indicate that a molecule is an effective drug.
          </p>
        </div>
      </div>
    </section>
  );
}
