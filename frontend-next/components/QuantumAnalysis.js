"use client";

import { useState } from "react";
import { fmt, isNum, fmtSeconds } from "@/lib/analysis";

function QMetric({ value, label, sub, accent = false, mono = true }) {
  return (
    <div
      className={`rounded-xl border p-4 ${
        accent
          ? "border-cyan-400/25 bg-gradient-to-br from-cyan-400/[0.09] to-violet-400/[0.06]"
          : "border-white/[0.07] bg-ink-900/60"
      }`}
    >
      <p className={`${mono ? "font-data" : ""} text-2xl font-semibold tracking-tight text-white`}>
        {value}
      </p>
      <p className="mt-1.5 text-xs font-medium uppercase tracking-wider text-slate-400">{label}</p>
      {sub && <p className="mt-0.5 text-[11px] text-slate-500">{sub}</p>}
    </div>
  );
}

// Schematic only: level heights are fixed, the numbers shown are the real
// values returned by the backend.
function OrbitalDiagram({ homo, lumo, gap }) {
  return (
    <div className="rounded-xl border border-white/[0.07] bg-ink-900/60 p-4">
      <p className="metric-label">Frontier orbitals</p>
      <svg viewBox="0 0 260 190" className="mt-2 w-full" role="img" aria-label="Schematic of HOMO and LUMO orbital levels">
        <line x1="40" y1="40" x2="150" y2="40" stroke="#a78bfa" strokeWidth="2.5" strokeLinecap="round" />
        <line x1="40" y1="145" x2="150" y2="145" stroke="#22d3ee" strokeWidth="2.5" strokeLinecap="round" />
        <line x1="95" y1="52" x2="95" y2="133" stroke="#94a3b8" strokeWidth="1" strokeDasharray="3 4" />
        <path d="M91 58 95 50 99 58M91 127 95 135 99 127" stroke="#94a3b8" strokeWidth="1" fill="none" />
        <text x="160" y="36" fill="#c4b5fd" fontSize="11" fontWeight="600">LUMO</text>
        <text x="160" y="50" fill="#94a3b8" fontSize="10" className="font-data">{fmt(lumo, 4)} Ha</text>
        <text x="160" y="141" fill="#67e8f9" fontSize="11" fontWeight="600">HOMO</text>
        <text x="160" y="155" fill="#94a3b8" fontSize="10" className="font-data">{fmt(homo, 4)} Ha</text>
        <text x="105" y="97" fill="#e2e8f0" fontSize="11" className="font-data">Δ {fmt(gap, 4)}</text>
        <text x="40" y="180" fill="#475569" fontSize="9">Schematic, not to scale</text>
      </svg>
    </div>
  );
}

const METHOD_FLOW = [
  "Geometry",
  "Active space",
  "Fermionic Hamiltonian",
  "Jordan-Wigner",
  "VQE",
];

function MethodFlow() {
  return (
    <ol className="flex flex-wrap items-center gap-x-2 gap-y-2" aria-label="Quantum calculation workflow">
      {METHOD_FLOW.map((s, i) => (
        <li key={s} className="flex items-center gap-2">
          <span className="rounded-lg border border-cyan-400/20 bg-cyan-400/[0.07] px-2.5 py-1 text-xs font-medium text-cyan-100">
            {s}
          </span>
          {i < METHOD_FLOW.length - 1 && (
            <span className="text-slate-600" aria-hidden="true">→</span>
          )}
        </li>
      ))}
    </ol>
  );
}

function WhyQuantum() {
  return (
    <div className="rounded-2xl border border-violet-400/20 bg-violet-400/[0.05] p-5">
      <h3 className="text-sm font-semibold text-violet-200">Why quantum?</h3>
      <p className="mt-2 text-sm leading-6 text-slate-300">
        VQE is used here to estimate molecular electronic properties within a
        reduced active-space representation. These quantum-derived descriptors
        are reported alongside classical molecular features for each candidate.
      </p>
      <p className="mt-3 text-xs leading-5 text-slate-500">
        The calculation is a statevector simulation on classical hardware. It
        does not demonstrate quantum advantage and does not predict drug
        efficacy.
      </p>
    </div>
  );
}

function NotRun({ derived }) {
  const { quantumStep, lightMolecules, failedMolecules, summaryCounts } = derived;
  const stepError = quantumStep?.status === "error";

  let title = "VQE analysis was not run for this result";
  let body =
    "No candidates in this response carry VQE results, so no quantum values are shown.";

  if (stepError) {
    title = "The quantum analysis stage reported an error";
    body = quantumStep?.data?.error || quantumStep?.summary || "No error detail was returned.";
  } else if (lightMolecules.length > 0) {
    title = "Backend ran in lightweight descriptor mode";
    body =
      "This deployment returned RDKit molecular descriptors only. VQE, Hamiltonian construction and active-space reduction were not executed, so no quantum values are displayed.";
  } else if (failedMolecules.length > 0) {
    title = "Quantum analysis failed for all targeted candidates";
    body = failedMolecules
      .map((m) => `${m.name}: ${m.quantum_analysis?.message || "unknown error"}`)
      .join(" · ");
  }

  return (
    <div className="rounded-2xl border border-amber-400/25 bg-amber-400/[0.05] p-5">
      <h3 className="text-sm font-semibold text-amber-200">{title}</h3>
      <p className="mt-2 text-sm leading-6 text-slate-300">{body}</p>
      {summaryCounts.quantumTargeted != null && (
        <p className="mt-2 text-xs text-slate-500">
          Candidates targeted for quantum analysis: {summaryCounts.quantumTargeted}
        </p>
      )}
    </div>
  );
}

