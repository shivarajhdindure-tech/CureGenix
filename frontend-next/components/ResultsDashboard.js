import { isNum } from "@/lib/analysis";
import { getNoVqeResourceSkipDisclosure } from "@/lib/candidateTransparency.mjs";
import { CompletedPipeline } from "./AnalysisPipeline";
import CandidateCard from "./CandidateCard";
import QuantumAnalysis from "./QuantumAnalysis";
import CandidateComparison from "./CandidateComparison";
import RiskAnalysis from "./RiskAnalysis";
import Prioritization from "./Prioritization";
import TechnicalDetails from "./TechnicalDetails";
import DiscoveryStrategySimulator from "./DiscoveryStrategySimulator";
import Molecule3DExplorer from "./Molecule3DExplorer";
import QuantumKernelLab from "./QuantumKernelLab";
import BenchmarkResults from "./BenchmarkResults";
import MolecularActivityComparison from "./MolecularActivityComparison";

function SummaryCard({ label, value, sub, accent }) {
  return (
    <div className="panel animate-fadeUp p-5">
      <p className="metric-label">{label}</p>
      <p
        className={`font-data mt-3 break-all text-2xl font-semibold tracking-tight sm:text-3xl ${
          accent || "text-white"
        }`}>
        {value}
      </p>
      {sub && <p className="mt-1 text-xs text-slate-500">{sub}</p>}
    </div>
  );
}

