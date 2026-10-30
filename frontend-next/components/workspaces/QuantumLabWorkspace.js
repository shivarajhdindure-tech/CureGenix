"use client";

import { useState } from "react";
import MolecularTargetSelector from "../MolecularTargetSelector";
import QuantumAnalysis from "../QuantumAnalysis";
import QuantumKernelLab from "../QuantumKernelLab";
import H2OWorkflow from "../H2OWorkflow";
import { QuantumOutcomeDistributionChart } from "../charts/ScientificCharts";
import { QUANTUM_RESOURCE_DEFAULTS } from "../../lib/quantumLabTransparency.mjs";

export default function QuantumLabWorkspace({ derived, result, activeStructure = null }) {
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

        {/* Tab Switcher & Active PDB Provenance */}
        <div className="flex flex-wrap items-center gap-2">
          {activeStructure?.pdbId && (
            <span className="rounded bg-teal-50 border border-teal-200 text-teal-900 text-xs font-bold px-2.5 py-1 font-mono">
              PDB: {activeStructure.pdbId} ({activeStructure.selectedChainId ? `Chain ${activeStructure.selectedChainId}` : "Chain A"})
            </span>
          )}
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
            onClick={() => setActiveSubTab("h2o")}
            className={`rounded-md px-3 py-1 font-semibold transition ${
              activeSubTab === "h2o"
                ? "bg-white text-slate-900 shadow-sm"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            H₂O Experiment
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
          {/* Phase 3 Unified Molecular Calculation Target & Provenance Selector */}
          <MolecularTargetSelector
            activeStructure={activeStructure}
            derived={derived}
          />

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
                  Local PySCF when available; otherwise WSL PySCF
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

      {activeSubTab === "h2o" && <H2OWorkflow />}

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
              Configurable size guardrails from <code className="text-teal-700 font-mono">quantum_resource_policy.py</code>. These are rough eligibility checks, not exact memory or runtime predictions.
            </p>

            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
              <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Heavy Atom Limit</span>
                <p className="font-data mt-1 text-xl font-bold text-slate-900">&le; {QUANTUM_RESOURCE_DEFAULTS.maxHeavyAtoms} heavy atoms</p>
                <p className="mt-1 text-xs text-slate-500">Larger molecules are skipped by default; environment settings can change this limit.</p>
              </div>

              <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Total Atom Limit</span>
                <p className="font-data mt-1 text-xl font-bold text-slate-900">&le; {QUANTUM_RESOURCE_DEFAULTS.maxTotalAtoms} atoms</p>
                <p className="mt-1 text-xs text-slate-500">Configurable default admission threshold.</p>
              </div>

              <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Estimated STO-3G Functions</span>
                <p className="font-data mt-1 text-xl font-bold text-slate-900">&le; {QUANTUM_RESOURCE_DEFAULTS.maxEstimatedBasisFunctions}</p>
                <p className="mt-1 text-xs text-slate-500">Rough tabulated estimate, not an exact memory limit.</p>
              </div>

              <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Basis Set &amp; Active Space</span>
                <p className="font-data mt-1 text-xl font-bold text-slate-900">Generic: 2e, 2o</p>
                <p className="mt-1 text-xs text-slate-500">HOMO/LUMO active orbitals; STO-3G, Jordan–Wigner. Dedicated H₂O uses 4e/4o.</p>
              </div>

              <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">WSL Worker Timeout</span>
                <p className="font-data mt-1 text-xl font-bold text-slate-900">{QUANTUM_RESOURCE_DEFAULTS.wslTimeoutSeconds} seconds default</p>
                <p className="mt-1 text-xs text-slate-500">Configurable with CUREGENIX_WSL_TIMEOUT; local PySCF uses this WSL timeout only when routed through WSL.</p>
              </div>
            </div>

            <p className="mt-4 text-xs text-slate-600">Supported resource-estimate elements are H through Ar with STO-3G; estimates for other elements or bases are unavailable. Generic SMILES VQE default: {QUANTUM_RESOURCE_DEFAULTS.genericDefaultIterations} optimizer iterations; policy maximum: {QUANTUM_RESOURCE_DEFAULTS.maxVqeIterations}. Generic SMILES VQE uses a 2e/2o HOMO/LUMO model. The separate H₂O workflow uses a 4e/4o active space and its UI requests 50 iterations (API range 1–500).</p>

            <div className="mt-5 rounded-lg bg-slate-100 border border-slate-200 p-3 text-xs text-slate-700">
              <span className="font-semibold text-slate-900">Integrity Rule:</span> Skipped molecules are explicitly disclosed with <code className="font-mono text-teal-800">quantumState = &quot;resource_skipped&quot;</code>. Ground state energy values are left empty or null; they are never substituted with fabricated or approximated values.
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
