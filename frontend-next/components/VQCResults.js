"use client";

import { useEffect, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function Metric({ label, value }) {
  return (
    <div className="rounded-lg border border-white/10 bg-ink-900/60 p-3">
      <p className="text-[10px] uppercase tracking-wider text-slate-500">{label}</p>
      <p className="font-data mt-1 text-lg font-semibold text-white">{value}</p>
    </div>
  );
}

function pct(value) {
  return Number.isFinite(value) ? `${(value * 100).toFixed(1)}%` : "—";
}

export default function VQCResults() {
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    fetch(`${API_URL}/api/vqc/egfr`)
      .then(async (response) => {
        const payload = await response.json();
        if (!response.ok) throw new Error(payload.detail || "VQC result unavailable.");
        return payload;
      })
      .then((payload) => { if (active) setResult(payload); })
      .catch((err) => { if (active) setError(err.message); });
    return () => { active = false; };
  }, []);

  const vqc = result?.evaluation?.metrics?.vqc?.test;
  const baseline = result?.evaluation?.metrics?.classical_rbf_svm?.test;

  return (
    <section id="vqc" className="scroll-mt-24">
      <div className="panel-quantum p-6 md:p-8">
        <p className="eyebrow">Variational Quantum Classifier</p>
        <h2 className="section-title mt-2">EGFR activity-class prototype</h2>
        {result ? (
          <>
            <p className="mt-2 text-sm leading-6 text-slate-400">
              Trainable 4-qubit RealAmplitudes circuit with cross-entropy, evaluated on the saved scaffold-disjoint test partition. Simulation ran on classical statevector hardware.
            </p>
            <div className="mt-4 rounded-xl border border-amber-400/25 bg-amber-400/[0.05] p-3 text-xs leading-5 text-amber-100/90">
              Labels are conservative pIC50 range thresholds from a heuristically curated biochemical cohort. They are not clinical outcomes, target engagement, or evidence of drug efficacy. This experiment does not demonstrate quantum advantage.
            </div>
            <p className="mt-4 text-xs text-slate-400">
              {result.dataset.label_definition.active} · {result.dataset.label_definition.inactive} · {result.dataset.balanced_training_subset_per_class} balanced training compounds per class · {result.vqc.fit.runtime_seconds.toFixed(2)} s VQC training
            </p>
            <div className="mt-4 grid grid-cols-2 gap-3 md:grid-cols-4">
              <Metric label="VQC test balanced accuracy" value={pct(vqc.balanced_accuracy)} />
              <Metric label="RBF-SVM test balanced accuracy" value={pct(baseline.balanced_accuracy)} />
              <Metric label="VQC test ROC-AUC" value={vqc.roc_auc.toFixed(3)} />
              <Metric label="RBF-SVM test ROC-AUC" value={baseline.roc_auc.toFixed(3)} />
            </div>
            <p className="mt-3 text-xs text-slate-500">
              Same training subset and held-out molecules; 311 test compounds, including 61 inactive and 250 active labels. The classical baseline scores higher on this split. No VQC/QGNN equivalence is implied.
            </p>
          </>
        ) : (
          <p role={error ? "status" : undefined} className="mt-3 text-sm text-slate-400">
            {error || "Loading saved VQC evaluation…"}
          </p>
        )}
      </div>
    </section>
  );
}
