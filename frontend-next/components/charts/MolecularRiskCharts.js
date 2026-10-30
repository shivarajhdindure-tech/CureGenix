"use client";

import { useState } from "react";

// ============================================================================
// MODULE A: DEVELOPABILITY & ADMET VISUALIZATIONS
// ============================================================================

/**
 * 1. ADMET Radar Chart
 * Plots 6 key physicochemical/ADMET dimensions:
 * Lipophilicity, Molecular Size, Polarity, Solubility, Flexibility, Saturation.
 */
export function AdmetRadarChart({ radarMetrics }) {
  const metrics = radarMetrics || {
    lipophilicity: 6.2,
    size: 5.8,
    polarity: 5.5,
    solubility: 6.0,
    flexibility: 4.5,
    saturation: 3.8,
  };

  const keys = [
    { key: "lipophilicity", label: "Lipophilicity (cLogP)" },
    { key: "size", label: "Size (MW)" },
    { key: "polarity", label: "Polarity (TPSA)" },
    { key: "solubility", label: "Solubility (ESOL)" },
    { key: "flexibility", label: "Flexibility (RotB)" },
    { key: "saturation", label: "Saturation (Fsp3)" },
  ];

  const size = 300;
  const center = size / 2;
  const radius = 100;
  const angleStep = (2 * Math.PI) / keys.length;

  // Compute vertices for candidate polygon
  const candidatePoints = keys.map((item, i) => {
    const angle = i * angleStep - Math.PI / 2;
    const value = Math.max(0, Math.min(10, metrics[item.key] || 5)) / 10;
    const r = radius * value;
    return `${center + r * Math.cos(angle)},${center + r * Math.sin(angle)}`;
  }).join(" ");

  // Reference "ideal drug-like" boundary (normalized 0.5 to 0.8)
  const idealPoints = keys.map((_, i) => {
    const angle = i * angleStep - Math.PI / 2;
    const r = radius * 0.65;
    return `${center + r * Math.cos(angle)},${center + r * Math.sin(angle)}`;
  }).join(" ");

  return (
    <div className="flex flex-col items-center">
      <svg width={size} height={size} className="overflow-visible">
        {/* Background web rings */}
        {[0.25, 0.5, 0.75, 1.0].map((level) => {
          const points = keys.map((_, i) => {
            const angle = i * angleStep - Math.PI / 2;
            const r = radius * level;
            return `${center + r * Math.cos(angle)},${center + r * Math.sin(angle)}`;
          }).join(" ");
          return (
            <polygon
              key={level}
              points={points}
              fill="none"
              stroke="#e2e8f0"
              strokeDasharray={level === 1.0 ? "none" : "2,2"}
              strokeWidth="1"
            />
          );
        })}

        {/* Spokes */}
        {keys.map((item, i) => {
          const angle = i * angleStep - Math.PI / 2;
          const x = center + radius * Math.cos(angle);
          const y = center + radius * Math.sin(angle);
          const labelX = center + (radius + 24) * Math.cos(angle);
          const labelY = center + (radius + 16) * Math.sin(angle);
          return (
            <g key={item.key}>
              <line x1={center} y1={center} x2={x} y2={y} stroke="#cbd5e1" strokeWidth="1" />
              <text
                x={labelX}
                y={labelY}
                textAnchor="middle"
                dominantBaseline="central"
                className="text-[10px] font-semibold fill-slate-600"
              >
                {item.label.split(" ")[0]}
              </text>
            </g>
          );
        })}

        {/* Ideal range polygon */}
        <polygon
          points={idealPoints}
          fill="rgba(14, 165, 233, 0.08)"
          stroke="#0ea5e9"
          strokeWidth="1.5"
          strokeDasharray="4,3"
        />

        {/* Candidate polygon */}
        <polygon
          points={candidatePoints}
          fill="rgba(20, 184, 166, 0.25)"
          stroke="#0d9488"
          strokeWidth="2.5"
        />

        {/* Candidate vertex dots */}
        {keys.map((item, i) => {
          const angle = i * angleStep - Math.PI / 2;
          const value = Math.max(0, Math.min(10, metrics[item.key] || 5)) / 10;
          const r = radius * value;
          const x = center + r * Math.cos(angle);
          const y = center + r * Math.sin(angle);
          return <circle key={item.key} cx={x} cy={y} r="3.5" fill="#0d9488" stroke="#ffffff" strokeWidth="1.5" />;
        })}
      </svg>

      <div className="flex items-center gap-4 mt-2 text-xs">
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-sm bg-teal-600" />
          <span className="text-slate-700 font-medium">Candidate Profile</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-0.5 border-t-2 border-dashed border-sky-500" />
          <span className="text-slate-500 font-medium">Optimal Drug-Like Space</span>
        </div>
      </div>
    </div>
  );
}

