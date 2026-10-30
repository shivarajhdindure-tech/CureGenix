"use client";

import { useState } from "react";
import { fmt, isNum, API_URL } from "@/lib/analysis";
import { isSafeHttpUrl, ReferenceLink } from "./ReferenceLink.mjs";
import { getQuantumCalculationDisplay } from "@/lib/quantumCalculationDisplay.mjs";

function EvidenceRow({ label, value, status }) {
  return (
    <div className="flex flex-wrap items-start justify-between gap-3 border-b border-white/[0.06] py-3 last:border-0">
      <div>
        <p className="text-xs text-slate-400">{label}</p>
        <p className="mt-1 break-words text-sm text-slate-100">
          {value ?? "Not available"}
        </p>
      </div>
      {status && (isSafeHttpUrl(status) ? (
        <ReferenceLink href={status} className="max-w-[55%] text-right text-xs">
          {status}
        </ReferenceLink>
      ) : (
        <span className="badge border-white/10 bg-white/[0.04] text-slate-400">
          {status}
        </span>
      ))}
    </div>
  );
}

export default function EvidencePassport({ candidate: c, activeStructure = null }) {
  const [open, setOpen] = useState(false);
  const [quantumJob, setQuantumJob] = useState(null);
  const [quantumRequestError, setQuantumRequestError] = useState("");

  const verified =
    c.verificationStatus === "verified" &&
    c.targetAssociationVerified === true;

  const quantumDisplay = getQuantumCalculationDisplay(c, quantumJob);
  const q = quantumDisplay.quantum;
  const quantumBusy = quantumDisplay.status === "queued" || quantumDisplay.status === "running";

  async function runQuantumCalculation() {
    if (quantumBusy || !c.smiles || !c.id) return;
    setQuantumRequestError("");
    setQuantumJob({ status: "queued" });
    try {
      const submitted = await fetch(`${API_URL}/api/quantum-calculations`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ candidate_id: c.id, smiles: c.smiles }),
      });
      if (!submitted.ok) {
        const body = await submitted.json().catch(() => ({}));
        throw new Error(typeof body.detail === "string" ? body.detail : "Backend could not accept the calculation request.");
      }
      const accepted = await submitted.json();
      setQuantumJob({ job_id: accepted.job_id, status: accepted.status, duplicate: accepted.duplicate });

      while (true) {
        await new Promise((resolve) => setTimeout(resolve, 1500));
        const response = await fetch(`${API_URL}/api/quantum-calculations/${encodeURIComponent(accepted.job_id)}`, { cache: "no-store" });
        if (!response.ok) throw new Error("Could not retrieve the backend calculation status.");
        const current = await response.json();
        setQuantumJob(current);
        if (["completed", "failed", "skipped"].includes(current.status)) break;
      }
    } catch (error) {
      setQuantumJob(null);
      setQuantumRequestError(error instanceof Error ? error.message : "Quantum calculation request failed.");
    }
  }
  const screening = c.screening;
  const provenance = c.candidateMetadata;

  return (
    <section className="mt-5 overflow-hidden rounded-xl border border-cyan-400/20 bg-cyan-400/[0.025]">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
        className="flex w-full items-center justify-between gap-3 p-4 text-left transition hover:bg-white/[0.03] focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300"
      >
        <div>
          <p className="text-sm font-semibold text-cyan-200">
            Evidence Passport
          </p>
          <p className="mt-1 text-xs text-slate-400">
            Inspect data provenance, calculations, and evidence gaps
          </p>
        </div>
        <span className="text-slate-400" aria-hidden="true">
          {open ? "−" : "+"}
        </span>
      </button>

      {open && (
        <div className="space-y-5 border-t border-white/[0.06] p-4">
          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-300">
              01 · Identity and verification
            </h4>
            <div className="mt-2">
              <EvidenceRow label="Candidate ID" value={c.id} />
              <EvidenceRow
                label="Candidate category"
                value={c.category || "Unknown"}
              />
              <EvidenceRow
                label="Structure (SMILES)"
                value={c.smiles}
                status={c.smiles ? "Provided" : "Missing"}
              />
              <EvidenceRow
                label="Structure verification"
                value={c.verificationStatus || "not_verified"}
                status={
                  c.verificationStatus === "verified"
                    ? "Identity status reported verified"
                    : "Not verified"
                }
              />
              <EvidenceRow
                label="Target association"
                value={
                  c.targetAssociationVerified
                    ? "Reported verified"
                    : "Not verified"
                }
                status={
                  c.targetAssociationVerified
                    ? "Verified status reported"
                    : "Evidence gap"
                }
              />
              {provenance && (
                <>
                  <EvidenceRow
                    label="Target-informed context"
                    value={`${activeStructure?.proteinName || provenance.target?.name || "Unknown target"} (${activeStructure?.targetAccession || provenance.target?.uniprot_id || "no accession"}); ${provenance.target?.identity_state || "unresolved"}; chain ${activeStructure?.selectedChainId || provenance.target?.selected_chain_id || "not selected"}`}
                  />
                  <EvidenceRow label="Target Structure PDB ID" value={activeStructure?.pdbId || "Not established"} />
                  {activeStructure?.sha256 && (
                    <EvidenceRow label="Structure Checksum" value={activeStructure.sha256.slice(0, 16) + "…"} />
                  )}
                  <EvidenceRow label="Identity source" value={provenance.target?.identity_source} />
                  <EvidenceRow label="Identity warnings" value={(provenance.target?.warnings || []).join(" ") || "None"} />
                  {provenance.target?.evidence?.sequence_validation && (
                    <>
                      <EvidenceRow
                        label="Sequence validation"
                        value={provenance.target.evidence.sequence_validation.identity_state}
                        status={provenance.target.evidence.sequence_validation.validation_outcome}
                      />
                      <EvidenceRow
                        label="Sequence identity and coverage"
                        value={`${Number(provenance.target.evidence.sequence_validation.identity_percent || 0).toFixed(1)}% identity · ${(Number(provenance.target.evidence.sequence_validation.observed_chain_coverage || 0) * 100).toFixed(1)}% observed coverage · ${(Number(provenance.target.evidence.sequence_validation.reference_sequence_coverage || 0) * 100).toFixed(1)}% reference coverage`}
                      />
                    </>
                  )}
                  <EvidenceRow
                    label="Reference scaffold"
                    value={`${provenance.scaffold_provenance?.scaffold_name || "Unknown"} from ${provenance.scaffold_provenance?.reference_compound || "unknown compound"} (${provenance.scaffold_provenance?.reference_chembl_id || "no ChEMBL ID"})`}
                  />
                  <EvidenceRow
                    label="Generation method"
                    value={provenance.generation_method?.name}
                    status="Hypothesis only"
                  />
                  <EvidenceRow
                    label="Rationale and source"
                    value={provenance.scaffold_provenance?.rationale}
                  />
                  {(provenance.scaffold_provenance?.sources || []).map((source) => (
                    <EvidenceRow key={source.url} label="Reference source" value={source.name} status={source.url} />
                  ))}
                </>
              )}
            </div>
          </div>

          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-300">
              02 · Classical screening
            </h4>
            <div className="mt-2">
              {screening ? (
                <>
                  <EvidenceRow
                    label="Drug-likeness score"
                    value={
                      isNum(screening.drug_likeness)
                        ? fmt(screening.drug_likeness, 3)
                        : "Not available"
                    }
                    status="Computed"
                  />
                  <EvidenceRow
                    label="BBB permeability score"
                    value={
                      isNum(screening.bbb_permeability)
                        ? fmt(screening.bbb_permeability, 3)
                        : "Not available"
                    }
                    status="Computed"
                  />
                  <EvidenceRow
                    label="Potency proxy"
                    value={
                      isNum(screening.potency_proxy)
                        ? fmt(screening.potency_proxy, 3)
                        : "Not available"
                    }
                    status="Heuristic"
                  />
                  <EvidenceRow
                    label="Toxicity penalty"
                    value={
                      isNum(screening.toxicity_penalty)
                        ? fmt(screening.toxicity_penalty, 3)
                        : "Not available"
                    }
                    status="Heuristic"
                  />
                </>
              ) : (
                <p className="mt-2 text-sm text-slate-400">
                  Screening data was not included in this response.
                </p>
              )}
            </div>
          </div>

          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-300">
              03 · Quantum calculation
            </h4>
            <div className="mt-2">
              <EvidenceRow
                label="Calculation status"
                value={quantumDisplay.status === "completed" ? "completed · VQE result available" : quantumDisplay.status === "skipped" ? "skipped_resource_limit" : quantumDisplay.status}
                status={
                  quantumDisplay.status === "completed" || c.quantumState === "vqe"
                    ? "VQE result available"
                    : quantumDisplay.status === "running" || quantumDisplay.status === "queued"
                      ? "Calculation in progress"
                      : "No VQE result available"
                }
              />
              <EvidenceRow
                label="HOMO–LUMO gap"
                value={
                  q && isNum(q.homo_lumo_gap_hartree)
                    ? `${fmt(q.homo_lumo_gap_hartree)} Ha`
                    : "Not available"
                }
              />
              <EvidenceRow
                label="VQE electronic energy"
                value={
                  q && isNum(q.vqe?.electronic_energy_hartree)
                    ? `${fmt(q.vqe.electronic_energy_hartree)} Ha`
                    : "Not available"
                }
              />
              <EvidenceRow
                label="Total molecular energy"
                value={q && isNum(q.vqe?.total_molecular_energy_hartree)
                  ? `${fmt(q.vqe.total_molecular_energy_hartree)} Ha`
                  : "Not available"}
              />
              <EvidenceRow
                label="Optimizer status"
                value={q?.vqe?.optimizer_status_available
                  ? (q.vqe.optimizer_success ? "Reported converged" : "Reported not converged")
                  : "Not reported by optimizer"}
              />
              {quantumJob?.experiment_record_id && (
                <EvidenceRow label="Experiment record" value={quantumJob.experiment_record_id} />
              )}
              {isNum(quantumJob?.elapsed_seconds) && (
                <EvidenceRow label="Calculation elapsed time" value={`${quantumJob.elapsed_seconds.toFixed(2)} s`} />
              )}
              {quantumDisplay.message && quantumDisplay.status !== "completed" && (
                <div role="status" className={`mt-2 rounded-lg border p-3 text-xs leading-5 ${quantumDisplay.status === "failed" ? "border-red-400/25 bg-red-400/[0.05] text-red-200" : "border-amber-400/25 bg-amber-400/[0.05] text-amber-100"}`}>
                  {quantumDisplay.message}
                  {quantumDisplay.eligibilityReasons.length > 0 && (
                    <ul className="mt-1 list-disc pl-4">{quantumDisplay.eligibilityReasons.map((reason) => <li key={reason}>{reason}</li>)}</ul>
                  )}
                </div>
              )}
              {c.smiles && c.id && (
                <div className="mt-3">
                  <button type="button" onClick={runQuantumCalculation} disabled={quantumBusy} aria-busy={quantumBusy} className="rounded-lg border border-cyan-300/30 bg-cyan-300/10 px-3 py-2 text-xs font-semibold text-cyan-100 transition hover:bg-cyan-300/20 disabled:cursor-wait disabled:opacity-60">
                    {quantumBusy ? "Running quantum calculation…" : "Run Quantum Calculations"}
                  </button>
                  <p className="mt-1 text-[11px] leading-4 text-slate-500">Runs only after this button is selected. Resource eligibility safeguards remain active.</p>
                  {quantumRequestError && <p role="alert" className="mt-2 text-xs text-red-200">{quantumRequestError}</p>}
                </div>
              )}
              <p className="mt-2 text-xs leading-5 text-slate-400">
                Quantum-derived descriptors are computational results.
                They do not establish target binding, clinical efficacy,
                or quantum advantage.
              </p>
            </div>
          </div>

          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-300">
              04 · Evidence gaps
            </h4>
            <ul className="mt-2 space-y-2 text-sm leading-5 text-slate-300">
              {!verified && (
                <li>
                  • Drug identity/approval and association with the analyzed
                  target have not both been verified.
                </li>
              )}
              {c.structuralAlertCount === 0 && (
                <li>
                  • No configured structural alerts were detected. This
                  does not establish safety or exclude toxicity.
                </li>
              )}
              {c.quantumState !== "vqe" && quantumDisplay.status !== "completed" && (
                <li>
                  {quantumDisplay.status === "skipped" || c.quantumState === "resource_skipped"
                    ? `• Quantum calculation was skipped by resource policy: ${quantumDisplay.message || "molecule exceeded a configured eligibility limit"}.`
                    : quantumDisplay.status === "failed" || c.quantumState === "failed"
                      ? `• Quantum calculation failed: ${quantumDisplay.message || "no failure detail available"}.`
                      : "• A successful VQE result is not available for this candidate."}
                </li>
              )}
              <li>
                • Candidate-specific source citations and experimental
                validation evidence are not available in the current
                candidate data.
              </li>
            </ul>
          </div>

          <p className="rounded-lg border border-amber-400/20 bg-amber-400/[0.05] p-3 text-xs leading-5 text-amber-100/80">
            Evidence note: this passport summarizes the fields returned by
            the current CureGenix pipeline. A reported verification status
            is not independent proof, and missing evidence must not be
            interpreted as a positive result.
          </p>
        </div>
      )}
    </section>
  );
}
