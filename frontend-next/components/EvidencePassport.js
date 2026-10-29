"use client";

import { useState } from "react";
import { fmt, isNum } from "@/lib/analysis";

function EvidenceRow({ label, value, status }) {
  return (
    <div className="flex flex-wrap items-start justify-between gap-3 border-b border-white/[0.06] py-3 last:border-0">
      <div>
        <p className="text-xs text-slate-400">{label}</p>
        <p className="mt-1 break-words text-sm text-slate-100">
          {value ?? "Not available"}
        </p>
      </div>
      {status && (
        <span className="badge border-white/10 bg-white/[0.04] text-slate-400">
          {status}
        </span>
      )}
    </div>
  );
}

export default function EvidencePassport({ candidate: c }) {
  const [open, setOpen] = useState(false);

  const verified =
    c.verificationStatus === "verified" &&
    c.targetAssociationVerified === true;

  const q = c.quantumState === "vqe" ? c.quantum : null;
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
                    value={`${provenance.target?.name || "Unknown target"} (${provenance.target?.uniprot_id || "no accession"}); ${provenance.target?.identity_state || "unresolved"}; chain ${provenance.target?.selected_chain_id || "not selected"}`}
                  />
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
                value={c.quantumState || "Unknown"}
                status={
                  c.quantumState === "vqe"
                    ? "VQE result available"
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
              {c.quantumState !== "vqe" && (
                <li>
                  {c.quantumState === "resource_skipped"
                    ? `• Quantum calculation was skipped by resource policy: ${c.quantum?.message || "molecule exceeded a configured eligibility limit"}.`
                    : c.quantumState === "failed"
                      ? `• Quantum calculation failed: ${c.quantum?.message || "no failure detail available"}.`
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