/**
 * 2. Physicochemical Property Dashboard
 */
export function PhysicochemicalPropertyDashboard({ descriptors, lipinski }) {
  const d = descriptors || {};
  const cards = [
    { label: "Molecular Weight", value: `${d.molecular_weight || "—"} Da`, sub: "Rule: ≤ 500 Da", pass: (d.molecular_weight || 0) <= 500 },
    { label: "Lipophilicity (cLogP)", value: d.logp ?? "—", sub: "Rule: ≤ 5.0", pass: (d.logp ?? 0) <= 5.0 },
    { label: "Polar Surface (TPSA)", value: `${d.tpsa ?? "—"} Å²`, sub: "Veber: ≤ 140 Å²", pass: (d.tpsa ?? 0) <= 140 },
    { label: "H-Bond Donors", value: d.hbd ?? "—", sub: "Rule: ≤ 5", pass: (d.hbd ?? 0) <= 5 },
    { label: "H-Bond Acceptors", value: d.hba ?? "—", sub: "Rule: ≤ 10", pass: (d.hba ?? 0) <= 10 },
    { label: "Rotatable Bonds", value: d.rotatable_bonds ?? "—", sub: "Veber: ≤ 10", pass: (d.rotatable_bonds ?? 0) <= 10 },
    { label: "Fraction Csp3", value: d.fraction_csp3 ?? "—", sub: "Sat: ≥ 0.25 target", pass: (d.fraction_csp3 ?? 0) >= 0.25 },
    { label: "Drug-likeness (QED)", value: d.qed ?? "—", sub: "Bickerton: 0 to 1", pass: (d.qed ?? 0) >= 0.5 },
  ];

  return (
    <div className="grid gap-3 grid-cols-2 sm:grid-cols-4">
      {cards.map((c) => (
        <div key={c.label} className="rounded-lg border border-slate-200 bg-slate-50/70 p-3">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">{c.label}</span>
            <span className={`h-2 w-2 rounded-full ${c.pass ? "bg-emerald-500" : "bg-amber-500"}`} />
          </div>
          <p className="font-mono text-base font-bold text-slate-900 mt-1">{c.value}</p>
          <p className="text-[10px] text-slate-500 mt-0.5">{c.sub}</p>
        </div>
      ))}
    </div>
  );
}

/**
 * 3. Solubility and Permeability (Boiled-Egg / ESOL) Visualization
 */
