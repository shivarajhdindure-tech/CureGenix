"use client";

import { useEffect, useState } from "react";
import { getMolecularActivityModelEvaluation } from "@/lib/molecularActivityMetrics.mjs";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function metric(value) {
  return Number.isFinite(value) ? `${(100 * value).toFixed(1)}%` : "—";
}

export default function MolecularActivityComparison() {
  const [smiles, setSmiles] = useState("");
  const [prediction, setPrediction] = useState(null);
  const [evaluation, setEvaluation] = useState(null);
  const [evaluationStatus, setEvaluationStatus] = useState("loading");
  const [requestStatus, setRequestStatus] = useState("idle");

  useEffect(() => {
    let active = true;
    fetch(`${API_URL}/api/molecular-activity/egfr`)
      .then(async (response) => {
        const payload = await response.json();
        if (!response.ok) throw new Error(payload.detail || "Evaluation unavailable");
        return payload;
      })
      .then((payload) => { if (active) { setEvaluation(payload); setEvaluationStatus("ready"); } })
      .catch(() => { if (active) setEvaluationStatus("unavailable"); });
    return () => { active = false; };
  }, []);

  async function submit(event) {
    event.preventDefault();
    setRequestStatus("loading");
    setPrediction(null);
    try {
      const response = await fetch(`${API_URL}/api/molecular-activity/predict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ smiles }),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail || "Prediction request failed");
      setPrediction(payload);
      setRequestStatus("complete");
    } catch (error) {
      setPrediction({ error: error.message });
      setRequestStatus("failed");
    }
  }

  const predictionModels = prediction?.models || {};
  const cards = [
    { key: "vqc", title: "VQC · trainable variational circuit", metricKey: "vqc" },
    { key: "qgnn", title: "QGNN · graph message passing + PQC", metricKey: "qgnn" },
    { key: "classical_rbf_svm", title: "Classical RBF-SVM baseline", metricKey: "classical_rbf_svm" },
  ];

  return (
    <section id="molecular-activity" className="scroll-mt-24">
      <div className="panel-quantum p-6 md:p-8">
        <p className="eyebrow">Molecular activity proxy</p>
        <h2 className="section-title mt-2">VQC vs QGNN vs classical baseline</h2>
        <p className="mt-2 text-sm leading-6 text-slate-400">
          EGFR retrospective biochemical activity-proxy classification. The saved models were trained offline on the same scaffold-disjoint split; inference requests never train models.
        </p>
        <div className="mt-4 rounded-xl border border-amber-400/25 bg-amber-400/[0.05] p-3 text-xs leading-5 text-amber-100/90">
          Scores are uncalibrated activity-proxy outputs from threshold-derived historical measurements. They are not experimental activity, binding affinity, efficacy, or safety.
        </div>

        {evaluationStatus === "ready" ? (
          <div className="mt-4 grid gap-3 md:grid-cols-3">
            {cards.map(({ key, title, metricKey }) => {
              const { test, trainingStatus } = getMolecularActivityModelEvaluation(evaluation, metricKey);
              return (
                <div key={key} className="rounded-lg border border-white/10 bg-ink-900/60 p-3">
                  <p className="text-xs font-semibold text-white">{title}</p>
                  <p className="mt-2 text-xs text-slate-400">Test balanced accuracy {metric(test?.balanced_accuracy)} · ROC-AUC {Number.isFinite(test?.roc_auc) ? test.roc_auc.toFixed(3) : "—"}</p>
                  {trainingStatus && <p className="mt-1 text-[10px] text-amber-200/80">Training status: {trainingStatus.replaceAll("_", " ")}</p>}
                </div>
              );
            })}
          </div>
        ) : (
          <p role="status" className="mt-4 text-xs text-slate-400">
            {evaluationStatus === "loading" ? "Loading saved evaluation…" : "Saved model evaluation is unavailable; no metrics are being substituted."}
          </p>
        )}

        <form onSubmit={submit} className="mt-5">
          <label htmlFor="activity-smiles" className="block text-xs font-medium text-slate-300">SMILES for the same activity-proxy endpoint</label>
          <div className="mt-2 flex flex-col gap-2 sm:flex-row">
            <input id="activity-smiles" value={smiles} onChange={(event) => setSmiles(event.target.value)} required maxLength={5000} placeholder="Enter a valid molecular SMILES" className="min-w-0 flex-1 rounded-lg border border-white/15 bg-black/20 px-3 py-2 text-sm text-white" />
            <button type="submit" disabled={requestStatus === "loading"} className="btn-primary disabled:opacity-50">{requestStatus === "loading" ? "Evaluating…" : "Compare models"}</button>
          </div>
        </form>

        {prediction?.error && <p role="alert" className="mt-3 text-sm text-rose-300">{prediction.error}</p>}
        {prediction?.models && (
          <div className="mt-4">
            <p className="break-all text-xs text-slate-400">Validated molecule: {prediction.canonical_smiles}</p>
            <div className="mt-3 grid gap-3 md:grid-cols-3">
              {cards.map(({ key, title }) => {
                const result = predictionModels[key];
                return (
                  <div key={key} className="rounded-lg border border-white/10 bg-ink-900/60 p-3">
                    <p className="text-xs font-semibold text-white">{title}</p>
                    <p className="mt-2 text-xs text-slate-300">Status: {result?.status || "unavailable"}</p>
                    {result?.model_id && <p className="mt-1 break-all text-[10px] text-slate-500">{result.model_id}</p>}
                    {result?.prediction && <p className="mt-2 text-sm text-cyan-200">{result.prediction.replaceAll("_", " ")}</p>}
                    {Number.isFinite(result?.probability_active) && <p className="mt-1 text-xs text-slate-400">Uncalibrated active-proxy score: {(100 * result.probability_active).toFixed(1)}%</p>}
                    {result?.reason && <p className="mt-1 text-xs text-amber-200">{result.reason}</p>}
                    {Number.isFinite(result?.runtime_seconds) && <p className="mt-1 text-[10px] text-slate-500">{result.runtime_seconds.toFixed(4)} s</p>}
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
