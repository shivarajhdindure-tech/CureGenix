"use client";

import { useState } from "react";
import { fmt, isNum } from "@/lib/analysis";

export const RISK_STYLES = {
  low: "border-emerald-400/30 bg-emerald-400/10 text-emerald-300",
  medium: "border-amber-400/30 bg-amber-400/10 text-amber-300",
  high: "border-red-400/30 bg-red-400/10 text-red-300",
};

function Badges({ c }) {
  return (
    <div className="flex flex-wrap gap-1.5">
      {c.isNovel ? (
        <span className="badge border-violet-400/30 bg-violet-400/10 text-violet-300">Novel</span>
      ) : (
        <span className="badge border-slate-400/30 bg-slate-400/10 text-slate-300">
          Reference{c.category ? ` · ${c.category}` : ""}
        </span>
      )}
      {c.quantumState === "vqe" && (
        <span className="badge border-cyan-400/30 bg-cyan-400/10 text-cyan-300">Quantum analyzed</span>
      )}
      {c.quantumState === "lightweight" && (
        <span className="badge border-amber-400/30 bg-amber-400/10 text-amber-300">Descriptor mode</span>
      )}
      {c.quantumState === "skipped" && (
        <span className="badge border-white/10 bg-white/[0.04] text-slate-400">Quantum skipped</span>
      )}
      {c.quantumState === "failed" && (
        <span className="badge border-red-400/30 bg-red-400/10 text-red-300">Quantum failed</span>
      )}
      {c.isBestNovel && (
        <span className="badge border-emerald-400/40 bg-emerald-400/15 text-emerald-300">Prioritized</span>
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
          /* clipboard unavailable: ignore */
        }
      }}
      className="shrink-0 rounded-md border border-white/10 px-2 py-1 text-[10px] text-slate-400 transition hover:bg-white/[0.06] hover:text-slate-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300"
    >
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

export default function CandidateCard({ candidate: c, featured = false }) {
  const [open, setOpen] = useState(false);
  const q = c.quantumState === "vqe" ? c.quantum : null;
  const scr = c.screening;

  return (
    <article
      className={`relative rounded-2xl border p-5 md:p-6 ${
        featured
          ? "border-emerald-400/30 bg-ink-800/90 shadow-[0_0_0_1px_rgba(52,211,153,0.15),0_20px_60px_-30px_rgba(52,211,153,0.35)]"
          : "border-white/[0.08] bg-ink-800/70"
      }`}
    >
      {featured && (
        <p className="mb-3 text-[11px] font-semibold uppercase tracking-[0.2em] text-emerald-300">
          Best novel candidate
        </p>
      )}

      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="flex items-center gap-3">
            {isNum(c.rank) && (
              <span className="font-data text-lg font-semibold text-slate-500">#{c.rank}</span>
            )}
            <h3 className="font-data truncate text-lg font-semibold text-white" title={c.id}>
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
            <p className="font-data mt-1 text-2xl font-semibold text-white">{fmt(c.adjustedScore, 3)}</p>
          </div>
        )}
      </div>

      {c.smiles && (
        <div className="mt-4 flex items-start gap-2 rounded-lg border border-white/[0.06] bg-ink-950/60 p-3">
          <p className="font-data min-w-0 flex-1 break-all text-xs leading-5 text-slate-300">{c.smiles}</p>
          <CopyButton text={c.smiles} />
        </div>
      )}

      <div className={`mt-5 grid gap-4 ${featured ? "sm:grid-cols-4" : "grid-cols-2"}`}>
        <Field label="Type">
          <span className="capitalize">{c.category || "—"}</span>
        </Field>
        <Field label="Risk">
          {c.riskLevel ? (
            <span className={`badge ${RISK_STYLES[c.riskLevel] || RISK_STYLES.medium}`}>{c.riskLevel}</span>
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
            className="flex w-full items-center justify-between text-left text-xs font-medium text-slate-400 transition hover:text-slate-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300 rounded"
          >
            Generated rationale
            <span aria-hidden="true" className={`transition ${open ? "rotate-180" : ""}`}>▾</span>
          </button>
          {open && (
            <p className="mt-2 text-xs leading-5 text-slate-400">
              {c.reasoning}
              <span className="mt-2 block text-[11px] italic text-slate-600">
                Text generated by the pipeline&apos;s language model. Computational output only,
                not experimentally validated.
              </span>
            </p>
          )}
        </div>
      )}
    </article>
  );
}
