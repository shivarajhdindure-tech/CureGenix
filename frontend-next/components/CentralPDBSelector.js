"use client";

import { useRef, useState } from "react";

function fmtBytes(bytes) {
  if (!bytes && bytes !== 0) return "";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function CentralPDBSelector({
  curatedStructures = [],
  collectionMeta = null,
  activePdbId = "1M17",
  activeStructure = null,
  onSelectCurated = null,
  onUploadCustom = null,
  loading = false,
}) {
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef(null);

  function handleDrop(e) {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer?.files?.[0];
    if (file && onUploadCustom) {
      onUploadCustom(file);
    }
  }

  function handleFileChange(e) {
    const file = e.target.files?.[0];
    if (file && onUploadCustom) {
      onUploadCustom(file);
      e.target.value = "";
    }
  }

  const isCustomActive = activeStructure?.structureSource === "custom";

  return (
    <div className="space-y-6" id="central-pdb-selector">
      {/* EGFR Collection Focus Header */}
      <div className="rounded-xl border border-teal-200/90 bg-gradient-to-r from-teal-50/90 via-slate-50/70 to-teal-50/50 p-4 sm:p-5 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <span className="rounded-md bg-teal-600 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-white">
                Curated Collection
              </span>
              <span className="text-xs font-semibold text-teal-950">
                {collectionMeta?.collection_name || "CureGenix EGFR-Focused Curated Structure Collection"}
              </span>
            </div>
            <p className="mt-1.5 text-xs leading-relaxed text-slate-600 max-w-4xl">
              All four curated structures represent the human <strong>Epidermal Growth Factor Receptor (EGFR / UniProt P00533)</strong> kinase domain in different conformational states, complexes, or mutational profiles (wild-type, active, inactive, and drug-resistant T790M/V948R). They do not represent four independent protein targets.
            </p>
          </div>
          {loading && (
            <div className="flex items-center gap-2 text-xs font-semibold text-teal-800 bg-white/80 px-3 py-1.5 rounded-lg border border-teal-200 shrink-0">
              <span className="inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-teal-600 border-t-transparent" />
              <span>Updating context…</span>
            </div>
          )}
        </div>
      </div>

      {/* 4-PDB Curated Selection Cards Grid */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-bold uppercase tracking-wider text-slate-700">
            A. Select One Curated EGFR Structure
          </h3>
          <span className="text-xs text-slate-500 font-mono">
            4 Verified PDBs Available
          </span>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {curatedStructures.map((struct) => {
            const isSelected = !isCustomActive && activePdbId === struct.pdb_id;
            const chains = struct.protein_chains || [];
            const ligands = struct.ligand_component_ids || [];
            const mutations = struct.verified_mutations || [];

            return (
              <div
                key={struct.pdb_id}
                role="button"
                tabIndex={0}
                onClick={() => !loading && onSelectCurated && onSelectCurated(struct.pdb_id)}
                onKeyDown={(e) => {
                  if ((e.key === "Enter" || e.key === " ") && !loading && onSelectCurated) {
                    e.preventDefault();
                    onSelectCurated(struct.pdb_id);
                  }
                }}
                className={`flex flex-col justify-between rounded-xl border p-4 text-left transition cursor-pointer relative shadow-xs ${
                  isSelected
                    ? "border-teal-500 bg-teal-50/70 ring-2 ring-teal-500/30"
                    : "border-slate-200 bg-white hover:border-teal-300 hover:bg-slate-50/70"
                }`}
              >
                {/* Active check pill */}
                {isSelected && (
                  <span className="absolute -top-2.5 right-3 rounded-full bg-teal-600 text-white px-2 py-0.5 text-[10px] font-bold shadow-xs">
                    ✓ Active Context
                  </span>
                )}

                <div>
                  {/* PDB ID & Target Accession */}
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xl font-bold tracking-tight text-slate-900">
                      {struct.pdb_id}
                    </span>
                    <span className="rounded bg-slate-100 text-slate-700 font-mono text-[11px] font-semibold px-2 py-0.5 border border-slate-200">
                      P00533
                    </span>
                  </div>

                  {/* Structure Title / Description from Registry */}
                  <p className="mt-2 text-xs font-semibold text-slate-800 line-clamp-2" title={struct.verified_structure_description}>
                    {struct.verified_structure_description}
                  </p>

                  {/* Metadata Chips */}
                  <div className="mt-3 flex flex-wrap gap-1.5 text-[11px]">
                    <span className="rounded bg-slate-100 px-2 py-0.5 font-medium text-slate-700 border border-slate-200/80">
                      Chains: <strong className="font-mono">{chains.join(", ")}</strong>
                    </span>
                    <span className="rounded bg-indigo-50 px-2 py-0.5 font-medium text-indigo-800 border border-indigo-200/80">
                      Ligand: <strong className="font-mono">{ligands.join(", ") || "None"}</strong>
                    </span>
                    {mutations.length > 0 && (
                      <span className="rounded bg-amber-50 px-2 py-0.5 font-semibold text-amber-900 border border-amber-200/80">
                        Mutations: {mutations.map((m) => m.variant).join(", ")}
                      </span>
                    )}
                  </div>
                </div>

                {/* Selection Action Button */}
                <div className="mt-4 pt-3 border-t border-slate-200/70">
                  <button
                    type="button"
                    disabled={loading || isSelected}
                    className={`w-full rounded-lg px-3 py-1.5 text-xs font-bold transition ${
                      isSelected
                        ? "bg-teal-600 text-white cursor-default"
                        : "bg-slate-100 text-slate-700 hover:bg-teal-600 hover:text-white"
                    }`}
                  >
                    {isSelected ? "Selected Structure" : "Select Structure"}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* B. Custom PDB Upload Option */}
      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-700">
              B. Or Upload a Custom PDB Structure
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Analyze non-curated macromolecular structures (e.g. 1CRN, AlphaFold models). Automatically initiates chain discovery.
            </p>
          </div>
          {isCustomActive && (
            <span className="rounded-full bg-cyan-100 text-cyan-900 px-3 py-1 text-xs font-bold border border-cyan-300">
              ✓ Custom Upload Active
            </span>
          )}
        </div>

        {/* Drag & Drop Zone */}
        <div
          role="button"
          tabIndex={0}
          onClick={() => fileInputRef.current?.click()}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault();
              fileInputRef.current?.click();
            }
          }}
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          className={`flex flex-col items-center justify-center rounded-xl border-2 border-dashed p-6 text-center cursor-pointer transition ${
            dragOver
              ? "border-teal-500 bg-teal-50/50"
              : isCustomActive
                ? "border-cyan-300 bg-cyan-50/20"
                : "border-slate-300 bg-slate-50/50 hover:border-teal-400 hover:bg-slate-50"
          }`}
        >
          <svg className="w-8 h-8 text-slate-400 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
          <p className="text-xs font-semibold text-slate-800">
            Click to browse or drag and drop a <code>.pdb</code> coordinate file
          </p>
          <p className="text-[11px] text-slate-500 mt-1">
            Plain-text ASCII PDB format up to 20 MB. Fixed-column ATOM records required.
          </p>
        </div>

        <input
          ref={fileInputRef}
          type="file"
          accept=".pdb"
          className="hidden"
          onChange={handleFileChange}
        />

        {/* Custom Upload Details if active */}
        {isCustomActive && activeStructure && (
          <div className="mt-4 rounded-lg border border-cyan-200 bg-cyan-50/50 p-3.5 text-xs flex flex-wrap items-center justify-between gap-3">
            <div>
              <span className="font-bold text-cyan-950">Active Custom File: </span>
              <span className="font-semibold text-slate-900">{activeStructure.originalFilename || activeStructure.pdbId}</span>
              <span className="text-slate-500 ml-2">({activeStructure.availableChains?.length || 0} chain(s) identified)</span>
            </div>
            <div className="text-[11px] text-slate-600 font-mono">
              SHA-256: {activeStructure.sha256 ? `${activeStructure.sha256.slice(0, 16)}…` : "—"}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
