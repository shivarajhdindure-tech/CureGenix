"use client";

import { useState, useEffect } from "react";
import { API_URL, fmt, isNum } from "@/lib/analysis";
import { extractCalculationTargets } from "../lib/activeStructureState.mjs";
import { QUANTUM_RESOURCE_DEFAULTS } from "../lib/quantumLabTransparency.mjs";

function TargetBadge({ variant = "default", children }) {
  const styles = {
    verified: "bg-emerald-50 text-emerald-800 border-emerald-200",
    amber: "bg-amber-50 text-amber-800 border-amber-200",
    rose: "bg-rose-50 text-rose-800 border-rose-200",
    cyan: "bg-cyan-50 text-cyan-800 border-cyan-200",
    slate: "bg-slate-100 text-slate-700 border-slate-200",
    teal: "bg-teal-50 text-teal-800 border-teal-200",
  };
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium border font-mono ${styles[variant] || styles.slate}`}>
      {children}
    </span>
  );
}

export default function MolecularTargetSelector({
  activeStructure,
  derived,
  onTargetSelect,
}) {
  const [filterType, setFilterType] = useState("all"); // all | co_crystallized_ligand | benchmark | candidate
  const [selectedTargetId, setSelectedTargetId] = useState(null);
  const [jobState, setJobState] = useState(null); // { job_id, status, result, elapsed_seconds }
  const [submitError, setSubmitError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Extract unified calculation targets from active structure, candidates, benchmarks
  const targets = extractCalculationTargets(activeStructure, derived);

  // Auto-select first matching target if none selected or if active structure changed
  useEffect(() => {
    if (targets.length > 0) {
      // Prefer first co-crystallized drug candidate matching selected chain, else first target
      const defaultTarget = targets.find((t) => t.type === "co_crystallized_ligand" && t.isChainMatched) || targets[0];
      setSelectedTargetId(defaultTarget.targetId);
      setJobState(null);
      setSubmitError("");
      if (onTargetSelect) onTargetSelect(defaultTarget);
    }
  }, [activeStructure?.pdbId, activeStructure?.selectedChainId]);

  const selectedTarget = targets.find((t) => t.targetId === selectedTargetId) || targets[0] || null;

  function handleSelect(target) {
    setSelectedTargetId(target.targetId);
    setJobState(null);
    setSubmitError("");
    if (onTargetSelect) onTargetSelect(target);
  }

  const isEligible = selectedTarget?.resourceEligibility?.status === "eligible";
  const isSkippedLimit = selectedTarget?.resourceEligibility?.status === "skipped_resource_limit";
  const isUnverified = selectedTarget?.verificationStatus === "unverified_raw_pdb_coordinates" || !selectedTarget?.smiles;
  const skipReasons = selectedTarget?.resourceEligibility?.reasons || [];

  const isJobActive = jobState?.status === "queued" || jobState?.status === "running";

  async function handleRunCalculation() {
    if (!selectedTarget || isJobActive || !selectedTarget.smiles) return;
    setIsSubmitting(true);
    setSubmitError("");
    setJobState({ status: "queued", candidate_id: selectedTarget.targetId });

    try {
      const response = await fetch(`${API_URL}/api/quantum-calculations`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          candidate_id: selectedTarget.targetId.replace(/[^A-Za-z0-9_.-]/g, "_"),
          smiles: selectedTarget.smiles,
          basis: "sto3g",
          maxiter: 50,
          charge: 0,
          spin: 0,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail?.message || errorData.detail || `Server returned status ${response.status}`);
      }

      const accepted = await response.json();
      setJobState({ job_id: accepted.job_id, status: accepted.status, candidate_id: selectedTarget.targetId });

      // Poll until terminal status
      const pollJob = async () => {
        let attempts = 0;
        const maxAttempts = 60;
        while (attempts < maxAttempts) {
          await new Promise((r) => setTimeout(r, 1200));
          attempts++;
          const checkRes = await fetch(`${API_URL}/api/quantum-calculations/${encodeURIComponent(accepted.job_id)}`, {
            cache: "no-store",
          });
          if (checkRes.ok) {
            const data = await checkRes.json();
            setJobState(data);
            if (["completed", "skipped", "failed"].includes(data.status)) {
              break;
            }
          }
        }
      };

      pollJob();
    } catch (err) {
      setSubmitError(err.message || "Calculation submission failed.");
      setJobState(null);
    } finally {
      setIsSubmitting(false);
    }
  }

  // Filter targets for UI list
  const filteredTargets = targets.filter((t) => {
    if (filterType === "all") return true;
    if (filterType === "co_crystallized_ligand") return t.type === "co_crystallized_ligand";
    if (filterType === "benchmark") return t.type === "benchmark";
    if (filterType === "candidate") return t.type === "novel_candidate" || t.type === "reference_compound";
    return true;
  });

  return (
    <div className="rounded-xl border border-slate-200/90 bg-white p-5 shadow-sm space-y-6">
      {/* Header and Provenance Banner */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 border-b border-slate-100 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-base font-bold text-slate-900">
              Calculation Target &amp; Molecular Input Selector
            </h3>
            <span className="rounded bg-teal-50 border border-teal-200 text-teal-800 text-[11px] font-bold px-2 py-0.5 font-mono">
              Phase 3 Unified Workflow
            </span>
          </div>
          <p className="mt-1 text-xs text-slate-500">
            Select a target molecule derived from the active PDB structure context ({activeStructure?.pdbId || "None"}), curated benchmarks, or discovery candidates.
          </p>
        </div>

        {/* Filter Pills */}
        <div className="flex flex-wrap items-center gap-1 rounded-lg border border-slate-200 bg-slate-100 p-1 text-xs">
          <button
            type="button"
            onClick={() => setFilterType("all")}
            className={`rounded px-2.5 py-1 font-semibold transition ${
              filterType === "all" ? "bg-white text-slate-900 shadow-xs" : "text-slate-600 hover:text-slate-900"
            }`}
          >
            All ({targets.length})
          </button>
          <button
            type="button"
            onClick={() => setFilterType("co_crystallized_ligand")}
            className={`rounded px-2.5 py-1 font-semibold transition ${
              filterType === "co_crystallized_ligand" ? "bg-white text-slate-900 shadow-xs" : "text-slate-600 hover:text-slate-900"
            }`}
          >
            Co-Crystallized Ligands ({targets.filter((t) => t.type === "co_crystallized_ligand").length})
          </button>
          <button
            type="button"
            onClick={() => setFilterType("benchmark")}
            className={`rounded px-2.5 py-1 font-semibold transition ${
              filterType === "benchmark" ? "bg-white text-slate-900 shadow-xs" : "text-slate-600 hover:text-slate-900"
            }`}
          >
            Benchmarks (2)
          </button>
          {targets.filter((t) => t.type === "novel_candidate" || t.type === "reference_compound").length > 0 && (
            <button
              type="button"
              onClick={() => setFilterType("candidate")}
              className={`rounded px-2.5 py-1 font-semibold transition ${
                filterType === "candidate" ? "bg-white text-slate-900 shadow-xs" : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Candidates ({targets.filter((t) => t.type === "novel_candidate" || t.type === "reference_compound").length})
            </button>
          )}
        </div>
      </div>

      {/* Target Grid / List */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {filteredTargets.map((target) => {
          const isSelected = target.targetId === selectedTargetId;
          const targetEligible = target.resourceEligibility?.status === "eligible";
          const targetSkipped = target.resourceEligibility?.status === "skipped_resource_limit";

          return (
            <button
              key={target.targetId}
              type="button"
              onClick={() => handleSelect(target)}
              className={`text-left rounded-xl border p-3.5 transition flex flex-col justify-between ${
                isSelected
                  ? "border-teal-500 bg-teal-50/40 ring-2 ring-teal-500/20 shadow-xs"
                  : "border-slate-200 hover:border-slate-300 bg-white"
              }`}
            >
              <div>
                <div className="flex items-center justify-between gap-1.5 mb-1.5">
                  <span className="font-mono text-xs font-bold text-slate-900 truncate">
                    {target.targetId}
                  </span>
                  {target.type === "co_crystallized_ligand" && (
                    <span className="rounded bg-sky-50 text-sky-800 border border-sky-200 text-[10px] px-1.5 py-0.2 font-mono">
                      {target.sourcePdbId}:{target.chainId}
                    </span>
                  )}
                  {target.type === "benchmark" && (
                    <span className="rounded bg-violet-50 text-violet-800 border border-violet-200 text-[10px] px-1.5 py-0.2 font-mono">
                      Benchmark
                    </span>
                  )}
                </div>

                <p className="text-xs font-semibold text-slate-800 line-clamp-1 mb-1">
                  {target.name}
                </p>

                <p className="text-[11px] font-mono text-slate-500 truncate mb-2">
                  {target.formula || (target.smiles ? target.smiles.substring(0, 22) + "…" : "No formula")}
                </p>
              </div>

              <div className="flex flex-wrap items-center gap-1 pt-2 border-t border-slate-100">
                {target.heavyAtoms !== null && (
                  <TargetBadge variant="slate">{target.heavyAtoms} heavy</TargetBadge>
                )}
                {targetEligible && (
                  <TargetBadge variant="verified">Eligible</TargetBadge>
                )}
                {targetSkipped && (
                  <TargetBadge variant="amber">&gt;20 Limit</TargetBadge>
                )}
                {target.verificationStatus === "verified_ccd" && (
                  <TargetBadge variant="teal">CCD</TargetBadge>
                )}
              </div>
            </button>
          );
        })}
      </div>

      {/* Selected Target Detail & Honest Resource Preflight */}
      {selectedTarget && (
        <div className="rounded-xl border border-slate-200 bg-slate-50/50 p-5 space-y-5">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 border-b border-slate-200 pb-4">
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h4 className="text-base font-bold text-slate-900">
                  {selectedTarget.name}
                </h4>
                <TargetBadge variant={selectedTarget.verificationStatus.startsWith("verified") ? "verified" : "amber"}>
                  {selectedTarget.verificationStatus}
                </TargetBadge>
                <span className="text-xs font-mono text-slate-500">ID: {selectedTarget.targetId}</span>
              </div>
              {selectedTarget.chemicalName && (
                <p className="mt-1 text-xs text-slate-600 italic">
                  {selectedTarget.chemicalName}
                </p>
              )}
            </div>

            {/* Action Button */}
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={handleRunCalculation}
                disabled={isJobActive || isUnverified || isSubmitting}
                className={`rounded-lg px-4 py-2 text-xs font-semibold shadow-xs transition flex items-center gap-2 ${
                  isJobActive
                    ? "bg-slate-200 text-slate-500 cursor-not-allowed"
                    : isUnverified
                    ? "bg-slate-200 text-slate-400 cursor-not-allowed"
                    : isEligible
                    ? "bg-teal-600 hover:bg-teal-700 text-white"
                    : "bg-amber-600 hover:bg-amber-700 text-white"
                }`}
              >
                {isJobActive ? (
                  <>
                    <svg className="animate-spin h-3.5 w-3.5 text-slate-500" viewBox="0 0 24 24" fill="none">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                    </svg>
                    <span>Simulation In Progress…</span>
                  </>
                ) : isEligible ? (
                  <>
                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span>Run VQE Calculation</span>
                  </>
                ) : (
                  <>
                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                    </svg>
                    <span>Execute Policy Verification Run</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {submitError && (
            <div role="alert" className="rounded-lg border border-rose-300 bg-rose-50 p-3 text-xs text-rose-800">
              <span className="font-semibold">Submission Notice:</span> {submitError}
            </div>
          )}

          {/* Molecule Metrics & Resource Preflight Card */}
          <div className="grid gap-4 md:grid-cols-2">
            {/* Left: Molecular Details & Provenance */}
            <div className="rounded-lg border border-slate-200 bg-white p-4 space-y-3">
              <h5 className="text-xs font-bold uppercase tracking-wider text-slate-500">
                Molecular Specification &amp; Provenance
              </h5>

              <div className="grid grid-cols-2 gap-3 text-xs">
                <div>
                  <span className="text-slate-400 block text-[11px]">Source Context</span>
                  <span className="font-semibold text-slate-800">
                    {selectedTarget.type === "benchmark" ? "Standard Benchmark" : `PDB ${selectedTarget.sourcePdbId} (Chain ${selectedTarget.chainId || "A"})`}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[11px]">Formula</span>
                  <span className="font-mono font-semibold text-slate-800">{selectedTarget.formula || "—"}</span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[11px]">Heavy Atoms</span>
                  <span className="font-mono font-bold text-slate-900">{selectedTarget.heavyAtoms ?? "—"}</span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[11px]">Molecular Weight</span>
                  <span className="font-mono text-slate-800">{isNum(selectedTarget.molecularWeight) ? `${fmt(selectedTarget.molecularWeight, 2)} g/mol` : "—"}</span>
                </div>
              </div>

              <div>
                <span className="text-slate-400 block text-[11px] mb-1">Canonical / Verified SMILES</span>
                {selectedTarget.smiles ? (
                  <div className="rounded bg-slate-50 border border-slate-200 p-2 font-mono text-[11px] text-slate-800 break-all select-all">
                    {selectedTarget.smiles}
                  </div>
                ) : (
                  <div className="rounded bg-amber-50 border border-amber-200 p-2 text-xs text-amber-900">
                    SMILES withheld: PDB coordinates alone do not establish chemical bond orders or aromaticity without CCD verification.
                  </div>
                )}
              </div>

              {selectedTarget.ccdSource && (
                <div className="text-[11px] text-slate-500">
                  <span className="font-medium text-slate-700">CCD Reference:</span> {selectedTarget.ccdSource}
                </div>
              )}
            </div>

            {/* Right: Honest Resource Policy Preflight */}
            <div className={`rounded-lg border p-4 space-y-3 ${
              isEligible
                ? "border-emerald-200 bg-emerald-50/40"
                : isSkippedLimit
                ? "border-amber-200 bg-amber-50/50"
                : "border-slate-200 bg-white"
            }`}>
              <div className="flex items-center justify-between">
                <h5 className="text-xs font-bold uppercase tracking-wider text-slate-600">
                  Resource Policy Preflight Audit
                </h5>
                <TargetBadge variant={isEligible ? "verified" : isSkippedLimit ? "amber" : "slate"}>
                  {selectedTarget.resourceEligibility?.status || "preflight_ready"}
                </TargetBadge>
              </div>

              {isEligible && (
                <div className="space-y-2 text-xs text-emerald-950">
                  <p className="font-semibold text-emerald-900 flex items-center gap-1.5">
                    <svg className="w-4 h-4 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                    </svg>
                    Eligible for Variational Quantum Eigensolver
                  </p>
                  <p className="text-emerald-800 leading-relaxed">
                    Heavy-atom count ({selectedTarget.heavyAtoms}) and estimated STO-3G basis functions ({selectedTarget.basisFunctionsEstimate || "≤14"}) comply with the cluster policy (&le; {QUANTUM_RESOURCE_DEFAULTS.maxHeavyAtoms} heavy atoms, &le; {QUANTUM_RESOURCE_DEFAULTS.maxEstimatedBasisFunctions} AO).
                  </p>
                </div>
              )}

              {isSkippedLimit && (
                <div className="space-y-2 text-xs text-amber-950">
                  <p className="font-semibold text-amber-900 flex items-center gap-1.5">
                    <svg className="w-4 h-4 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                    Exceeds Operational Resource Policy Limits
                  </p>
                  <ul className="list-disc pl-4 space-y-1 text-amber-900">
                    {skipReasons.map((reason, idx) => (
                      <li key={idx} className="leading-relaxed font-medium">{reason}</li>
                    ))}
                  </ul>
                  <p className="text-[11px] text-amber-800 leading-relaxed pt-1 border-t border-amber-200">
                    <strong className="font-semibold">Scientific Safeguard:</strong> This ligand exceeds cluster limits. Under CureGenix policy, oversized molecules are not forced into undersized simulators. The backend halts prior to PySCF allocation and returns an explicit policy skip record; simulated values are never fabricated.
                  </p>
                </div>
              )}

              {isUnverified && (
                <div className="text-xs text-slate-700 space-y-1">
                  <p className="font-semibold text-slate-900">Chemical Verification Required</p>
                  <p className="text-slate-600 leading-relaxed">
                    This HETATM component lacks a validated Chemical Component Dictionary entry. Quantum chemistry calculations cannot proceed without verified chemical connectivity.
                  </p>
                </div>
              )}

              <div className="pt-2 border-t border-slate-200/60 text-[11px] text-slate-500 flex justify-between">
                <span>Cluster Limit: &le;{QUANTUM_RESOURCE_DEFAULTS.maxHeavyAtoms} heavy atoms</span>
                <span>Basis: STO-3G (&le;{QUANTUM_RESOURCE_DEFAULTS.maxEstimatedBasisFunctions} AO)</span>
              </div>
            </div>
          </div>

          {/* Job Execution & Lifecycle Progress Monitor */}
          {jobState && (
            <div className={`rounded-lg border p-4 space-y-3 transition ${
              jobState.status === "completed"
                ? "border-emerald-300 bg-emerald-50/50"
                : jobState.status === "skipped"
                ? "border-amber-300 bg-amber-50/50"
                : jobState.status === "failed"
                ? "border-rose-300 bg-rose-50/50"
                : "border-sky-300 bg-sky-50/40"
            }`}>
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-slate-200/60 pb-3">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-700">
                    Job Lifecycle Monitor:
                  </span>
                  <TargetBadge variant={
                    jobState.status === "completed" ? "verified" :
                    jobState.status === "skipped" ? "amber" :
                    jobState.status === "failed" ? "rose" : "cyan"
                  }>
                    {jobState.status.toUpperCase()}
                  </TargetBadge>
                  {jobState.job_id && (
                    <span className="font-mono text-[11px] text-slate-500">
                      Record: {jobState.job_id}
                    </span>
                  )}
                </div>

                {isNum(jobState.elapsed_seconds) && (
                  <span className="text-xs font-mono font-medium text-slate-600">
                    Elapsed: {jobState.elapsed_seconds}s
                  </span>
                )}
              </div>

              {/* Status details */}
              {jobState.status === "queued" && (
                <p className="text-xs text-sky-900 leading-relaxed">
                  Calculation queued in background execution pool. Preparing molecular geometry and assessing operational resource limits…
                </p>
              )}

              {jobState.status === "running" && (
                <div className="flex items-center gap-2 text-xs text-sky-900">
                  <svg className="animate-spin h-4 w-4 text-sky-700" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                  </svg>
                  <span>Active-space VQE simulation in progress on simulation worker…</span>
                </div>
              )}

              {jobState.status === "skipped" && (
                <div className="space-y-1.5 text-xs text-amber-950">
                  <p className="font-bold text-amber-900">
                    Calculation Safely Skipped by Resource Policy Preflight
                  </p>
                  <p className="leading-relaxed text-amber-900">
                    {jobState.result?.message || "Molecule size exceeded cluster limits."}
                  </p>
                  <p className="text-[11px] text-amber-800">
                    Provenance record persisted in <code className="font-mono text-amber-950">experiments/molecular_calculations/{jobState.job_id}.json</code>.
                  </p>
                </div>
              )}

              {jobState.status === "completed" && jobState.result && (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <div className="rounded bg-white p-3 border border-emerald-200">
                      <span className="text-[10px] font-bold uppercase text-slate-400 block">Total Energy</span>
                      <span className="font-mono font-bold text-sm text-emerald-950">
                        {fmt(jobState.result.vqe?.total_molecular_energy_hartree || jobState.result.total_energy_hartree, 4)} Ha
                      </span>
                    </div>
                    <div className="rounded bg-white p-3 border border-emerald-200">
                      <span className="text-[10px] font-bold uppercase text-slate-400 block">Electronic Energy</span>
                      <span className="font-mono font-bold text-sm text-emerald-950">
                        {fmt(jobState.result.vqe?.electronic_energy_hartree || jobState.result.electronic_energy_hartree, 4)} Ha
                      </span>
                    </div>
                    <div className="rounded bg-white p-3 border border-emerald-200">
                      <span className="text-[10px] font-bold uppercase text-slate-400 block">HOMO-LUMO Gap</span>
                      <span className="font-mono font-bold text-sm text-emerald-950">
                        {fmt(jobState.result.homo_lumo_gap_hartree, 4)} Ha
                      </span>
                    </div>
                    <div className="rounded bg-white p-3 border border-emerald-200">
                      <span className="text-[10px] font-bold uppercase text-slate-400 block">Optimizer</span>
                      <span className="font-semibold text-xs text-emerald-900 block truncate">
                        {jobState.result.vqe?.optimizer_success ? "Converged" : "Completed"}
                      </span>
                    </div>
                  </div>

                  <p className="text-[11px] text-emerald-800">
                    Calculation verified on classical statevector backend. Result persisted in <code className="font-mono text-emerald-950">experiments/molecular_calculations/{jobState.job_id}.json</code>.
                  </p>
                </div>
              )}

              {jobState.status === "failed" && (
                <div className="space-y-1 text-xs text-rose-950">
                  <p className="font-bold text-rose-900">Quantum Job Execution Notice</p>
                  <p className="text-rose-800">{jobState.result?.message || "Chemistry calculation could not be completed."}</p>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
