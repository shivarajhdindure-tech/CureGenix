import { isNum } from "@/lib/analysis";
import { CompletedPipeline } from "./AnalysisPipeline";
import CandidateCard from "./CandidateCard";
import QuantumAnalysis from "./QuantumAnalysis";
import CandidateComparison from "./CandidateComparison";
import RiskAnalysis from "./RiskAnalysis";
import Prioritization from "./Prioritization";
import TechnicalDetails from "./TechnicalDetails";

function SummaryCard({ label, value, sub, accent }) {
  return (
    <div className="panel animate-fadeUp p-5">
      <p className="metric-label">{label}</p>
      <p
        className={`font-data mt-3 break-all text-2xl font-semibold tracking-tight sm:text-3xl ${
          accent || "text-white"
        }`}
      >
        {value}
      </p>
      {sub && <p className="mt-1 text-xs text-slate-500">{sub}</p>}
    </div>
  );
}

export default function ResultsDashboard({ result, derived, onReset }) {
  const { summaryCounts, bestNovelId, durationMs, candidates, proteinInfo, lightMolecules, vqeMolecules } = derived;

  const featured = derived.bestNovel;
  const others = candidates.filter((c) => c !== featured);

  const chains = Array.isArray(proteinInfo.chains) ? proteinInfo.chains.length : null;
  const infoChips = [
    result.protein?.pdb_id && { k: "PDB", v: result.protein.pdb_id },
    chains != null && chains > 0 && { k: "Chains", v: chains },
    isNum(proteinInfo.sequence_length) && proteinInfo.sequence_length > 0 && { k: "Residues", v: proteinInfo.sequence_length },
    isNum(proteinInfo.binding_sites_count) && { k: "Binding sites", v: proteinInfo.binding_sites_count },
  ].filter(Boolean);

  return (
    <div className="space-y-12">
      {/* Title */}
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div className="min-w-0">
          <p className="eyebrow !text-emerald-300/80">Analysis complete</p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight text-white md:text-4xl">
            {result.protein_name || result.protein?.name || "Molecular Analysis"}
          </h1>
          {result.summary && <p className="mt-2 text-sm text-slate-400">{result.summary}</p>}
          {infoChips.length > 0 && (
            <ul className="mt-4 flex flex-wrap gap-2">
              {infoChips.map((c) => (
                <li key={c.k} className="rounded-md border border-white/10 bg-white/[0.03] px-2.5 py-1 text-xs text-slate-400">
                  {c.k} <span className="font-data ml-1 text-slate-100">{c.v}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
        <button type="button" onClick={onReset} className="btn-ghost">
          Analyze another structure
        </button>
      </div>

      {/* Lightweight-mode notice */}
      {lightMolecules.length > 0 && vqeMolecules.length === 0 && (
        <div role="note" className="rounded-xl border border-amber-400/30 bg-amber-400/[0.06] p-4 text-sm text-amber-100">
          This backend is running in lightweight descriptor mode. The quantum
          stage returned RDKit molecular descriptors only; VQE was not run for
          these results.
        </div>
      )}

      {/* Summary cards */}
      <div className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
        <SummaryCard label="Candidates analyzed" value={summaryCounts.analyzed} />
        <SummaryCard
          label="Quantum evaluated"
          value={summaryCounts.quantumEvaluated}
          accent="text-cyan-300"
          sub={summaryCounts.quantumTargeted != null ? `of ${summaryCounts.quantumTargeted} novel candidates` : undefined}
        />
        <SummaryCard label="Best novel candidate" value={bestNovelId || "—"} accent="text-emerald-300" />
        <SummaryCard
          label="Analysis time"
          value={isNum(durationMs) ? `${Math.round(durationMs / 1000)}s` : "—"}
          sub={isNum(durationMs) ? "end-to-end pipeline" : undefined}
        />
      </div>

      <CompletedPipeline steps={derived.steps} />

      {/* Candidates */}
      <section id="candidates" className="scroll-mt-24">
        <div className="mb-5">
          <h2 className="section-title">Candidates</h2>
          <p className="mt-1.5 max-w-2xl text-sm text-slate-400">
            All candidates evaluated in this run, ordered by pipeline rank.
          </p>
        </div>
        {candidates.length === 0 ? (
          <div className="panel p-5 text-sm text-slate-400">No candidates were returned.</div>
        ) : (
          <div className="space-y-4">
            {featured && <CandidateCard candidate={featured} featured />}
            {others.length > 0 && (
              <div className="grid gap-4 md:grid-cols-2">
                {others.map((c) => (
                  <CandidateCard key={c.id} candidate={c} />
                ))}
              </div>
            )}
          </div>
        )}
      </section>

      <QuantumAnalysis derived={derived} />
      <CandidateComparison derived={derived} />
      <RiskAnalysis derived={derived} />
      <Prioritization derived={derived} />
      <TechnicalDetails derived={derived} />
    </div>
  );
}
