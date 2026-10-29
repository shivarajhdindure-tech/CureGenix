"use client";

import { useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function Metric({ label, value, note }) {
  return (
    <div className="rounded-xl border border-white/[0.08] bg-ink-900/60 p-4">
      <p className="text-xs uppercase tracking-wider text-slate-400">{label}</p>
      <p className="font-data mt-2 text-2xl font-semibold text-white">
        {value}
      </p>
      {note && <p className="mt-1 text-xs text-slate-500">{note}</p>}
    </div>
  );
}

function Heatmap({ matrix }) {
  if (!Array.isArray(matrix) || matrix.length === 0) return null;

  const values = matrix.flat();
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;

  return (
    <div className="overflow-x-auto">
      <div
        className="grid gap-1"
        style={{
          gridTemplateColumns: `repeat(${matrix.length}, minmax(24px, 1fr))`,
          minWidth: `${matrix.length * 28}px`,
        }}
        role="img"
        aria-label="Quantum kernel matrix heatmap; brighter cells indicate higher kernel similarity">
        {matrix.flatMap((row, i) =>
          row.map((value, j) => {
            const intensity = Math.round(15 + ((value - min) / range) * 85);

            return (
              <div
                key={`${i}-${j}`}
                title={`K[${i}, ${j}] = ${Number(value).toFixed(3)}`}
                className="flex aspect-square items-center justify-center rounded-sm text-[9px] text-white"
                style={{
                  backgroundColor: `rgb(${Math.round(intensity * 0.15)}, ${Math.round(intensity * 1.5)}, ${Math.round(intensity * 2.2)})`,
                }}>
                {Number(value).toFixed(2)}
              </div>
            );
          }),
        )}
      </div>
    </div>
  );
}

export default function QuantumKernelLab() {
  const [task, setTask] = useState("classification");
  const [landmarks, setLandmarks] = useState(4);
  const [seed, setSeed] = useState(42);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function runExperiment() {
    setLoading(true);
    setError("");
    setResult(null);

    try {
      const response = await fetch(`${API_URL}/api/quantum-kernel/demo`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ task, landmarks, seed }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Quantum kernel experiment failed.");
      }

      setResult(data);
    } catch (err) {
      setError(
        err.message ||
          "Could not connect to the backend. Check that FastAPI is running.",
      );
    } finally {
      setLoading(false);
    }
  }

  const metricName = result?.metric;
  const quantumMetric = result?.quantum_kernel_model?.[metricName];
  const classicalMetric = result?.classical_rbf_baseline?.[metricName];
  const lowerIsBetter = task === "regression";

  function formatMetric(value) {
    if (typeof value !== "number" || !Number.isFinite(value)) return "—";
    return `${(value * (metricName === "test_accuracy" ? 100 : 1)).toFixed(3)}${
      metricName === "test_accuracy" ? "%" : ""
    }`;
  }

  return (
    <section id="quantum-kernel-lab" className="scroll-mt-24">
      <div className="panel-quantum p-6 md:p-8">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="eyebrow">Quantum-kernel SVM/SVR</p>
            <h2 className="section-title mt-2">Quantum Kernel Demo</h2>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">
              Explore fidelity-based quantum kernels, Nyström approximation, and
              a classical RBF baseline in a reproducible simulator experiment.
            </p>
          </div>
          <span className="rounded-lg border border-cyan-400/25 bg-cyan-400/[0.08] px-3 py-1.5 text-xs text-cyan-200">
            Statevector simulator
          </span>
        </div>

        <div
          role="note"
          className="mt-5 rounded-xl border border-amber-400/25 bg-amber-400/[0.05] p-4 text-sm leading-6 text-amber-100">
          This experiment currently uses synthetic demonstration data, not
          measured drug activity. Its metrics do not establish drug efficacy or
          quantum advantage.
        </div>

        <div className="mt-6 grid gap-5 md:grid-cols-3">
          <label className="block">
            <span className="metric-label">Learning task</span>
            <select
              value={task}
              onChange={(event) => {
                setTask(event.target.value);
                setResult(null);
              }}
              className="mt-2 w-full rounded-xl border border-white/10 bg-ink-900 px-3 py-3 text-sm text-white">
              <option value="classification">QSVM classification</option>
              <option value="regression">QSVR regression</option>
            </select>
          </label>

          <label className="block">
            <span className="metric-label">Nyström landmarks: {landmarks}</span>
            <input
              type="range"
              min="2"
              max="6"
              step="1"
              value={landmarks}
              onChange={(event) => {
                setLandmarks(Number(event.target.value));
                setResult(null);
              }}
              className="mt-4 w-full accent-cyan-400"
            />
            <span className="mt-1 block text-xs text-slate-500">
              More landmarks increase the kernel approximation cost.
            </span>
          </label>

          <label className="block">
            <span className="metric-label">Random seed</span>
            <input
              type="number"
              min="0"
              max="100000"
              value={seed}
              onChange={(event) => {
                const next = Number(event.target.value);
                if (Number.isInteger(next) && next >= 0 && next <= 100000) {
                  setSeed(next);
                  setResult(null);
                }
              }}
              className="mt-2 w-full rounded-xl border border-white/10 bg-ink-900 px-3 py-3 text-sm text-white"
            />
          </label>
        </div>

        <div className="mt-5 flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={runExperiment}
            disabled={loading}
            className="btn-primary disabled:cursor-not-allowed disabled:opacity-50">
            {loading ? "Running experiment…" : "Run quantum experiment"}
          </button>
          {result && (
            <span className="text-xs text-emerald-300">
              Experiment completed · seed {result.seed}
            </span>
          )}
        </div>

        {error && (
          <div
            role="alert"
            className="mt-4 rounded-xl border border-red-400/25 bg-red-400/[0.05] p-4 text-sm text-red-200">
            {error}
          </div>
        )}

        {result && (
          <div className="mt-8 space-y-6">
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              <Metric label="Training samples" value={result.train_samples} />
              <Metric label="Test samples" value={result.test_samples} />
              <Metric
                label="Landmarks"
                value={result.landmark_count}
                note="Selected from training data"
              />
              <Metric
                label="Runtime"
                value={`${result.runtime_seconds.toFixed(3)} s`}
                note="Includes quantum-kernel and model fitting"
              />
            </div>

            <div className="grid gap-5 lg:grid-cols-2">
              <div className="rounded-xl border border-white/[0.08] bg-ink-900/50 p-5">
                <h3 className="text-sm font-semibold text-white">
                  Quantum-kernel model
                </h3>
                <p className="mt-1 text-xs text-slate-500">
                  ZZ feature map · fidelity kernel · Nyström approximation
                </p>
                <p className="font-data mt-5 text-3xl font-semibold text-cyan-200">
                  {formatMetric(quantumMetric)}
                </p>
                <p className="mt-1 text-xs text-slate-400">
                  {metricName === "test_accuracy"
                    ? "Held-out accuracy"
                    : "Held-out mean absolute error"}
                </p>
              </div>

              <div className="rounded-xl border border-white/[0.08] bg-ink-900/50 p-5">
                <h3 className="text-sm font-semibold text-white">
                  Classical RBF baseline
                </h3>
                <p className="mt-1 text-xs text-slate-500">
                  Scikit-learn · same train/test split
                </p>
                <p className="font-data mt-5 text-3xl font-semibold text-violet-200">
                  {formatMetric(classicalMetric)}
                </p>
                <p className="mt-1 text-xs text-slate-400">
                  {metricName === "test_accuracy"
                    ? "Held-out accuracy"
                    : "Held-out mean absolute error"}
                </p>
              </div>
            </div>

            {typeof quantumMetric === "number" &&
              typeof classicalMetric === "number" && (
                <div className="rounded-xl border border-white/[0.08] bg-ink-900/50 p-5">
                  <h3 className="text-sm font-semibold text-white">
                    Metric comparison
                  </h3>
                  <p className="mt-1 text-xs text-slate-500">
                    {lowerIsBetter
                      ? "Lower MAE is better."
                      : "Higher accuracy is better."}
                  </p>
                  {[
                    ["Quantum kernel", quantumMetric],
                    ["Classical RBF", classicalMetric],
                  ].map(([label, value]) => {
                    const scale =
                      metricName === "test_accuracy"
                        ? 1
                        : Math.max(quantumMetric, classicalMetric, 1e-9);
                    const width = Math.max(
                      2,
                      Math.min(100, (Number(value) / scale) * 100),
                    );

                    return (
                      <div key={label} className="mt-4">
                        <div className="mb-1 flex justify-between gap-3 text-xs">
                          <span className="text-slate-300">{label}</span>
                          <span className="font-data text-white">
                            {formatMetric(Number(value))}
                          </span>
                        </div>
                        <div className="h-2 overflow-hidden rounded-full bg-white/5">
                          <div
                            className={`h-full rounded-full ${
                              label === "Quantum kernel"
                                ? "bg-cyan-400"
                                : "bg-violet-400"
                            }`}
                            style={{ width: `${width}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}

            <div className="rounded-xl border border-white/[0.08] bg-ink-900/50 p-5">
              <h3 className="text-sm font-semibold text-white">
                Landmark kernel matrix
              </h3>
              <p className="mb-4 mt-1 text-xs leading-5 text-slate-500">
                Cell values show pairwise fidelity-kernel values between
                selected landmarks. Hover over a cell for its numeric value.
              </p>
              <Heatmap matrix={result.kernel_visualization?.landmark_kernel} />
            </div>

            <div className="rounded-xl border border-white/[0.08] bg-ink-900/50 p-5">
              <h3 className="text-sm font-semibold text-white">
                Experiment details
              </h3>
              <dl className="mt-3 grid gap-3 text-sm sm:grid-cols-2">
                <div>
                  <dt className="text-slate-500">Dataset</dt>
                  <dd className="mt-1 text-slate-200">
                    {result.dataset.replaceAll("_", " ")}
                  </dd>
                </div>
                <div>
                  <dt className="text-slate-500">Evaluation</dt>
                  <dd className="mt-1 text-slate-200">
                    {result.evaluation.replaceAll("_", " ")}
                  </dd>
                </div>
                <div>
                  <dt className="text-slate-500">Method</dt>
                  <dd className="mt-1 text-slate-200">
                    {result.quantum_method}
                  </dd>
                </div>
                <div>
                  <dt className="text-slate-500">Execution hardware</dt>
                  <dd className="mt-1 text-slate-200">{result.hardware}</dd>
                </div>
              </dl>
              <p className="mt-4 text-xs leading-5 text-amber-200/80">
                {result.scientific_warning}
              </p>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
