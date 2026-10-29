"use client";

import { useEffect, useState } from "react";
import { VqcQgnnClassicalGroupedChart } from "../charts/ScientificCharts";
import { getMolecularActivityModelEvaluation } from "@/lib/molecularActivityMetrics.mjs";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function MolecularActivityWorkspace() {
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
      .then((payload) => {
        if (active) {
          setEvaluation(payload);
          setEvaluationStatus("ready");
        }
      })
      .catch(() => {
        if (active) setEvaluationStatus("unavailable");
      });
    return () => {
      active = false;
    };
  }, []);

  async function submitPrediction(e) {
    e.preventDefault();
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
    } catch (err) {
      setPrediction({ error: err.message });
      setRequestStatus("failed");
    }
  }

  const predictionModels = prediction?.models || {};

  const modelCards = [
    { key: "vqc", title: "VQC (Variational Quantum Circuit)", metricKey: "vqc", color: "border-teal-300" },
    { key: "qgnn", title: "Molecular QGNN (Graph + PQC)", metricKey: "qgnn", color: "border-violet-300" },
    { key: "classical_rbf_svm", title: "Classical RBF-SVM Baseline", metricKey: "classical_rbf_svm", color: "border-sky-300" },
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-slate-200 pb-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-slate-900 sm:text-2xl">
            Molecular Activity AI &amp; Retrospective Models
          </h2>
          <p className="mt-1 text-sm text-slate-600">
            Retrospective biochemical activity-proxy classification evaluating VQC, QGNN, and classical RBF-SVM baselines.
          </p>
        </div>
        <span className="rounded-full bg-teal-50 border border-teal-200 px-3 py-1 text-xs font-semibold text-teal-800">
          Scaffold Split (Seed 42)
        </span>
      </div>

      {/* Visualization 1: Grouped Bar Chart of VQC, QGNN, and Classical RBF-SVM */}
      <VqcQgnnClassicalGroupedChart />

      {/* Held-Out Metrics Detailed Table */}
      <div className="rounded-xl border border-slate-200/90 bg-white p-6 shadow-sm">
        <h3 className="text-base font-semibold text-slate-900 mb-1">
          Detailed Partition Performance (Test Cohort N = 311)
        </h3>
        <p className="text-xs text-slate-500 mb-4">
          All models trained on identical Murcko scaffold training partition (128 balanced samples) and evaluated on identical test compounds.
        </p>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border border-slate-200 rounded-lg">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-700">
              <tr>
                <th className="py-2.5 px-4 font-semibold">Model Architecture</th>
                <th className="py-2.5 px-4 font-semibold">Test Balanced Acc</th>
                <th className="py-2.5 px-4 font-semibold">Test ROC-AUC</th>
                <th className="py-2.5 px-4 font-semibold">Test Raw Acc</th>
                <th className="py-2.5 px-4 font-semibold">Optimizer &amp; Status</th>
                <th className="py-2.5 px-4 font-semibold">Parameters / Circuit</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-150">
              <tr className="hover:bg-slate-50/60">
                <td className="py-3 px-4 font-semibold text-slate-900">
                  Classical RBF-SVM (Baseline)
                </td>
                <td className="py-3 px-4 font-data font-bold text-sky-700">85.0%</td>
                <td className="py-3 px-4 font-data font-bold text-sky-700">0.911</td>
                <td className="py-3 px-4 font-data text-slate-600">77.8%</td>
                <td className="py-3 px-4 text-slate-600">Exact Solution (scikit-learn)</td>
                <td className="py-3 px-4 text-slate-500">C=1, gamma=scale, balanced</td>
              </tr>
              <tr className="hover:bg-slate-50/60">
                <td className="py-3 px-4 font-semibold text-teal-900">
                  VQC (Variational Circuit)
                </td>
                <td className="py-3 px-4 font-data font-bold text-teal-700">64.8%</td>
                <td className="py-3 px-4 font-data font-bold text-teal-700">0.660</td>
                <td className="py-3 px-4 font-data text-slate-600">64.3%</td>
                <td className="py-3 px-4 text-slate-600">COBYLA (15 evals, converged)</td>
                <td className="py-3 px-4 text-slate-500">4-qubit ZZFeatureMap + RealAmplitudes</td>
              </tr>
              <tr className="hover:bg-slate-50/60">
                <td className="py-3 px-4 font-semibold text-violet-900">
                  Molecular QGNN (Graph + PQC)
                </td>
                <td className="py-3 px-4 font-data font-bold text-violet-700">59.4%</td>
                <td className="py-3 px-4 font-data font-bold text-violet-700">0.614</td>
                <td className="py-3 px-4 font-data text-slate-600">55.6%</td>
                <td className="py-3 px-4 text-amber-700 font-medium">COBYLA MAXFUN (24 evals)</td>
                <td className="py-3 px-4 text-slate-500">Message-passing + 4-qubit RY/RZ PQC</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Interactive SMILES Inference Test Form */}
      <div className="rounded-xl border border-slate-200/90 bg-white p-6 shadow-sm">
        <h3 className="text-base font-semibold text-slate-900 mb-1">
          Interactive Activity-Proxy SMILES Evaluator
        </h3>
        <p className="text-xs text-slate-500 mb-4">
          Query the offline-trained models against any valid candidate SMILES string. Runs instant inference without retraining.
        </p>

        <form onSubmit={submitPrediction} className="space-y-3">
          <div className="flex flex-col sm:flex-row gap-2">
            <input
              type="text"
              value={smiles}
              onChange={(e) => setSmiles(e.target.value)}
              placeholder="e.g. C#Cc1cccc(Nc2ncnc3cc(OCCOC)c(OCCOC)cc23)c1 (Erlotinib)"
              maxLength={5000}
              required
              className="flex-1 rounded-lg border border-slate-300 px-4 py-2.5 font-mono text-xs text-slate-900 placeholder:text-slate-400 focus:border-teal-500 focus:outline-none"
            />
            <button
              type="submit"
              disabled={requestStatus === "loading" || !smiles.trim()}
              className="rounded-lg bg-teal-600 px-5 py-2.5 text-xs font-semibold text-white shadow-sm hover:bg-teal-700 disabled:opacity-50 transition"
            >
              {requestStatus === "loading" ? "Running Inference..." : "Compare Models"}
            </button>
          </div>
        </form>

        {prediction?.error && (
          <div className="mt-4 rounded-lg bg-rose-50 border border-rose-200 p-3 text-xs text-rose-800">
            {prediction.error}
          </div>
        )}

        {prediction?.models && (
          <div className="mt-5 pt-4 border-t border-slate-200">
            <p className="text-xs text-slate-600 mb-3">
              Validated Canonical SMILES: <code className="font-mono text-teal-800 break-all">{prediction.canonical_smiles}</code>
            </p>

            <div className="grid gap-4 md:grid-cols-3">
              {modelCards.map(({ key, title, color }) => {
                const res = predictionModels[key];
                return (
                  <div key={key} className={`rounded-xl border ${color} bg-slate-50/80 p-4 shadow-sm`}>
                    <p className="text-xs font-bold text-slate-900">{title}</p>
                    <div className="mt-2 text-xs space-y-1">
                      <p className="text-slate-500">Status: <span className="font-semibold text-slate-800">{res?.status || "unavailable"}</span></p>
                      {res?.prediction && (
                        <p className="text-sm font-bold text-teal-700 capitalize mt-2">
                          Prediction: {res.prediction.replaceAll("_", " ")}
                        </p>
                      )}
                      {Number.isFinite(res?.probability_active) && (
                        <p className="text-xs text-slate-600">
                          Active Proxy Score: <strong>{(res.probability_active * 100).toFixed(1)}%</strong>
                        </p>
                      )}
                      {Number.isFinite(res?.runtime_seconds) && (
                        <p className="text-[10px] text-slate-400 font-mono">
                          Latency: {(res.runtime_seconds * 1000).toFixed(1)} ms
                        </p>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