export default function ResultsDashboard({ result, derived, onReset }) {
  const {
    summaryCounts,
    bestNovelId,
    bestNovelCandidates = [],
    bestNovelIsTie = false,
    hasScoreTies = false,
    durationMs,
    candidates,
    demonstrationCandidates = [],
    proteinInfo,
    lightMolecules,
    vqeMolecules,
  } = derived;

  const featured = derived.bestNovel;
  const noVqeDisclosure = getNoVqeResourceSkipDisclosure({
    candidateCount: candidates.length,
    vqeCount: vqeMolecules.length,
    skippedCount: derived.resourceSkippedMolecules?.length || 0,
  });
  const generationStatus = result.candidate_generation || {};
  const identity = proteinInfo.target_identity || {};
  const sequenceValidation = identity.sequence_validation || null;
  const others = candidates.filter((c) => c !== featured);

  const chains = Array.isArray(proteinInfo.chains)
    ? proteinInfo.chains.length
    : null;
  const infoChips = [
    result.protein?.pdb_id && { k: "PDB", v: result.protein.pdb_id },
    proteinInfo.target_identity?.uniprot_id && {
      k: "Verified target",
      v: `${proteinInfo.target_identity.protein_name} (${proteinInfo.target_identity.uniprot_id})`,
    },
    !proteinInfo.target_identity?.uniprot_id &&
      proteinInfo.target_identity?.identity_status && {
        k: "Target status",
        v: proteinInfo.target_identity.identity_status,
      },
    chains != null && chains > 0 && { k: "Chains", v: chains },
    isNum(proteinInfo.sequence_length) &&
      proteinInfo.sequence_length > 0 && {
        k: "Residues",
        v: proteinInfo.sequence_length,
      },
    isNum(proteinInfo.binding_sites_count) && {
      k: "Binding sites",
      v: proteinInfo.binding_sites_count,
    },
  ].filter(Boolean);

  return (
    <div className="space-y-12">
      {/* Title */}
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div className="min-w-0">
          <p className="eyebrow !text-emerald-300/80">Analysis complete</p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight text-white md:text-4xl">
            {result.protein_name ||
              result.protein?.name ||
              "Molecular Analysis"}
          </h1>
          {result.summary && (
            <p className="mt-2 text-sm text-slate-400">{result.summary}</p>
          )}
          {infoChips.length > 0 && (
            <ul className="mt-4 flex flex-wrap gap-2">
              {infoChips.map((c) => (
                <li
                  key={c.k}
                  className="rounded-md border border-white/10 bg-white/[0.03] px-2.5 py-1 text-xs text-slate-400">
                  {c.k}{" "}
                  <span className="font-data ml-1 text-slate-100">{c.v}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
        <button type="button" onClick={onReset} className="btn-ghost">
          Analyze another structure
        </button>
      </div>

      {(generationStatus.warning || generationStatus.claims || identity.warnings?.length > 0) && (
        <div role="note" className="rounded-xl border border-amber-400/30 bg-amber-400/[0.06] p-4 text-sm leading-6 text-amber-100">
          {generationStatus.warning || identity.warnings?.[0] || "Candidate generation status is available."}
          {generationStatus.claims && <p className="mt-1 text-amber-100/80">{generationStatus.claims}</p>}
          {identity.identity_source && <p className="mt-1 text-amber-100/80">Identity source: {identity.identity_source}. Chain: {identity.selected_chain_id || "not selected"}.</p>}
          {identity.chain_accessions && <p className="mt-1 break-words text-amber-100/80">PDB chain mappings: {Object.entries(identity.chain_accessions).map(([chain, accessions]) => `${chain || "(blank)"}: ${accessions.join(", ")}`).join("; ") || "none"}</p>}
          {identity.uniprot_lookup?.status && <p className="mt-1 text-amber-100/80">UniProt lookup: {identity.uniprot_lookup.status}</p>}
          {sequenceValidation && (
            <div className="mt-3 rounded-lg border border-white/10 bg-black/10 p-3 text-amber-100/90">
              <p className="font-semibold">Chain sequence check: {sequenceValidation.validation_outcome || "not available"}</p>
              <p className="mt-1">{sequenceValidation.aligned_observed_residue_count ?? 0} aligned informative residues · {Number.isFinite(sequenceValidation.identity_percent) ? `${sequenceValidation.identity_percent.toFixed(1)}% identity` : "identity unavailable"}</p>
              <p>Observed-chain coverage: {Number.isFinite(sequenceValidation.observed_chain_coverage) ? `${(sequenceValidation.observed_chain_coverage * 100).toFixed(1)}%` : "—"} · Full UniProt reference coverage: {Number.isFinite(sequenceValidation.reference_sequence_coverage) ? `${(sequenceValidation.reference_sequence_coverage * 100).toFixed(1)}%` : "—"}</p>
              <p>Substitutions: {sequenceValidation.substitution_count ?? "—"} · Insertions: {sequenceValidation.insertion_count ?? "—"} · Deletions: {sequenceValidation.deletion_count ?? "—"}</p>
              {(sequenceValidation.warnings || []).map((warning, index) => <p key={`seq-${index}`} className="mt-1 text-amber-100/75">{warning}</p>)}
              {sequenceValidation.aligned_observed_sequence && (
                <details className="mt-2">
                  <summary className="cursor-pointer">Alignment evidence</summary>
                  <pre className="mt-2 overflow-x-auto whitespace-pre-wrap break-all rounded bg-black/20 p-2 text-xs">Observed: {sequenceValidation.aligned_observed_sequence}{"\n"}UniProt:  {sequenceValidation.aligned_reference_sequence}</pre>
                </details>
              )}
              {sequenceValidation.identity_state === "structure_linked_partial_sequence_support" && <p className="mt-2 text-amber-100/80">Partial sequence correspondence meets the configured policy; it does not establish target function or binding.</p>}
            </div>
          )}
          {identity.dbref_records?.length > 0 && (
            <details className="mt-2">
              <summary className="cursor-pointer text-amber-100/90">PDB DBREF evidence</summary>
              <pre className="mt-2 overflow-x-auto whitespace-pre-wrap break-all rounded bg-black/20 p-2 text-xs text-amber-100/70">{identity.dbref_records.map((record) => `Line ${record.line_number} · chain ${record.chain_id || "(blank)"} · ${record.accession || "missing accession"}\n${record.raw_record || ""}`).join("\n")}</pre>
            </details>
          )}
          {(identity.warnings || []).map((warning, index) => <p key={`${index}-${warning}`} className="mt-1 text-amber-100/80">{warning}</p>)}
        </div>
      )}

      {noVqeDisclosure && (
        <div role="note" className="rounded-xl border border-amber-400/30 bg-amber-400/[0.06] p-4 text-sm leading-6 text-amber-100">
          <p className="font-semibold">{noVqeDisclosure.title}</p>
          <p className="mt-1 text-amber-100/80">{noVqeDisclosure.body}</p>
        </div>
      )}

      {/* Lightweight-mode notice */}
      {lightMolecules.length > 0 && vqeMolecules.length === 0 && (
        <div
          role="note"
          className="rounded-xl border border-amber-400/30 bg-amber-400/[0.06] p-4 text-sm text-amber-100">
          This backend is running in lightweight descriptor mode. The quantum
          stage returned RDKit molecular descriptors only; VQE was not run for
          these results.
        </div>
      )}

      {/* Summary cards */}
      <div className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
        <SummaryCard
          label="Candidates analyzed"
          value={summaryCounts.analyzed}
        />
        <SummaryCard
          label="Quantum evaluated"
          value={summaryCounts.quantumEvaluated}
          accent="text-cyan-300"
          sub={
            summaryCounts.quantumTargeted != null
              ? `of ${summaryCounts.quantumTargeted} novel candidates`
              : undefined
          }
        />
        <SummaryCard
          label={bestNovelIsTie ? "Top novel score · tie" : "Best novel candidate"}
          value={bestNovelIsTie ? bestNovelCandidates.map((c) => c.id).join(" / ") : bestNovelId || "—"}
          accent={bestNovelIsTie ? "text-sky-200" : "text-emerald-300"}
          sub={bestNovelIsTie ? "Equal adjusted scores; no score-based winner." : undefined}
        />
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
            Candidates are shown in adjusted-score order. Equal displayed scores are ties.
          </p>
        </div>
        {hasScoreTies && (
          <p role="note" className="mb-4 rounded-lg border border-sky-400/20 bg-sky-400/[0.05] p-3 text-xs leading-5 text-sky-100/90">
            The ranking has no secondary scientific tie-breaker. The backend sort preserves incoming candidate order when adjusted scores are equal; that order does not imply superiority.
          </p>
        )}
        {candidates.length === 0 ? (
          <div className="panel p-5 text-sm text-slate-400">
            No eligible non-mock candidates are available for primary ranking.
            Check the demonstration references below, if any, or run another
            analysis.
          </div>
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
      {demonstrationCandidates.length > 0 && (
        <section className="scroll-mt-24">
          <div className="mb-5">
            <h2 className="section-title">Demonstration references</h2>
            <p className="mt-1.5 max-w-2xl text-sm text-slate-400">
              Mock reference compounds shown for pipeline demonstration only.
              They are not verified drugs and are excluded from primary ranking.
            </p>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            {demonstrationCandidates.map((candidate) => (
              <CandidateCard key={candidate.id} candidate={candidate} />
            ))}
          </div>
        </section>
      )}

      <DiscoveryStrategySimulator candidates={candidates} />

      <Molecule3DExplorer
        candidates={[...candidates, ...demonstrationCandidates]}
      />

      <QuantumKernelLab />

      <MolecularActivityComparison />

      <BenchmarkResults />

      <QuantumAnalysis derived={derived} />
      <CandidateComparison derived={derived} />
      <RiskAnalysis derived={derived} />
      <Prioritization derived={derived} />
      <TechnicalDetails derived={derived} />
    </div>
  );
}