export function SolubilityPermeabilityVisualization({ esol, boiledEgg }) {
  const sol = esol || { logs: -4.2, solubility_class: "Moderate", estimated_aqueous_solubility_mg_ml: 0.025 };
  const egg = boiledEgg || { region: "GI Permeant", gi_absorption: "High (GI only)", bbb_permeant: false };

  return (
    <div className="grid gap-4 sm:grid-cols-2">
      {/* ESOL Solubility Box */}
      <div className="rounded-lg border border-slate-200 bg-white p-4">
        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-600 mb-2">
          Delaney ESOL Aqueous Solubility
        </h4>
        <div className="flex items-baseline gap-2">
          <span className="font-mono text-xl font-bold text-teal-700">{sol.logs}</span>
          <span className="text-xs text-slate-500">log(mol/L)</span>
          <span className="ml-auto rounded bg-teal-50 border border-teal-200 px-2 py-0.5 text-xs font-semibold text-teal-800">
            {sol.solubility_class}
          </span>
        </div>
        <p className="text-xs text-slate-600 mt-2">
          Est. Conc: <span className="font-mono font-semibold">{sol.estimated_aqueous_solubility_mg_ml} mg/mL</span>
        </p>

        {/* Solubility scale bar */}
        <div className="mt-3">
          <div className="flex justify-between text-[10px] text-slate-400 mb-1">
            <span>Insoluble (&lt; -6)</span>
            <span>Moderate (-4 to -2)</span>
            <span>Soluble (&gt; 0)</span>
          </div>
          <div className="h-2 w-full rounded-full bg-gradient-to-r from-rose-400 via-amber-300 to-emerald-400 relative">
            {/* Pointer */}
            <div
              className="absolute top-[-3px] w-3 h-3 rounded-full bg-slate-900 border-2 border-white shadow -ml-1.5"
              style={{
                left: `${Math.max(5, Math.min(95, ((sol.logs + 8) / 10) * 100))}%`,
              }}
            />
          </div>
        </div>
      </div>

      {/* Boiled Egg Permeability Box */}
      <div className="rounded-lg border border-slate-200 bg-white p-4">
        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-600 mb-2">
          Boiled-Egg Absorption &amp; BBB Model
        </h4>
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-slate-700">GI Tract Permeation:</span>
          <span className="rounded bg-emerald-50 border border-emerald-200 px-2 py-0.5 text-xs font-semibold text-emerald-800">
            {egg.gi_absorption}
          </span>
        </div>
        <div className="flex items-center justify-between mt-2">
          <span className="text-xs font-medium text-slate-700">Blood-Brain Barrier (BBB):</span>
          <span className={`rounded border px-2 py-0.5 text-xs font-semibold ${
            egg.bbb_permeant
              ? "bg-purple-50 text-purple-800 border-purple-200"
              : "bg-slate-100 text-slate-700 border-slate-200"
          }`}>
            {egg.bbb_permeant ? "BBB Permeant (High)" : "Non-Permeant (Peripheral)"}
          </span>
        </div>
        <p className="text-[11px] text-slate-500 mt-3 leading-relaxed">
          {egg.region}. Predictive boundary model based on WLOGP and TPSA descriptors.
        </p>
      </div>
    </div>
  );
}

/**
 * 4. CYP Interaction Matrix
 */
