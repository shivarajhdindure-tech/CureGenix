"use client";

import { useState } from "react";
import CandidateCard from "../CandidateCard";
import Molecule3DExplorer from "../Molecule3DExplorer";
import ProteinPDBViewer from "../ProteinPDBViewer";
import DiscoveryStrategySimulator from "../DiscoveryStrategySimulator";
import { CandidateScreeningComparisonChart } from "../charts/ScientificCharts";

export default function MoleculeDiscoveryWorkspace({
  result,
  derived,
  activeStructure = null,
  onNavigateToRisk = null,
}) {
  const candidates = derived?.candidates || [];
  const featured = derived?.bestNovel;
  const others = candidates.filter((c) => c !== featured);
  const demonstrationCandidates = derived?.demonstrationCandidates || [];
  const hasScoreTies = derived?.hasScoreTies || false;

  const targetPdbId = activeStructure?.pdbId || result?.protein?.pdb_id || "1M17";
  const targetProteinName = activeStructure?.proteinName || result?.protein_name || "Target Protein Structure";
  const [activeTab, setActiveTab] = useState("cards"); // cards | protein-pdb | 3d | simulator

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-slate-200 pb-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-slate-900 sm:text-2xl">
            Molecule Discovery &amp; Candidate Prioritization
          </h2>
          <p className="mt-1 text-sm text-slate-600">
            Target-aware candidate generation, multi-objective screening, 3D macromolecular protein structure, conformational visualization, and evidence passports.
          </p>
        </div>

        {/* View Switcher Pills */}
        <div className="flex flex-wrap items-center gap-1 rounded-lg border border-slate-200 bg-slate-100 p-1 text-xs">
          <button
            type="button"
            onClick={() => setActiveTab("cards")}
            className={`rounded-md px-3 py-1 font-semibold transition ${
              activeTab === "cards"
                ? "bg-white text-slate-900 shadow-sm"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            Candidate Cards ({candidates.length})
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("protein-pdb")}
            className={`rounded-md px-3 py-1 font-semibold transition flex items-center gap-1.5 ${
              activeTab === "protein-pdb"
                ? "bg-white text-teal-900 shadow-sm font-bold"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <span>Protein Target 3D (PDB)</span>
            <span className="rounded bg-teal-100 text-teal-800 text-[10px] px-1.5 py-0.2 font-mono">
              {targetPdbId}
            </span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("3d")}
            className={`rounded-md px-3 py-1 font-semibold transition ${
              activeTab === "3d"
                ? "bg-white text-slate-900 shadow-sm"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            3D Molecular Conformations
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("simulator")}
            className={`rounded-md px-3 py-1 font-semibold transition ${
              activeTab === "simulator"
                ? "bg-white text-slate-900 shadow-sm"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            Strategy Simulator
          </button>
        </div>
      </div>

      {/* Tie Handling & Ranking Transparency Disclosure */}
      {hasScoreTies && (
        <div role="note" className="rounded-xl border border-sky-200 bg-sky-50/80 p-4 text-xs leading-5 text-sky-900">
          <span className="font-semibold text-sky-950">Tie-Breaking Disclosure:</span> The ranking has no secondary scientific tie-breaker. The backend sort preserves incoming candidate order when adjusted scores are equal; that order does not imply superiority.
        </div>
      )}

      {/* Visualization 4: Candidate Screening Metric Comparison Chart */}
      <CandidateScreeningComparisonChart candidates={candidates} />

      {/* View Tab 1: Cards */}
      {activeTab === "cards" && (
        <div className="space-y-6">
          {/* Target Macromolecule PDB Invitation Banner */}
          <div className="rounded-xl border border-teal-200/80 bg-teal-50/50 p-4 shadow-xs flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-teal-600 text-white shrink-0 shadow-xs">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <circle cx="12" cy="12" r="3" strokeWidth="1.75" />
                  <ellipse cx="12" cy="12" rx="9" ry="4" transform="rotate(30 12 12)" strokeWidth="1.75" />
                  <ellipse cx="12" cy="12" rx="9" ry="4" transform="rotate(-30 12 12)" strokeWidth="1.75" />
                </svg>
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-teal-950">
                    Target Macromolecule: {targetProteinName}
                  </span>
                  <span className="rounded bg-teal-200/70 text-teal-900 font-mono text-[10px] font-bold px-1.5 py-0.2">
                    PDB: {targetPdbId}
                  </span>
                </div>
                <p className="text-[11px] text-teal-800 mt-0.5">
                  Interactive 3D protein cartoon ribbon, crystallographic provenance, and co-crystallized ligand pocket inspection.
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={() => setActiveTab("protein-pdb")}
              className="inline-flex items-center gap-1.5 rounded-lg bg-teal-600 px-3 py-1.5 text-xs font-bold text-white shadow-xs hover:bg-teal-700 transition shrink-0"
            >
              <span>Launch 3D Protein Viewer</span>
              <span aria-hidden="true">&rarr;</span>
            </button>
          </div>

          {candidates.length === 0 ? (
            <div className="rounded-xl border border-slate-200 bg-white p-8 text-center text-sm text-slate-500 shadow-sm">
              <p className="font-semibold text-slate-800">No primary candidates generated yet.</p>
              <p className="mt-1 text-xs">Upload a target structure and run discovery to generate novel and reference molecules.</p>
            </div>
          ) : (
            <div className="space-y-6">
              {featured && (
                <div>
                  <div className="flex items-center gap-2 mb-3">
                    <span className="rounded bg-teal-100 text-teal-800 text-xs font-bold uppercase tracking-wider px-2 py-0.5">
                      Prioritized Top Candidate
                    </span>
                    <span className="text-xs text-slate-500">Highest composite discovery score</span>
                  </div>
                  <CandidateCard candidate={featured} featured onSelectForRisk={onNavigateToRisk} />
                </div>
              )}

              {others.length > 0 && (
                <div>
                  <h3 className="text-sm font-bold uppercase tracking-wider text-slate-600 mb-3">
                    Other Candidate Derivatives ({others.length})
                  </h3>
                  <div className="grid gap-4 md:grid-cols-2">
                    {others.map((c) => (
                      <CandidateCard key={c.id} candidate={c} onSelectForRisk={onNavigateToRisk} />
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Demonstration References (Separated strictly from primary ranking) */}
          {demonstrationCandidates.length > 0 && (
            <div className="mt-8 pt-6 border-t border-slate-200">
              <div className="mb-3">
                <span className="rounded bg-slate-200 text-slate-700 text-xs font-bold uppercase tracking-wider px-2 py-0.5">
                  Demonstration References (Excluded from Ranking)
                </span>
                <p className="mt-1 text-xs text-slate-500">
                  Control compounds and mock references included solely for pipeline calibration; not proposed leads.
                </p>
              </div>
              <div className="grid gap-4 md:grid-cols-2">
                {demonstrationCandidates.map((c) => (
                  <CandidateCard key={c.id} candidate={c} onSelectForRisk={onNavigateToRisk} />
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* View Tab 2: Dedicated Interactive Protein PDB Viewer */}
      {activeTab === "protein-pdb" && (
        <div className="rounded-xl border border-slate-200/90 bg-white p-6 shadow-sm">
          <ProteinPDBViewer defaultPdbId={targetPdbId} />
        </div>
      )}

      {/* View Tab 3: 3D Conformations */}
      {activeTab === "3d" && (
        <div className="rounded-xl border border-slate-200/90 bg-white p-6 shadow-sm">
          <div className="mb-4">
            <h3 className="text-base font-semibold text-slate-900">
              Interactive 3D Conformational Viewer (3Dmol.js)
            </h3>
            <p className="text-xs text-slate-500">
              Generated 3D molecular conformations with solvent-accessible surface rendering and electrostatic coloring.
            </p>
          </div>
          <Molecule3DExplorer candidates={[...candidates, ...demonstrationCandidates]} />
        </div>
      )}

      {/* View Tab 4: Strategy Simulator */}
      {activeTab === "simulator" && (
        <div className="rounded-xl border border-slate-200/90 bg-white p-6 shadow-sm">
          <DiscoveryStrategySimulator candidates={candidates} />
        </div>
      )}
    </div>
  );
}
