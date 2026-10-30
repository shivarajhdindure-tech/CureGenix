"use client";

import { useEffect, useState } from "react";
import { optimizerStatusLabel, QUANTUM_RESOURCE_DEFAULTS } from "../lib/quantumLabTransparency.mjs";
import { isIdealSimulatorStatevector, sortStatevectorProbabilities } from "../lib/statevectorDisplay.mjs";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const DEFAULT_STATEVECTOR_RECORD_ID = "simulator-d33cf70ce6ac47b0809ebd853ca7203a";

export default function H2OWorkflow() {
  const [reference, setReference] = useState(null);
  const [simulator, setSimulator] = useState(null);
  const [preflight, setPreflight] = useState(null);
  const [environment, setEnvironment] = useState(null);
  const [timeoutSeconds, setTimeoutSeconds] = useState(QUANTUM_RESOURCE_DEFAULTS.h2oSimulatorTimeoutSeconds);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [statevectorRecordId, setStatevectorRecordId] = useState(DEFAULT_STATEVECTOR_RECORD_ID);
  const [statevector, setStatevector] = useState(null);
  const [statevectorLoading, setStatevectorLoading] = useState(false);
  const [statevectorError, setStatevectorError] = useState("");

  useEffect(() => {
    let active = true;
    fetch(`${API_URL}/api/quantum-chemistry/h2o/preflight`)
      .then((response) => (response.ok ? response.json() : null))
      .then((data) => { if (active && data) setPreflight(data); })
      .catch(() => { if (active) setPreflight({ unavailable: true }); });
    fetch(`${API_URL}/api/quantum-chemistry/h2o/environment`)
      .then((response) => (response.ok ? response.json() : null))
      .then((data) => { if (active) setEnvironment(data || { ready: false, message: "WSL readiness could not be checked. Calculation requests may still return a backend error." }); })
      .catch(() => { if (active) setEnvironment({ ready: false, message: "WSL readiness could not be checked. Calculation requests may still return a backend error." }); });
    return () => { active = false; };
  }, []);

  async function request(path, body) {
    setBusy(path);
    setError("");
    try {
      const response = await fetch(`${API_URL}/api/quantum-chemistry/h2o/${path}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data?.detail?.message || data?.detail || `Request failed (${response.status})`);
      return data;
    } catch (requestError) {
      setError(String(requestError.message || requestError));
      return null;
    } finally {
      setBusy("");
    }
  }

  async function runReference() {
    const result = await request("classical", {});
    if (result) {
      setReference(result);
      setSimulator(null);
    }
  }

  async function runSimulator() {
    if (!reference?.experiment_record_id) return;
    const result = await request("simulator", {
      classical_record_id: reference.experiment_record_id,
      maxiter: 50,
      timeout_seconds: timeoutSeconds,
    });
    if (result) {
      setSimulator(result);
      if (result.experiment_record_id) setStatevectorRecordId(result.experiment_record_id);
      setStatevector(null);
    }
  }

  async function showFinalStatevector() {
    const recordId = statevectorRecordId.trim();
    setStatevector(null);
    setStatevectorError("");
    setStatevectorLoading(true);
    try {
      const response = await fetch(
        `${API_URL}/api/quantum-chemistry/h2o/statevector/${encodeURIComponent(recordId)}`
      );
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data?.detail?.message || data?.detail || `Request failed (${response.status})`);
      }
      if (!isIdealSimulatorStatevector(data)) {
        throw new Error("The backend response was not an ideal simulator statevector.");
      }
      setStatevector(data);
    } catch (requestError) {
      setStatevectorError(String(requestError.message || requestError));
    } finally {
      setStatevectorLoading(false);
    }
  }

  const full = reference?.full_system;
  const active = reference?.active_space;
  const vqe = simulator?.simulator;
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm" aria-labelledby="h2o-workflow-title">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 id="h2o-workflow-title" className="text-base font-semibold text-slate-900">H₂O / STO-3G experiment</h3>
          <p className="mt-1 text-xs text-slate-600">Neutral singlet, configurable equilibrium-like geometry (O–H 0.9572 Å, H–O–H 104.5°). Jobs run only after a button press through the WSL worker (default timeout {QUANTUM_RESOURCE_DEFAULTS.wslTimeoutSeconds} seconds; configurable).</p>
        </div>
        <span className="rounded border border-slate-200 bg-slate-50 px-2 py-1 text-xs text-slate-700">No hardware job is submitted here</span>
      </div>

      <div className="mt-4 flex flex-wrap items-end gap-2">
        <button type="button" onClick={runReference} disabled={Boolean(busy)} className="rounded-lg bg-slate-900 px-3 py-2 text-sm font-semibold text-white disabled:opacity-50">
          {busy === "classical" ? "Running classical reference…" : "Run PySCF reference"}
        </button>
        <button type="button" onClick={runSimulator} disabled={Boolean(busy) || !reference?.experiment_record_id || !Number.isInteger(timeoutSeconds) || timeoutSeconds < 1 || timeoutSeconds > 14400} className="rounded-lg border border-teal-300 bg-teal-50 px-3 py-2 text-sm font-semibold text-teal-900 disabled:opacity-50">
          {busy === "simulator" ? "Running WSL statevector VQE…" : "Run WSL Qiskit statevector VQE"}
        </button>
        <label className="text-xs font-medium text-slate-700">
          Simulator timeout (seconds)
          <input
            aria-label="Simulator timeout in seconds"
            type="number"
            min="1"
            max="14400"
            value={timeoutSeconds}
            onChange={(event) => setTimeoutSeconds(Number(event.target.value))}
            disabled={Boolean(busy)}
            className="mt-1 block w-36 rounded-md border border-slate-300 px-2 py-2 text-sm"
          />
        </label>
      </div>

      {environment && <p role="status" className={`mt-3 rounded-lg border p-2 text-xs ${environment.ready ? "border-emerald-200 bg-emerald-50 text-emerald-800" : "border-amber-200 bg-amber-50 text-amber-900"}`}>WSL environment: {environment.message}</p>}
      <p className="mt-2 text-xs text-slate-500">Timeout is sent per simulator request (default {QUANTUM_RESOURCE_DEFAULTS.h2oSimulatorTimeoutSeconds} seconds; allowed 1–14,400). A timeout leaves no simulator result record; a retry creates a separate record if it completes.</p>

      {preflight && !preflight.unavailable && <p className="mt-2 text-xs text-slate-600">Preflight only (no PySCF run): expected full STO-3G size {preflight.electron_count} electrons / {preflight.spatial_orbitals_sto3g_expected} spatial orbitals / {preflight.resource_estimates.full_system.qubits} Jordan–Wigner qubits; the selected active model uses {preflight.resource_estimates.active_space.qubits} qubits. Statevector estimates exclude PySCF memory and wall time.</p>}
      {preflight?.unavailable && <p role="status" className="mt-2 text-xs text-amber-800">H₂O resource preflight is unavailable; no simulator validation status is inferred from this.</p>}

      {error && <p role="alert" className="mt-3 rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-800">{error}</p>}

      {reference && (
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          <div className="rounded-lg bg-slate-50 p-3 text-sm">
            <h4 className="font-semibold text-slate-900">Classical reference</h4>
            <p className="mt-1 text-slate-700">RHF total: {reference.references?.rhf?.total_energy_hartree?.toFixed(8) ?? "unavailable"} Ha</p>
            <p className="text-slate-700">Full-space FCI: {reference.references?.full_space_fci?.status === "completed" ? `${reference.references.full_space_fci.total_energy_hartree.toFixed(8)} Ha` : (reference.references?.full_space_fci?.status || "unavailable")}</p>
            <p className="text-slate-700">System: {full?.electron_count ?? "—"} e⁻ · {full?.spatial_orbitals ?? "—"} spatial orbitals · {full?.spin_orbitals ?? "—"} spin orbitals · {full?.mapped_qubits ?? "—"} JW qubits · {full?.pauli_term_count ?? "—"} Pauli terms</p>
            <p className="mt-1 text-xs text-slate-500">Saved: {reference.saved_record}</p>
          </div>
          <div className="rounded-lg bg-teal-50 p-3 text-sm">
            <h4 className="font-semibold text-teal-950">Active-space model</h4>
            <p className="mt-1 text-teal-900">4e / {active?.active_spatial_orbitals ?? "—"}o · {active?.mapped_qubits ?? "—"} JW qubits · {active?.pauli_term_count ?? "—"} Pauli terms</p>
            <p className="text-xs text-teal-800">Active orbitals: 3–6 (zero-based); frozen orbitals: 0–2. The model uses 4 active electrons, 4 spatial orbitals, and 8 qubits. This compact active space is an exploratory model, not a complete water calculation.</p>
          </div>
        </div>
      )}

      <p className="mt-3 rounded-lg border border-slate-200 bg-slate-50 p-3 text-xs text-slate-700">The H₂O VQE energy is comparable to CASCI for this same 4e/4o active-space Hamiltonian. Do not compare it as if it used the full-space FCI Hamiltonian. {simulator ? "A completed simulator result record is loaded below." : "No completed H₂O simulator result record is loaded; the simulator workflow is not yet validated by a completed result."}</p>

      {vqe && (
        <div className="mt-3 rounded-lg border border-indigo-200 bg-indigo-50 p-3 text-sm text-indigo-950">
          Local Statevector VQE: {vqe.total_energy_hartree?.toFixed(8)} Ha; active-space CASCI: {vqe.active_space_exact_total_energy_hartree?.toFixed(8)} Ha; |Δ|={vqe.absolute_difference_from_same_active_space_exact_hartree?.toFixed(8)} Ha. {optimizerStatusLabel(vqe.optimizer_success)}; {vqe.iterations ?? "?"} iterations. This comparison uses the same active-space Hamiltonian.
          <p className="mt-1 text-xs">Evaluations: {vqe.evaluations ?? "unavailable"} · VQE runtime: {vqe.runtime_seconds != null ? `${vqe.runtime_seconds}s` : "unavailable"} · {vqe.circuit?.qubits ?? "?"} qubits · circuit depth {vqe.circuit?.depth ?? "unavailable"} · gate counts {JSON.stringify(vqe.circuit?.gate_counts ?? {})}</p>
          <p className="mt-1 text-xs">Saved: {simulator.saved_record}</p>
        </div>
      )}

      <div className="mt-4 rounded-xl border border-indigo-200 bg-indigo-50/70 p-4" aria-labelledby="h2o-statevector-title" aria-busy={statevectorLoading}>
        <div className="flex flex-wrap items-end gap-3">
          <label className="min-w-64 flex-1 text-xs font-medium text-slate-700">
            Completed simulator experiment ID
            <input
              aria-label="Completed simulator experiment ID"
              type="text"
              value={statevectorRecordId}
              maxLength={43}
              autoComplete="off"
              onChange={(event) => {
                setStatevectorRecordId(event.target.value);
                setStatevector(null);
                setStatevectorError("");
              }}
              className="mt-1 block w-full rounded-md border border-slate-300 bg-white px-2 py-2 font-mono text-xs"
            />
          </label>
          <button
            type="button"
            onClick={showFinalStatevector}
            disabled={statevectorLoading || !statevectorRecordId.trim()}
            className="rounded-lg border border-indigo-300 bg-white px-3 py-2 text-sm font-semibold text-indigo-900 disabled:opacity-50"
          >
            Show final statevector
          </button>
        </div>
        <h4 id="h2o-statevector-title" className="mt-3 text-sm font-semibold text-indigo-950">Final ideal simulator state</h4>
        <p className="mt-1 text-xs text-indigo-900">This reads saved optimized parameters and simulates only the final bound circuit. It does not rerun VQE/SLSQP and does not show intermediate optimization states.</p>
        {statevectorLoading && <p role="status" className="mt-2 text-sm text-indigo-800">Reconstructing final statevector…</p>}
        {statevectorError && <p role="alert" className="mt-2 text-sm text-rose-800">{statevectorError}</p>}
        {statevector && (() => {
          const orderedStates = sortStatevectorProbabilities(statevector.states);
          const renderState = (item) => (
            <tr key={item.basis_state} className="border-t border-indigo-100">
              <td className="px-2 py-1.5 font-mono">|{item.basis_state}⟩</td>
              <td className="px-2 py-1.5 text-right font-mono">{item.amplitude_real.toExponential(5)} {item.amplitude_imag < 0 ? "−" : "+"} {Math.abs(item.amplitude_imag).toExponential(5)}i</td>
              <td className="px-2 py-1.5 text-right font-mono">{item.probability.toFixed(8)}</td>
            </tr>
          );
          return (
            <div className="mt-3 rounded-lg border border-indigo-200 bg-white p-3 text-xs text-slate-800">
              <p role="status" className="font-semibold text-emerald-800">Final statevector reconstructed successfully from the saved experiment.</p>
              <p className="font-semibold">Ideal Qiskit statevector · {statevector.qubit_count} qubits · dimension {statevector.statevector_dimension}</p>
              <p className="mt-1">Normalization: Σ probability = {statevector.normalization_check.probability_sum.toFixed(12)}; {statevector.normalization_check.normalized ? "passed" : "failed"}.</p>
              <p className="mt-2">Amplitude is complex (real + imaginary parts). Probability is its squared magnitude, |amplitude|². Probabilities depend on the computational measurement basis; bitstrings are shown as q[n−1]…q0, with q0 at the right.</p>
              <p className="mt-1">This is an ideal simulator-derived state, not a hardware measurement. Hardware shot probabilities and uncertainties are separate results and are not shown here. It does not indicate binding, efficacy, or quantum advantage.</p>
              <div className="mt-3 overflow-x-auto">
                <table className="w-full min-w-[34rem] text-left">
                  <thead><tr><th className="px-2 pb-1">Basis state</th><th className="px-2 pb-1 text-right">Amplitude</th><th className="px-2 pb-1 text-right">Probability</th></tr></thead>
                  <tbody>{orderedStates.slice(0, 12).map(renderState)}</tbody>
                </table>
              </div>
              <details className="mt-3">
                <summary className="cursor-pointer font-semibold text-indigo-900">Show all {statevector.statevector_dimension} basis states</summary>
                <div className="mt-2 max-h-96 overflow-auto">
                  <table className="w-full min-w-[34rem] text-left">
                    <thead className="sticky top-0 bg-white"><tr><th className="px-2 py-1">Basis state</th><th className="px-2 py-1 text-right">Amplitude</th><th className="px-2 py-1 text-right">Probability</th></tr></thead>
                    <tbody>{orderedStates.map(renderState)}</tbody>
                  </table>
                </div>
              </details>
            </div>
          );
        })()}
      </div>
      <p className="mt-3 text-xs text-slate-500">These calculations report isolated-molecule electronic energies. They do not predict protein binding, efficacy, or safety.</p>
    </section>
  );
}
