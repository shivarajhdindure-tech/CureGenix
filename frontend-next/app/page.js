"use client";

import { useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Home() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  async function runAnalysis() {
    if (!file) return;

    setLoading(true);
    setResult(null);
    setError("");

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(`${API_URL}/api/discover`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Analysis failed");
      }

      setResult(data);
    } catch (err) {
      setError(err.message || "Could not connect to the backend.");
    } finally {
      setLoading(false);
    }
  }

  function getStep(name) {
    return result?.steps?.find((step) => step.agent_name === name);
  }

  const quantumStep = getStep("Quantum Analysis Agent");
  const screeningStep = getStep("Screening Agent");
  const riskStep = getStep("Risk Agent");
  const decisionStep = getStep("Decision Agent");

  const quantumData = quantumStep?.data || {};
  const screeningData = screeningStep?.data || {};
  const riskData = riskStep?.data || {};
  const decisionData = decisionStep?.data || {};

  const quantumCandidates =
    quantumData.molecules?.filter(
      (molecule) =>
        molecule.category === "novel" &&
        molecule.quantum_analysis?.status === "success",
    ) || [];

  const recommendations = decisionData.recommendations || [];

  return (
    <main className="min-h-screen bg-[#05070a] text-white">
      <section className="mx-auto max-w-7xl px-6 py-8">
        {/* HEADER */}
        <header className="mb-12 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">CureGenix</h1>

            <p className="mt-1 text-sm text-gray-500">
              Quantum-Assisted Molecular Analysis
            </p>
          </div>

          <div className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-4 py-2 text-xs text-emerald-400">
            {loading ? "ANALYZING" : "SYSTEM ONLINE"}
          </div>
        </header>

        {/* UPLOAD SECTION */}
        {!result && (
          <div className="grid min-h-[70vh] items-center gap-12 md:grid-cols-2">
            <div>
              <p className="mb-4 text-sm font-medium uppercase tracking-[0.3em] text-emerald-400">
                Quantum Biotech
              </p>

              <h2 className="text-5xl font-bold leading-tight md:text-6xl">
                Molecular analysis,
                <span className="block text-gray-400">
                  enhanced by quantum computing.
                </span>
              </h2>

              <p className="mt-6 max-w-xl text-lg leading-8 text-gray-400">
                Upload a molecular structure and run the CureGenix analysis
                pipeline combining classical molecular processing with
                quantum-assisted computation.
              </p>
            </div>

            <div className="rounded-3xl border border-white/10 bg-white/[0.03] p-8">
              <h3 className="text-xl font-semibold">Analyze Structure</h3>

              <p className="mt-2 text-sm text-gray-500">
                Upload a PDB structure to begin the analysis pipeline.
              </p>

              <label className="mt-8 flex cursor-pointer flex-col items-center justify-center rounded-2xl border border-dashed border-white/20 bg-black/20 px-6 py-12 text-center transition hover:border-emerald-400/50">
                <div className="mb-4 text-4xl">↑</div>

                <span className="text-sm font-medium">
                  {file ? file.name : "Choose a PDB file"}
                </span>

                <span className="mt-2 text-xs text-gray-500">
                  Click to browse your files
                </span>

                <input
                  type="file"
                  accept=".pdb"
                  className="hidden"
                  onChange={(event) => {
                    const selected = event.target.files?.[0];

                    if (selected) {
                      setFile(selected);
                      setError("");
                    }
                  }}
                />
              </label>

              <button
                onClick={runAnalysis}
                disabled={!file || loading}
                className="mt-6 w-full rounded-xl bg-emerald-500 px-5 py-3 font-semibold text-black transition hover:bg-emerald-400 disabled:cursor-not-allowed disabled:opacity-30">
                {loading
                  ? "Running Quantum Analysis..."
                  : "Run Quantum Analysis"}
              </button>

              {error && (
                <div className="mt-5 rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-300">
                  {error}
                </div>
              )}
            </div>
          </div>
        )}

        {/* RESULTS DASHBOARD */}
        {result && (
          <div className="space-y-8">
            {/* TITLE */}
            <div>
              <p className="text-sm uppercase tracking-[0.3em] text-emerald-400">
                Analysis Complete
              </p>

              <h2 className="mt-2 text-4xl font-bold">
                {result.protein_name || "Molecular Analysis"}
              </h2>

              <p className="mt-2 text-gray-500">
                {result.summary || "CureGenix pipeline completed successfully."}
              </p>
            </div>

            {/* OVERVIEW CARDS */}
            <div className="grid gap-4 md:grid-cols-4">
              <Metric
                label="Pipeline Steps"
                value={result.steps?.length || 0}
              />

              <Metric
                label="Candidates"
                value={quantumData.total_candidates || 0}
              />

              <Metric
                label="Quantum Analyzed"
                value={quantumData.successful || 0}
              />

              <Metric
                label="Duration"
                value={`${((result.pipeline_duration_ms || 0) / 1000).toFixed(1)}s`}
              />
            </div>

            {/* PIPELINE */}
            <section className="rounded-3xl border border-white/10 bg-white/[0.03] p-6">
              <div className="mb-6 flex items-center justify-between">
                <div>
                  <h3 className="text-xl font-semibold">Analysis Pipeline</h3>

                  <p className="mt-1 text-sm text-gray-500">
                    Multi-agent molecular analysis workflow
                  </p>
                </div>

                <span className="text-sm text-emerald-400">● Complete</span>
              </div>

              <div className="grid gap-3 md:grid-cols-7">
                {result.steps?.map((step, index) => (
                  <div
                    key={step.agent_name}
                    className="rounded-xl border border-white/10 bg-black/20 p-4">
                    <div className="mb-3 text-xs text-gray-600">
                      0{index + 1}
                    </div>

                    <div className="mb-2 text-emerald-400">✓</div>

                    <p className="text-xs font-medium leading-5">
                      {step.agent_name.replace(" Agent", "")}
                    </p>

                    <p className="mt-2 text-[10px] text-gray-600">
                      {step.duration_ms} ms
                    </p>
                  </div>
                ))}
              </div>
            </section>

            {/* QUANTUM SECTION */}
            <section className="rounded-3xl border border-emerald-500/20 bg-emerald-500/[0.03] p-6">
              <div className="mb-6">
                <p className="text-xs uppercase tracking-[0.25em] text-emerald-400">
                  Quantum Layer
                </p>

                <h3 className="mt-2 text-2xl font-semibold">
                  Quantum-Assisted Molecular Analysis
                </h3>

                <p className="mt-2 max-w-3xl text-sm leading-6 text-gray-500">
                  VQE-based analysis using a reduced active space, Jordan-Wigner
                  mapping and a variational quantum circuit.
                </p>
              </div>

              <div className="grid gap-4 md:grid-cols-4">
                <Metric
                  label="Candidates Analyzed"
                  value={quantumData.successful || 0}
                />

                <Metric
                  label="Qubits"
                  value={
                    quantumCandidates[0]?.quantum_analysis?.hamiltonian
                      ?.qubits || "-"
                  }
                />

                <Metric
                  label="Pauli Terms"
                  value={
                    quantumCandidates[0]?.quantum_analysis?.hamiltonian
                      ?.pauli_terms || "-"
                  }
                />

                <Metric
                  label="Method"
                  value={
                    quantumCandidates[0]?.quantum_analysis?.method || "VQE"
                  }
                />
              </div>
            </section>

            {/* QUANTUM CANDIDATES */}
            <section>
              <div className="mb-5">
                <h3 className="text-2xl font-semibold">
                  Quantum Candidate Analysis
                </h3>

                <p className="mt-1 text-sm text-gray-500">
                  Quantum-derived molecular descriptors from the VQE stage.
                </p>
              </div>

              <div className="grid gap-5 md:grid-cols-2">
                {quantumCandidates.map((candidate) => {
                  const q = candidate.quantum_analysis;

                  return (
                    <div
                      key={candidate.name}
                      className="rounded-2xl border border-white/10 bg-white/[0.03] p-6">
                      <div className="flex items-start justify-between">
                        <div>
                          <h4 className="text-lg font-semibold">
                            {candidate.name}
                          </h4>

                          <p className="mt-1 max-w-md break-all font-mono text-xs text-gray-600">
                            {candidate.smiles}
                          </p>
                        </div>

                        <span className="rounded-full bg-emerald-500/10 px-3 py-1 text-xs text-emerald-400">
                          VQE
                        </span>
                      </div>

                      <div className="mt-6 grid grid-cols-2 gap-3">
                        <Metric
                          label="HOMO-LUMO Gap"
                          value={`${q.homo_lumo_gap_hartree.toFixed(4)} Ha`}
                        />

                        <Metric
                          label="VQE Energy"
                          value={`${q.vqe.electronic_energy_hartree.toFixed(4)} Ha`}
                        />

                        <Metric label="Qubits" value={q.hamiltonian.qubits} />

                        <Metric
                          label="Pauli Terms"
                          value={q.hamiltonian.pauli_terms}
                        />
                      </div>

                      <div className="mt-5 border-t border-white/10 pt-4 text-xs text-gray-500">
                        <span>
                          Active Space: {q.active_space.electrons} electrons /{" "}
                          {q.active_space.spatial_orbitals} orbitals
                        </span>

                        <span className="mx-2">•</span>

                        <span>Mapping: {q.hamiltonian.mapping}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </section>

            {/* RANKING */}
            <section className="rounded-3xl border border-white/10 bg-white/[0.03] p-6">
              <div className="mb-6">
                <h3 className="text-2xl font-semibold">
                  Candidate Prioritization
                </h3>

                <p className="mt-1 text-sm text-gray-500">
                  Computational screening and risk-adjusted ranking.
                </p>
              </div>

              <div className="space-y-3">
                {recommendations.map((candidate) => (
                  <div
                    key={candidate.drug_name}
                    className="grid items-center gap-4 rounded-xl border border-white/10 bg-black/20 p-4 md:grid-cols-[60px_1fr_120px_100px_100px]">
                    <div className="text-2xl font-bold text-gray-600">
                      #{candidate.rank}
                    </div>

                    <div>
                      <p className="font-semibold">{candidate.drug_name}</p>

                      <p className="mt-1 font-mono text-xs text-gray-600">
                        {candidate.smiles}
                      </p>
                    </div>

                    <div>
                      <p className="text-xs text-gray-600">Score</p>

                      <p className="font-semibold">
                        {candidate.adjusted_score?.toFixed(3)}
                      </p>
                    </div>

                    <div>
                      <p className="text-xs text-gray-600">Risk</p>

                      <p className="text-emerald-400">{candidate.risk_level}</p>
                    </div>

                    <div>
                      <p className="text-xs text-gray-600">Confidence</p>

                      <p>{candidate.confidence}</p>
                    </div>
                  </div>
                ))}
              </div>
            </section>

            {/* RISK */}
            <section className="grid gap-5 md:grid-cols-2">
              <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-6">
                <h3 className="text-lg font-semibold">Risk Distribution</h3>

                <div className="mt-5 grid grid-cols-3 gap-3">
                  <Metric
                    label="Low"
                    value={riskData.risk_distribution?.low || 0}
                  />

                  <Metric
                    label="Medium"
                    value={riskData.risk_distribution?.medium || 0}
                  />

                  <Metric
                    label="High"
                    value={riskData.risk_distribution?.high || 0}
                  />
                </div>
              </div>

              <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-6">
                <h3 className="text-lg font-semibold">Best Novel Candidate</h3>

                <p className="mt-4 text-2xl font-bold text-emerald-400">
                  {result.highlights?.best_novel_candidate || "—"}
                </p>

                <p className="mt-2 text-sm text-gray-500">
                  Top computationally prioritized novel candidate.
                </p>
              </div>
            </section>

            {/* RUN AGAIN */}
            <button
              onClick={() => {
                setResult(null);
                setFile(null);
                setError("");
              }}
              className="w-full rounded-xl border border-white/10 bg-white/[0.03] px-5 py-3 text-sm font-medium transition hover:bg-white/[0.07]">
              Analyze Another Structure
            </button>
          </div>
        )}

        <footer className="mt-12 border-t border-white/10 pt-6 text-center text-xs text-gray-600">
          CureGenix • Quantum-assisted molecular analysis prototype
        </footer>
      </section>
    </main>
  );
}

function Metric({ label, value }) {
  return (
    <div className="rounded-xl bg-white/[0.04] p-4">
      <p className="text-xs text-gray-500">{label}</p>

      <p className="mt-2 text-xl font-semibold">{value}</p>
    </div>
  );
}
