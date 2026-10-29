"use client";

import { useState } from "react";
import QuantumAnalysis from "../QuantumAnalysis";
import QuantumKernelLab from "../QuantumKernelLab";
import { QuantumOutcomeDistributionChart } from "../charts/ScientificCharts";

export default function QuantumLabWorkspace({ derived, result }) {
  const [activeSubTab, setActiveSubTab] = useState("vqe"); // vqe | kernel | policy

  const vqeMolecules = derived?.vqeMolecules || [];
  const resourceSkippedMolecules = derived?.resourceSkippedMolecules || [];
  const candidates = derived?.candidates || [];
  const lightMolecules = derived?.lightMolecules || [];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-slate-200 pb-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-slate-900 sm:text-2xl">
            Quantum Chemistry &amp; Simulation Lab
          </h2>
          <p className="mt-1 text-sm text-slate-600">
            Active-space molecular VQE, PySCF 2.14.0 WSL adapter, and quantum kernel similarity spaces.
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="flex items-center gap-1 rounded-lg border border-slate-200 bg-slate-100 p-1 text-xs">
          <button
            type="button"
            onClick={() => setActiveSubTab("vqe")}
            className={`rounded-md px-3 py-1 font-semibold transition ${
              activeSubTab === "vqe"
                ? "bg-white text-slate-900 shadow-sm"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            Molecular VQE &amp; Orbitals
          </button>
          <button
            type="button"
            onClick={() => setActiveSubTab("kernel")}
            className={`rounded-md px-3 py-1 font-semibold transition ${
              activeSubTab === "kernel"
                ? "bg-white text-slate-900 shadow-sm"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            Quantum Kernel Lab
          </button>
          <button
            type="button"
            onClick={() => setActiveSubTab("policy")}
            className={`rounded-md px-3 py-1 font-semibold transition ${
              activeSubTab === "policy"
                ? "bg-white text-slate-900 shadow-sm"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            Resource Policy &amp; Auditing
          </button>
        </div>
      </div>

      {/* Lightweight Mode Notice if active */}
      {lightMolecules.length > 0 && vqeMolecules.length === 0 && (
        <div role="note" className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-xs text-amber-900 leading-relaxed">
          <strong className="font-semibold text-amber-950">Descriptor Fallback Active:</strong> The pipeline returned RDKit quantum proxy descriptors. Full electronic VQE was bypassed for this run.
        </div>
      )}

      {/* Sub-Tab 1: Molecular VQE */}
      {activeSubTab === "vqe" && (
        <div className="space-y-6">
          <div className="rounded-xl border border-slate-200/90 bg-white p-5 shadow-sm">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-slate-100 pb-3">
              <div>
                <h3 className="text-base font-semibold text-slate-900">
                  Electronic Structure &amp; Variational Quantum Eigensolver
                </h3>
                <p className="text-xs text-slate-500">
                  PySCF Hartree–Fock initial state, fermionic Hamiltonian mapping via Jordan–Wigner, and active-space VQE ground-state energy.
                </p>
              </div>
              <div className="flex items-center gap-2">
                <span className="rounded bg-teal-50 border border-teal-200 text-teal-800 text-xs font-semibold px-2.5 py-0.5">
                  WSL PySCF 2.14.0 Subprocess
                </span>
                <span className="rounded bg-slate-100 border border-slate-200 text-slate-700 text-xs font-semibold px-2.5 py-0.5">
                  Statevector Simulator
                </span>
              </div>
            </div>

            <div className="mt-4">
              <QuantumAnalysis derived={derived || { vqeMolecules: [], lightMolecules: [] }} />
            </div>
          </div>
        </div>
      )}

      {/* Sub-Tab 2: Quantum Kernel Lab */}
      {activeSubTab === "kernel" && (
        <div className="space-y-6">
          <div className="rounded-xl border border-slate-200/90 bg-white p-5 shadow-sm">
            <div className="mb-4">
              <h3 className="text-base font-semibold text-slate-900">
                Quantum Kernel Similarity &amp; Landmark Space
              </h3>
              <p className="text-xs text-slate-500">
                Compute fidelity quantum kernel matrices using ZZFeatureMap. Compare classical RBF vs quantum kernel geometry.
              </p>
            </div>
            <QuantumKernelLab />
          </div>
        </div>
      )}

      {/* Sub-Tab 3: Resource Policy & Execution Outcomes */}
      {activeSubTab === "policy" && (
        <div className="space-y-6">
          {/* Visualization 5: Quantum Execution Outcomes */}
          <QuantumOutcomeDistributionChart
            candidateCount={candidates.length}
            vqeCount={vqeMolecules.length}
            skippedCount={resourceSkippedMolecules.length}
          />

          <div className="rounded-xl border border-slate-200/90 bg-white p-6 shadow-sm">
            <h3 className="text-base font-semibold text-slate-900 mb-2">
              Quantum Resource Admission Policy
            </h3>
            <p className="text-xs text-slate-500 mb-4">
              Rigorous eligibility criteria configured in <code className="text-teal-700 font-mono">quantum_resource_policy.py</code> to ensure numerical stability and prevent statevector memory exhaustion.
            </p>

            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Heavy Atom Limit</span>
                <p className="font-data mt-1 text-xl font-bold text-slate-900">&le; 12 Atoms</p>
                <p className="mt-1 text-xs text-slate-500">Molecules &gt; 12 heavy atoms skip full VQE</p>
              </div>

              <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Allowed Elements</span>
                <p className="font-data mt-1 text-base font-bold text-slate-900">H, C, N, O, F, P, S, Cl</p>
                <p className="mt-1 text-xs text-slate-500">Organic drug-like elements only</p>
              </div>

              <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Basis Set &amp; Active Space</span>
                <p className="font-data mt-1 text-xl font-bold text-slate-900">STO-3G (4e, 4o)</p>
                <p className="mt-1 text-xs text-slate-500">Jordan-Wigner fermion mapping</p>
              </div>

              <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Execution Timeout</span>
                <p className="font-data mt-1 text-xl font-bold text-slate-900">120 Seconds</p>
                <p className="mt-1 text-xs text-slate-500">Subprocess guard via WSL worker</p>
              </div>
            </div>

            <div className="mt-5 rounded-lg bg-slate-100 border border-slate-200 p-3 text-xs text-slate-700">
              <span className="font-semibold text-slate-900">Integrity Rule:</span> Skipped molecules are explicitly disclosed with <code className="font-mono text-teal-800">quantumState = &quot;resource_skipped&quot;</code>. Ground state energy values are left empty or null; they are never substituted with fabricated or approximated values.
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
