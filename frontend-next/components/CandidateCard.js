"use client";

import { useState } from "react";
import { fmt, isNum } from "@/lib/analysis";
import EvidencePassport from "./EvidencePassport";

export const RISK_STYLES = {
  low: "border-emerald-400/30 bg-emerald-400/10 text-emerald-300",
  medium: "border-amber-400/30 bg-amber-400/10 text-amber-300",
  high: "border-red-400/30 bg-red-400/10 text-red-300",
};

function isVerifiedCandidate(c) {
  return (
    c.verificationStatus === "verified" && c.targetAssociationVerified === true
  );
}

function Badges({ c }) {
  const verified = isVerifiedCandidate(c);

  return (
    <div className="flex flex-wrap gap-1.5">
      {c.isNovel ? (
        <span className="badge border-violet-400/30 bg-violet-400/10 text-violet-300">
          Novel
        </span>
      ) : (
        <span className="badge border-slate-400/30 bg-slate-400/10 text-slate-300">
          Reference{c.category ? ` · ${c.category}` : ""}
        </span>
      )}

      {verified ? (
        <span className="badge border-emerald-400/30 bg-emerald-400/10 text-emerald-300">
          Evidence verified
        </span>
      ) : (
        <span className="badge border-amber-400/30 bg-amber-400/10 text-amber-300">
          Unverified reference
        </span>
      )}

      {c.quantumState === "vqe" && (
        <span className="badge border-cyan-400/30 bg-cyan-400/10 text-cyan-300">
          Quantum analyzed
        </span>
      )}

      {c.quantumState === "lightweight" && (
        <span className="badge border-amber-400/30 bg-amber-400/10 text-amber-300">
          Descriptor mode
        </span>
      )}

      {c.quantumState === "skipped" && (
        <span className="badge border-white/10 bg-white/[0.04] text-slate-400">
          Quantum skipped
        </span>
      )}

      {c.quantumState === "resource_skipped" && (
        <span className="badge border-amber-400/30 bg-amber-400/10 text-amber-200">
          Skipped · resource limit
        </span>
      )}

      {c.quantumState === "failed" && (
        <span className="badge border-red-400/30 bg-red-400/10 text-red-300">
          Quantum failed
        </span>
      )}

      {c.scoreTie && (
        <span className="badge border-sky-400/30 bg-sky-400/10 text-sky-200">
          Equal adjusted score · tie
        </span>
      )}

      {c.isBestNovelTie && (
        <span className="badge border-violet-400/30 bg-violet-400/10 text-violet-200">
          Top novel score · tied
        </span>
      )}

      {c.isBestNovel && (
        <span className="badge border-emerald-400/40 bg-emerald-400/15 text-emerald-300">
          Prioritized
        </span>
      )}
    </div>
  );
}

function MiniBar({ label, value }) {
  const pct = isNum(value) ? Math.max(0, Math.min(1, value)) * 100 : 0;

  return (
    <div>
      <div className="flex justify-between text-[11px] text-slate-400">
        <span>{label}</span>
        <span className="font-data text-slate-300">{fmt(value, 2)}</span>
      </div>

      <div className="mt-1 h-1 overflow-hidden rounded-full bg-white/[0.06]">
        <div
          className="h-full origin-left animate-barGrow rounded-full bg-gradient-to-r from-cyan-400/70 to-violet-400/70"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false);

  if (!text) return null;

  return (
    <button
      type="button"
      onClick={async () => {
        try {
          await navigator.clipboard.writeText(text);
          setCopied(true);
          setTimeout(() => setCopied(false), 1500);
        } catch {
          // Clipboard unavailable.
        }
      }}
      className="shrink-0 rounded-md border border-white/10 px-2 py-1 text-[10px] text-slate-400 transition hover:bg-white/[0.06] hover:text-slate-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300">
      {copied ? "Copied" : "Copy"}
    </button>
  );
}

function Field({ label, children }) {
  return (
    <div>
      <p className="metric-label">{label}</p>
      <div className="mt-1 text-sm text-slate-100">{children}</div>
    </div>
  );
}