export default function QuantumAnalysis({ derived }) {
  const { vqeMolecules, quantumStep } = derived;
  const [selected, setSelected] = useState(0);

  const idx = Math.min(selected, Math.max(vqeMolecules.length - 1, 0));
  const mol = vqeMolecules[idx];
  const q = mol?.quantum_analysis;

  return (
    <section id="quantum" className="scroll-mt-24">
      <div className="panel-quantum p-6 md:p-8">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="eyebrow">Quantum Layer</p>
            <h2 className="section-title mt-2">Quantum Analysis</h2>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">
              Quantum-assisted molecular analysis for candidate prioritization.
              VQE-based active-space calculation generates quantum-derived
              molecular descriptors.
            </p>
          </div>
          {isNum(quantumStep?.duration_ms) && (
            <div className="text-right">
              <p className="metric-label">Stage duration</p>
              <p className="font-data mt-1 text-lg font-semibold text-white">{fmtSeconds(quantumStep.duration_ms)}</p>
            </div>
          )}
        </div>

        <div className="mt-6">
          <MethodFlow />
        </div>

        {!q ? (
          <div className="mt-6">
            <NotRun derived={derived} />
          </div>
        ) : (
          <>
            {vqeMolecules.length > 1 && (
              <div role="tablist" aria-label="Quantum-analyzed candidates" className="mt-6 flex flex-wrap gap-2">
                {vqeMolecules.map((m, i) => (
                  <button
                    key={m.name}
                    role="tab"
                    type="button"
                    aria-selected={i === idx}
                    onClick={() => setSelected(i)}
                    className={`font-data rounded-lg border px-3 py-1.5 text-xs transition focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300 ${
                      i === idx
                        ? "border-cyan-400/50 bg-cyan-400/15 text-cyan-100"
                        : "border-white/10 text-slate-400 hover:bg-white/5"
                    }`}
                  >
                    {m.name}
                  </button>
                ))}
              </div>
            )}

            <p className="font-data mt-5 break-all text-xs text-slate-500">
              <span className="text-slate-400">{mol.name}</span> · {mol.smiles}
            </p>

            <div className="mt-4 grid gap-6 lg:grid-cols-[1.6fr_1fr]">
              <div className="grid grid-cols-2 gap-3 md:grid-cols-3">
                <QMetric accent value={q.method || "VQE"} label="Method" sub="Variational solver" mono={false} />
                <QMetric accent value={q.hamiltonian?.qubits ?? "—"} label="Qubits" />
                <QMetric accent value={q.hamiltonian?.pauli_terms ?? "—"} label="Pauli terms" />
                <QMetric
                  value={`${fmt(q.homo_lumo_gap_hartree)} Ha`}
                  label="HOMO-LUMO gap"
                />
                <QMetric
                  value={`${fmt(q.vqe?.electronic_energy_hartree)} Ha`}
                  label="Electronic energy"
                  sub="VQE estimate"
                />
                <QMetric
                  value={
                    q.active_space
                      ? `${q.active_space.electrons}e · ${q.active_space.spatial_orbitals}o`
                      : "—"
                  }
                  label="Active space"
                  sub={q.active_space?.selection_method}
                />
                <QMetric value={q.basis || "—"} label="Basis" />
                <QMetric value={q.vqe?.optimizer || "—"} label="Optimizer" sub={isNum(q.vqe?.max_iterations) ? `max ${q.vqe.max_iterations} iterations` : undefined} />
                <QMetric value={q.vqe?.ansatz || "—"} label="Ansatz" />
              </div>

              <OrbitalDiagram
                homo={q.homo?.energy_hartree}
                lumo={q.lumo?.energy_hartree}
                gap={q.homo_lumo_gap_hartree}
              />
            </div>

            {q.molecular_system && (
              <p className="mt-4 text-xs text-slate-500">
                Full molecular system: {q.molecular_system.total_electrons} electrons ·{" "}
                {q.molecular_system.spatial_orbitals} spatial orbitals ·{" "}
                {q.molecular_system.spin_orbitals} spin orbitals · mapping{" "}
                {q.hamiltonian?.mapping || "—"}
              </p>
            )}
          </>
        )}

        <div className="mt-8">
          <WhyQuantum />
        </div>
      </div>
    </section>
  );
}