export function CypInteractionMatrix({ cypMatrix }) {
  const items = cypMatrix || [];

  return (
    <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
      <table className="w-full text-left text-xs">
        <thead className="bg-slate-50 border-b border-slate-200 text-slate-700 font-semibold">
          <tr>
            <th className="py-2.5 px-3">Cytochrome Isozyme</th>
            <th className="py-2.5 px-3">Structural Liability Status</th>
            <th className="py-2.5 px-3">Motif Name</th>
            <th className="py-2.5 px-3">Description</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {items.map((c) => {
            const hasAlert = c.status.includes("Alert");
            return (
              <tr key={c.isozyme} className="hover:bg-slate-50/50">
                <td className="py-2 px-3 font-bold text-slate-900">{c.isozyme}</td>
                <td className="py-2 px-3">
                  <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 font-semibold text-[10px] border ${
                    hasAlert
                      ? "bg-amber-50 text-amber-800 border-amber-200"
                      : "bg-emerald-50 text-emerald-800 border-emerald-200"
                  }`}>
                    <span className={`h-1.5 w-1.5 rounded-full ${hasAlert ? "bg-amber-500" : "bg-emerald-500"}`} />
                    {c.status}
                  </span>
                </td>
                <td className="py-2 px-3 text-slate-700 font-medium">{c.motif}</td>
                <td className="py-2 px-3 text-slate-500 text-[11px]">{c.description}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

/**
 * 5. Structural Alert & Toxicity Summary Map
 */
export function StructuralAlertMap({ structuralAlerts, toxicityAlerts }) {
  const sa = structuralAlerts || [];
  const ta = toxicityAlerts || [];

  return (
    <div className="grid gap-4 sm:grid-cols-2">
      {/* PAINS / BRENK / NIH Structural Alerts */}
      <div className="rounded-lg border border-slate-200 bg-slate-50/70 p-4">
        <div className="flex items-center justify-between mb-2">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-600">
            RDKit FilterCatalog Alerts (PAINS / Brenk / NIH)
          </h4>
          <span className="rounded bg-slate-200 px-1.5 py-0.2 text-[10px] font-bold text-slate-700">
            {sa.length} Detected
          </span>
        </div>
        {sa.length === 0 ? (
          <p className="text-xs text-emerald-700 font-medium bg-emerald-50 border border-emerald-200 rounded p-2.5">
            ✓ No PAINS, Brenk, or NIH reactive pan-assay interference substructures identified.
          </p>
        ) : (
          <ul className="space-y-1.5">
            {sa.map((alert, idx) => (
              <li key={idx} className="rounded bg-amber-50 border border-amber-200 p-2 text-xs text-amber-900 font-mono">
                ⚠ {alert}
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Reactive Toxicity Alerts */}
      <div className="rounded-lg border border-slate-200 bg-slate-50/70 p-4">
        <div className="flex items-center justify-between mb-2">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-600">
            Reactive Chemical Toxicophores
          </h4>
          <span className="rounded bg-slate-200 px-1.5 py-0.2 text-[10px] font-bold text-slate-700">
            {ta.length} Detected
          </span>
        </div>
        {ta.length === 0 ? (
          <p className="text-xs text-emerald-700 font-medium bg-emerald-50 border border-emerald-200 rounded p-2.5">
            ✓ No high-risk electrophilic or mutational alerts (nitro, azo, acyl chloride) detected.
          </p>
        ) : (
          <ul className="space-y-1.5">
            {ta.map((alert, idx) => (
              <li key={idx} className="rounded bg-rose-50 border border-rose-200 p-2 text-xs text-rose-900 font-mono">
                ✖ {alert}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}


// ============================================================================
// MODULE B: BINDING STABILITY & PROTEIN-LIGAND VISUALIZATIONS
// ============================================================================

/**
 * Binding Site Interaction Diagram & Simulation Trajectory Status
 */
export function BindingSiteInteractionDiagram({ pocketContacts, mdStatus }) {
  const contacts = pocketContacts || [];
  const status = mdStatus || {};

  return (
    <div className="space-y-4">
      {/* Simulation Engine Status Disclosure */}
      <div className="rounded-xl border border-amber-200 bg-amber-50/80 p-4 text-xs text-amber-950">
        <div className="flex items-center gap-2 font-bold text-amber-900">
          <svg className="w-4 h-4 text-amber-700" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Simulation Trajectory Execution State: {status.execution_status || "Prepared Only"}
        </div>
        <p className="mt-1 leading-relaxed text-slate-700">
          {status.message || "GROMACS molecular dynamics is not configured in this host environment. Conformer geometry was generated via RDKit ETKDGv3 + MMFF94 force field. Dynamic RMSD/RMSF trajectories have not been manufactured or claimed."}
        </p>
      </div>

      {/* Static Cleft Residue Alignment */}
      <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-50 border-b border-slate-200 text-slate-700 font-semibold">
            <tr>
              <th className="py-2.5 px-3">EGFR Pocket Residue</th>
              <th className="py-2.5 px-3">Structural Cleft Region</th>
              <th className="py-2.5 px-3">Predicted Interaction</th>
              <th className="py-2.5 px-3">Pharmacophore Match</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {contacts.map((c) => (
              <tr key={c.residue} className="hover:bg-slate-50/50">
                <td className="py-2 px-3 font-mono font-bold text-teal-800">{c.residue}</td>
                <td className="py-2 px-3 text-slate-600">{c.region}</td>
                <td className="py-2 px-3 text-slate-900 font-medium">{c.predicted_interaction}</td>
                <td className="py-2 px-3 text-slate-500 text-[11px]">{c.occupancy_proxy}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}


// ============================================================================
// MODULE C: OFF-TARGET & SELECTIVITY VISUALIZATIONS
// ============================================================================

/**
 * Target vs Off-Target Comparison Table & Similarity Network
 */
export function TargetOffTargetPanel({ panelEvaluations }) {
  const panel = panelEvaluations || [];

  return (
    <div className="space-y-4">
      {/* Panel Table */}
      <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-50 border-b border-slate-200 text-slate-700 font-semibold">
            <tr>
              <th className="py-2.5 px-3">Target Symbol</th>
              <th className="py-2.5 px-3">UniProt</th>
              <th className="py-2.5 px-3">Relationship</th>
              <th className="py-2.5 px-3">ATP Pocket Similarity</th>
              <th className="py-2.5 px-3">Selectivity Risk</th>
              <th className="py-2.5 px-3">Homologous Cys</th>
              <th className="py-2.5 px-3">Structural Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {panel.map((k) => {
              const isHigh = k.selectivity_risk.includes("Elevated");
              const pct = Math.round(k.pocket_similarity_score * 100);
              return (
                <tr key={k.symbol} className="hover:bg-slate-50/50">
                  <td className="py-2 px-3 font-bold text-slate-900">{k.symbol}</td>
                  <td className="py-2 px-3 font-mono text-slate-500">{k.uniprot_id}</td>
                  <td className="py-2 px-3 text-slate-600">{k.relationship}</td>
                  <td className="py-2 px-3">
                    <div className="flex items-center gap-2">
                      <div className="w-16 h-2 rounded-full bg-slate-200 overflow-hidden">
                        <div
                          className={`h-full ${isHigh ? "bg-rose-500" : "bg-teal-600"}`}
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                      <span className="font-mono text-slate-700">{pct}%</span>
                    </div>
                  </td>
                  <td className="py-2 px-3">
                    <span className={`inline-flex rounded-full px-2 py-0.5 text-[10px] font-semibold border ${
                      isHigh
                        ? "bg-rose-50 text-rose-800 border-rose-200"
                        : "bg-slate-100 text-slate-700 border-slate-200"
                    }`}>
                      {k.selectivity_risk}
                    </span>
                  </td>
                  <td className="py-2 px-3 font-mono text-[11px] text-slate-600">{k.covalent_anchor}</td>
                  <td className="py-2 px-3 text-[11px] text-slate-500">{k.structure_status}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Disclosures note */}
      <p className="text-[11px] text-slate-500 italic">
        * High pocket sequence similarity reflects shared architectural features of the kinase fold and does not confirm measured off-target potency. Distinguish computational predictions from experimental KINOMEscan profiles.
      </p>
    </div>
  );
}


// ============================================================================
// MODULE D: MUTATION & ROBUSTNESS VISUALIZATIONS
// ============================================================================

/**
 * Mutation Location & Robustness Table
 */
export function MutationRobustnessPanel({ variantAssessments }) {
  const variants = variantAssessments || [];

  return (
    <div className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-2">
        {variants.map((v) => {
          const isHighVuln = v.resistance_risk.includes("High") || v.resistance_risk.includes("Loss");
          return (
            <div key={v.variant} className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                <span className="font-mono font-bold text-base text-slate-900">{v.variant}</span>
                <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold border ${
                  isHighVuln
                    ? "bg-rose-50 text-rose-800 border-rose-200"
                    : "bg-emerald-50 text-emerald-800 border-emerald-200"
                }`}>
                  {v.resistance_risk}
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-2 font-medium">{v.location} · {v.clinical_prevalence}</p>
              <p className="text-xs text-slate-700 mt-2 leading-relaxed">{v.predicted_impact}</p>

              <div className="mt-3 grid grid-cols-2 gap-2 text-[11px] bg-slate-50 rounded p-2 border border-slate-150">
                <div>
                  <span className="text-slate-400">Volume Shift:</span>{" "}
                  <span className="font-mono text-slate-800 font-semibold">{v.volume_change}</span>
                </div>
                <div>
                  <span className="text-slate-400">Crystal Ref:</span>{" "}
                  <span className="font-mono text-teal-700 font-semibold">{v.validated_pdb_crystal}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}


// ============================================================================
// MODULE E: SYNTHETIC FEASIBILITY VISUALIZATIONS
// ============================================================================

/**
 * Synthetic Accessibility & Retrosynthesis Disconnections
 */
export function SyntheticFeasibilityPanel({ feasibilityDetails }) {
  const d = feasibilityDetails || {};
  const score = d.synthetic_accessibility_score || 3.2;
  const disconnections = d.retrosynthetic_disconnections || [];
  const fg = d.functional_groups_identified || [];
  const liabilities = d.chemical_liabilities || [];

  return (
    <div className="space-y-4">
      {/* Synthetic Accessibility Gauge */}
      <div className="rounded-xl border border-slate-200 bg-white p-5">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-slate-100 pb-3">
          <div>
            <h4 className="text-sm font-bold text-slate-900">Synthetic Accessibility Index (SAscore)</h4>
            <p className="text-xs text-slate-500">Heuristic scale from 1 (easy synthesis) to 10 (very difficult synthesis)</p>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="font-mono text-2xl font-extrabold text-teal-700">{score}</span>
            <span className="text-xs text-slate-500">/ 10</span>
            <span className="rounded bg-teal-50 border border-teal-200 px-2.5 py-0.5 text-xs font-semibold text-teal-800">
              {d.synthetic_accessibility_class || "High Accessibility"}
            </span>
          </div>
        </div>

        {/* Complexity stats */}
        <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
          <div className="bg-slate-50 p-2.5 rounded border border-slate-200">
            <span className="text-slate-500 text-[10px] font-bold uppercase">Bertz Complexity</span>
            <p className="font-mono text-base font-bold text-slate-900 mt-0.5">{d.bertz_complexity_index || "—"}</p>
          </div>
          <div className="bg-slate-50 p-2.5 rounded border border-slate-200">
            <span className="text-slate-500 text-[10px] font-bold uppercase">Chiral Centers</span>
            <p className="font-mono text-base font-bold text-slate-900 mt-0.5">{d.stereochemical_complexity?.chiral_center_count ?? 0}</p>
          </div>
          <div className="bg-slate-50 p-2.5 rounded border border-slate-200">
            <span className="text-slate-500 text-[10px] font-bold uppercase">Functional Groups</span>
            <p className="font-mono text-base font-bold text-slate-900 mt-0.5">{fg.length}</p>
          </div>
          <div className="bg-slate-50 p-2.5 rounded border border-slate-200">
            <span className="text-slate-500 text-[10px] font-bold uppercase">Disconnection Steps</span>
            <p className="font-mono text-base font-bold text-slate-900 mt-0.5">{disconnections.length}</p>
          </div>
        </div>
      </div>

      {/* Retrosynthetic Reaction Disconnections */}
      <div className="rounded-xl border border-slate-200 bg-white p-5">
        <h4 className="text-sm font-bold text-slate-900 mb-2">Rule-Based Retrosynthetic Pathways</h4>
        <p className="text-xs text-slate-500 mb-4">
          Identified synthetic disconnections using canonical organic transformation templates:
        </p>

        <div className="space-y-3">
          {disconnections.map((r, i) => (
            <div key={i} className="rounded-lg border border-slate-200 bg-slate-50/70 p-3 text-xs">
              <div className="flex items-center justify-between">
                <span className="font-bold text-teal-800">{r.name}</span>
                <span className="rounded bg-teal-100 text-teal-800 px-2 py-0.5 text-[10px] font-semibold">
                  {r.feasibility}
                </span>
              </div>
              <p className="text-slate-600 mt-1">{r.description}</p>
              <p className="text-slate-500 text-[11px] mt-1 font-mono">Reagents: {r.suggested_reagents}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Chemical Liabilities */}
      {liabilities.length > 0 && (
        <div className="rounded-xl border border-amber-200 bg-amber-50/80 p-4 text-xs text-amber-950">
          <h4 className="font-bold text-amber-900 mb-1">Potential Chemical Liabilities</h4>
          <ul className="list-disc pl-4 space-y-1">
            {liabilities.map((l, idx) => (
              <li key={idx}>{l}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