export default function CandidateCard({ candidate: c, featured = false, onSelectForRisk = null }) {
  const [open, setOpen] = useState(false);

  const q = c.quantumState === "vqe" ? c.quantum : null;
  const scr = c.screening;
  const verified = isVerifiedCandidate(c);

  return (
    <article
      className={`relative rounded-2xl border p-5 md:p-6 ${
        featured
          ? "border-emerald-400/30 bg-ink-800/90 shadow-[0_0_0_1px_rgba(52,211,153,0.15),0_20px_60px_-30px_rgba(52,211,153,0.35)]"
          : "border-white/[0.08] bg-ink-800/70"
      }`}>
      {featured && (
        <p className="mb-3 text-[11px] font-semibold uppercase tracking-[0.2em] text-emerald-300">
          Best novel candidate
        </p>
      )}

      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="flex items-center gap-3">
            {isNum(c.rank) && (
              <span
                className="font-data text-lg font-semibold text-slate-500"
                title={c.scoreTie ? "Equal adjusted score; order does not imply superiority." : undefined}>
                {c.scoreTie ? "Tie" : `#${c.rank}`}
              </span>
            )}

            <h3
              className="font-data truncate text-lg font-semibold text-white"
              title={c.id}>
              {c.id}
            </h3>
          </div>

          <div className="mt-2.5">
            <Badges c={c} />
          </div>
        </div>

        {isNum(c.adjustedScore) && (
          <div className="text-right">
            <p className="metric-label">Adjusted score</p>
            <p className="font-data mt-1 text-2xl font-semibold text-white">
              {fmt(c.adjustedScore, 3)}
            </p>
            {c.scoreTie && (
              <p className="mt-1 text-[10px] text-sky-200/80">Equal displayed score; no score-based distinction.</p>
            )}
          </div>
        )}
      </div>

      {!verified && (
        <div className="mt-4 rounded-lg border border-amber-400/20 bg-amber-400/[0.06] p-3">
          <p className="text-sm font-medium text-amber-200">
            Unverified reference compound
          </p>
          <p className="mt-1 text-xs leading-5 text-slate-400">
            Approval status and association with the analyzed target have not
            both been verified. Scores and confidence are computational
            prioritization estimates, not evidence of clinical effectiveness.
          </p>
        </div>
      )}

      {c.smiles && (
        <div className="mt-4 flex items-start gap-2 rounded-lg border border-white/[0.06] bg-ink-950/60 p-3">
          <p className="font-data min-w-0 flex-1 break-all text-xs leading-5 text-slate-300">
            {c.smiles}
          </p>
          <CopyButton text={c.smiles} />
        </div>
      )}

      <div
        className={`mt-5 grid gap-4 ${
          featured ? "sm:grid-cols-4" : "grid-cols-2"
        }`}>
        <Field label="Type">
          <span className="capitalize">{c.category || "—"}</span>
        </Field>

        <Field label="Risk">
          {c.riskLevel ? (
            <span
              className={`badge ${
                RISK_STYLES[c.riskLevel] || RISK_STYLES.medium
              }`}>
              {c.riskLevel}
            </span>
          ) : (
            "—"
          )}
        </Field>

        <Field label="Confidence">
          <span className="capitalize">{c.confidence || "—"}</span>
        </Field>

        <Field label="Composite score">
          <span className="font-data">{fmt(c.compositeScore, 3)}</span>
        </Field>
      </div>
      <div className="mt-4 rounded-lg border border-amber-400/25 bg-amber-400/[0.06] p-3">
        <p className="text-sm font-medium text-amber-200">
          Safety evidence insufficient
        </p>
        <p className="mt-1 text-xs leading-5 text-slate-400">
          The displayed risk category is based on a rule-based structural
          heuristic, not a validated toxicity model. Absence of detected
          structural alerts does not establish safety.
        </p>
        {c.structuralAlertCount !== null && (
          <p className="mt-2 text-xs text-slate-400">
            Structural alerts detected: {c.structuralAlertCount}
          </p>
        )}
      </div>
      {q && (
        <div className="mt-5 grid grid-cols-2 gap-3 rounded-xl border border-cyan-400/15 bg-cyan-400/[0.04] p-3">
          <div>
            <p className="metric-label">HOMO-LUMO gap</p>
            <p className="font-data mt-1 text-sm font-semibold text-cyan-200">
              {fmt(q.homo_lumo_gap_hartree)} Ha
            </p>
          </div>

          <div>
            <p className="metric-label">VQE electronic energy</p>
            <p className="font-data mt-1 text-sm font-semibold text-cyan-200">
              {fmt(q.vqe?.electronic_energy_hartree)} Ha
            </p>
          </div>
          <div>
            <p className="metric-label">Total molecular energy</p>
            <p className="font-data mt-1 text-sm font-semibold text-cyan-200">
              {fmt(q.vqe?.total_molecular_energy_hartree)} Ha
            </p>
          </div>
        </div>
      )}

      {scr && (
        <div className="mt-5">
          <p className="metric-label mb-2.5">Screening metrics</p>
          <div className="grid gap-3 sm:grid-cols-2">
            <MiniBar label="Drug-likeness" value={scr.drug_likeness} />
            <MiniBar label="BBB permeability" value={scr.bbb_permeability} />
            <MiniBar label="Potency proxy" value={scr.potency_proxy} />
            <MiniBar label="Toxicity penalty" value={scr.toxicity_penalty} />
          </div>
        </div>
      )}

      {c.reasoning && (
        <div className="mt-5 border-t border-white/[0.06] pt-3">
          <button
            type="button"
            onClick={() => setOpen((v) => !v)}
            aria-expanded={open}
            className="flex w-full items-center justify-between rounded text-left text-xs font-medium text-slate-400 transition hover:text-slate-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300">
            Generated rationale
            <span
              aria-hidden="true"
              className={`transition ${open ? "rotate-180" : ""}`}>
              ▾
            </span>
          </button>

          {open && (
            <p className="mt-2 text-xs leading-5 text-slate-400">
              {c.reasoning}
              <span className="mt-2 block text-[11px] italic text-slate-600">
                Text generated by the pipeline&apos;s language model.
                Computational output only, not experimentally validated.
              </span>
            </p>
          )}
        </div>
      )}
      <EvidencePassport candidate={c} />
      {onSelectForRisk && (
        <button
          type="button"
          onClick={() => onSelectForRisk(c.id)}
          className="mt-4 w-full rounded-lg border border-teal-500/40 bg-teal-500/10 hover:bg-teal-500/20 px-3 py-2 text-xs font-semibold text-teal-300 transition flex items-center justify-center gap-1.5 shadow-sm"
        >
          <svg className="w-4 h-4 text-teal-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
          Evaluate Molecular Risk &amp; Digital Twin
        </button>
      )}
    </article>
  );
}
