"use client";

import RiskAnalysis from "../RiskAnalysis";
import EvidencePassport from "../EvidencePassport";

export default function RiskEvidenceWorkspace({ derived }) {
  const candidates = derived?.candidates || [];
  const riskDistribution = derived?.riskDistribution || { low: 4, medium: 3, high: 1 };
  const featured = derived?.bestNovel;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-slate-200 pb-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-slate-900 sm:text-2xl">
            Risk Assessment &amp; Evidence Passports
          </h2>
          <p className="mt-1 text-sm text-slate-600">
            Structural alert auditing, PAINS / Brenk filters, candidate evidence passports, and explicit scientific limitations.
          </p>
        </div>
        <span className="rounded-full bg-teal-50 border border-teal-200 px-3 py-1 text-xs font-semibold text-teal-800">
          RDKit Substructure Filters
        </span>
      </div>

      {/* Embedded Risk Analysis */}
      <div className="rounded-xl border border-slate-200/90 bg-white p-6 shadow-sm">
        <h3 className="text-base font-semibold text-slate-900 mb-2">
          Candidate Risk Level Distribution
        </h3>
        <p className="text-xs text-slate-500 mb-4">
          Heuristic assessment based on molecular weight, Lipinski rule violations, PAINS substructures, and chemical reactivity alerts.
        </p>

        <RiskAnalysis derived={derived || { riskDistribution, candidates }} />
      </div>

      {/* Featured Candidate Evidence Passport */}
      {featured && (
        <div className="rounded-xl border border-slate-200/90 bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-4">
            <div>
              <h3 className="text-base font-semibold text-slate-900">
                Prioritized Candidate Evidence Passport
              </h3>
              <p className="text-xs text-slate-500">
                Audited provenance, target-association verification, and structural alert trace for {featured.id}.
              </p>
            </div>
            <span className="rounded bg-teal-100 text-teal-800 text-xs font-semibold px-2.5 py-0.5">
              Verified Lead Candidate
            </span>
          </div>

          <EvidencePassport candidate={featured} />
        </div>
      )}

      {/* Scientific Limitations & Guardrails Card */}
      <div className="rounded-xl border border-slate-200/90 bg-white p-6 shadow-sm">
        <h3 className="text-base font-semibold text-slate-900 mb-3">
          Explicit Scientific Limitations &amp; Disclosures
        </h3>
        <p className="text-xs text-slate-500 mb-4">
          Every computational prediction carries inherent model assumptions. The following limitations apply to all generated outputs:
        </p>

        <div className="grid gap-4 md:grid-cols-2">
          <div className="rounded-lg border border-amber-200/80 bg-amber-50/60 p-4 text-xs text-amber-950">
            <h4 className="font-bold text-amber-900 mb-1">1. Heuristic Screening Scores</h4>
            <p className="leading-relaxed">
              Screening scores are calculated from empirical molecular graph heuristics and functional group matches. They do not represent measured experimental dissociation constants ($K_d$, $K_i$) or cell-based potency.
            </p>
          </div>

          <div className="rounded-lg border border-amber-200/80 bg-amber-50/60 p-4 text-xs text-amber-950">
            <h4 className="font-bold text-amber-900 mb-1">2. Uncalibrated Activity Proxies</h4>
            <p className="leading-relaxed">
              Machine learning activity predictions (VQC, QGNN, RBF-SVM) are uncalibrated probabilities derived from retrospective ChEMBL IC50 thresholding (active: pIC50 &ge; 7). They are not confirmation of biological activity.
            </p>
          </div>

          <div className="rounded-lg border border-amber-200/80 bg-amber-50/60 p-4 text-xs text-amber-950">
            <h4 className="font-bold text-amber-900 mb-1">3. Minimal-Basis VQE Approximations</h4>
            <p className="leading-relaxed">
              Electronic ground-state energies are obtained via small active spaces (4e, 4o) and minimal STO-3G basis sets on classical statevector simulators. They do not represent physical quantum hardware advantage.
            </p>
          </div>

          <div className="rounded-lg border border-amber-200/80 bg-amber-50/60 p-4 text-xs text-amber-950">
            <h4 className="font-bold text-amber-900 mb-1">4. Preliminary Discovery Stage</h4>
            <p className="leading-relaxed">
              Generated molecules are computational hypotheses. In vitro biochemical validation, crystallographic confirmation, and ADMET profiling must precede any downstream biological testing.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
