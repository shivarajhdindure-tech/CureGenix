"use client";

import { useEffect, useRef, useState, useCallback } from "react";

/**
 * Common EGFR & benchmark reference PDB IDs for rapid judge & researcher inspection.
 */
const REFERENCE_PRESETS = [
  { id: "1M17", label: "1M17", description: "EGFR tyrosine kinase domain with erlotinib; annotated component AQ4." },
  { id: "2ITX", label: "2ITX", description: "EGFR kinase domain in complex with AMP-PNP; annotated component ANP." },
  { id: "4G5J", label: "4G5J", description: "EGFR kinase in complex with BIBW2992; Afatinib-related component records 0WM and 0WN." },
  { id: "7A2A", label: "7A2A", description: "EGFR T790M/V948R; the entry title lists spebrutinib and EAI001, with components 57N and 7G9. Component-to-compound roles are not assigned here." },
];

/**
 * Water residue names omitted from the heuristic non-water HETATM inventory.
 */
const SOLVENT_RESIDUES = new Set([
  "HOH", "WAT", "DOD", "H3O", "H2O", "OH2",
]);

/**
 * Parse essential metadata directly from raw PDB text lines as reliable fallback.
 */
function parsePdbHeader(pdbText) {
  const lines = pdbText.split("\n");
  let title = "";
  let classification = "";
  let depositDate = "";
  let resolution = null;
  let method = "";
  const chains = new Set();
  const ligandsMap = new Map();
  let atomCount = 0;
  let hetatmCount = 0;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (line.startsWith("HEADER")) {
      classification = line.substring(10, 50).trim();
      depositDate = line.substring(50, 59).trim();
    } else if (line.startsWith("TITLE")) {
      const part = line.substring(10, 70).trim();
      if (part) title += (title ? " " : "") + part;
    } else if (line.startsWith("EXPDTA")) {
      const part = line.substring(10, 70).trim();
      if (part) method += (method ? " " : "") + part;
    } else if (line.startsWith("REMARK   2") && line.includes("ANGSTROMS")) {
      const match = line.match(/([0-9]+\.[0-9]+)\s+ANGSTROMS/);
      if (match && !resolution) resolution = `${match[1]} Å`;
    } else if (line.startsWith("ATOM  ")) {
      atomCount++;
      const chain = line.substring(21, 22).trim();
      if (chain) chains.add(chain);
    } else if (line.startsWith("HETATM")) {
      hetatmCount++;
      const resn = line.substring(17, 20).trim();
      const chain = line.substring(21, 22).trim();
      const resSeq = line.substring(22, 26).trim();

      if (resn && !SOLVENT_RESIDUES.has(resn)) {
        const key = `${resn}-${chain}-${resSeq}`;
        if (!ligandsMap.has(key)) {
          ligandsMap.set(key, { resn, chain, resSeq, count: 1 });
        } else {
          ligandsMap.get(key).count++;
        }
      }
    }
  }

  return {
    title: title || "Macromolecular Protein Structure",
    classification: classification || "Protein Target",
    depositDate: depositDate || "—",
    resolution: resolution || "Not reported",
    method: method || "X-RAY DIFFRACTION",
    chains: Array.from(chains).sort(),
    ligands: Array.from(ligandsMap.values()),
    atomCount,
    hetatmCount,
  };
}

export default function ProteinPDBViewer({
  defaultPdbId = "1M17",
  onStructureLoaded = null,
  sourceUrlForPdbId = null,
  sourceCitationUrl = null,
  showStructureControls = true,
  compactLayout = false,
}) {
  const [pdbInput, setPdbInput] = useState(defaultPdbId);
  const [inputError, setInputError] = useState("");
  const [loadedPdbId, setLoadedPdbId] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadingStatus, setLoadingStatus] = useState("");
  const [error, setError] = useState("");
  const [metadata, setMetadata] = useState(null);

  // Visualization options
  const [colorScheme, setColorScheme] = useState("spectrum"); // spectrum | ssJmol | cyan | chain
  const [showLigand, setShowLigand] = useState(true);
  const [isSpinning, setIsSpinning] = useState(false);

  // 3Dmol viewer references
  const viewerElement = useRef(null);
  const viewerInstance = useRef(null);
  const initialViewRef = useRef(null);
  const pdbDataRef = useRef(null);
  const abortControllerRef = useRef(null);

  // Synchronize internal input if defaultPdbId prop changes
  useEffect(() => {
    if (defaultPdbId && defaultPdbId !== pdbInput && !loadedPdbId) {
      setPdbInput(defaultPdbId);
    }
  }, [defaultPdbId]);

  /**
   * Apply cartoon ribbon and distinct non-water HETATM representations.
   */
  const applyStyles = useCallback((viewer, scheme, ligandVisible) => {
    if (!viewer) return;

    try {
      // 1. Protein Cartoon representation
      let cartoonStyle = { opacity: 0.92 };
      if (scheme === "spectrum") {
        cartoonStyle.color = "spectrum";
      } else if (scheme === "ssJmol") {
        cartoonStyle.colorscheme = "ssJmol";
      } else if (scheme === "chain") {
        cartoonStyle.colorscheme = "chain";
      } else if (scheme === "cyan") {
        cartoonStyle.color = "#06b6d4";
      } else {
        cartoonStyle.color = "spectrum";
      }

      // Apply cartoon to standard amino acid ATOM records
      viewer.setStyle({ hetflag: false }, { cartoon: cartoonStyle });

      // 2. Distinct non-water HETATM representation (greenCarbon stick & sphere)
      if (ligandVisible) {
        viewer.setStyle({ hetflag: true }, {
          stick: { radius: 0.26, colorscheme: "greenCarbon" },
          sphere: { scale: 0.30, colorscheme: "greenCarbon" },
        });
      } else {
        viewer.setStyle({ hetflag: true }, {});
      }

      // 3. Hide water solvent molecules to prevent visual clutter
      viewer.setStyle({ resn: ["HOH", "WAT", "DOD", "H3O", "H2O", "OH2"] }, {});

      viewer.render();
    } catch (err) {
      console.warn("Could not apply style update:", err);
    }
  }, []);

  /**
   * Load and render PDB structure from RCSB PDB.
   */
  const handleLoadStructure = useCallback(async (targetId) => {
    const rawId = (targetId || pdbInput || "").trim().toUpperCase();
    const localSourceUrl = typeof sourceUrlForPdbId === "function"
      ? sourceUrlForPdbId(rawId)
      : null;

    // Input Validation: exactly 4 alphanumeric characters
    if (!rawId) {
      setInputError("Please enter a 4-character PDB code.");
      return;
    }
    if (!localSourceUrl && !/^[0-9A-Z]{4}$/.test(rawId)) {
      setInputError("PDB ID must be a 4-character alphanumeric code (e.g., 1M17).");
      return;
    }

    setInputError("");
    setError("");
    setLoading(true);
    setLoadingStatus(localSourceUrl
      ? `Loading local PDB structure ${rawId}...`
      : `Fetching PDB ${rawId} coordinates from RCSB PDB...`);

    // Cancel any previous in-flight fetch
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      // 1. Fetch raw PDB file from RCSB PDB
      const pdbUrl = localSourceUrl || `https://files.rcsb.org/download/${rawId}.pdb`;
      const response = await fetch(pdbUrl, { signal: controller.signal });

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error(`PDB ID '${rawId}' was not found in the RCSB Protein Data Bank.`);
        }
        throw new Error(`Failed to download PDB ${rawId} (HTTP status ${response.status}).`);
      }

      const pdbText = await response.text();

      if (!pdbText || (!pdbText.includes("ATOM") && !pdbText.includes("HETATM"))) {
        throw new Error(`PDB entry '${rawId}' does not contain valid 3D macromolecular coordinates.`);
      }

      pdbDataRef.current = pdbText;
      setLoadingStatus(`Parsing macromolecular metadata for ${rawId}...`);

      // 2. Parse fallback metadata from PDB file header
      const headerMeta = parsePdbHeader(pdbText);

      // 3. Fetch enhanced metadata only for the existing remote RCSB viewer path.
      let enhancedMeta = { ...headerMeta };
      try {
        if (!localSourceUrl) {
        const metaRes = await fetch(`https://data.rcsb.org/rest/v1/core/entry/${rawId}`, {
          signal: controller.signal,
        });
        if (metaRes.ok) {
          const apiJson = await metaRes.json();
          enhancedMeta = {
            ...headerMeta,
            title: apiJson.struct?.title || headerMeta.title,
            classification: apiJson.struct_keywords?.pdbx_keywords || headerMeta.classification,
            resolution: apiJson.rcsb_entry_info?.resolution_combined?.[0]
              ? `${apiJson.rcsb_entry_info.resolution_combined[0]} Å`
              : headerMeta.resolution,
            method: apiJson.exptl?.[0]?.method || headerMeta.method,
            depositDate: apiJson.pdbx_audit_revision_history?.[0]?.revision_date
              ? apiJson.pdbx_audit_revision_history[0].revision_date.split("T")[0]
              : headerMeta.depositDate,
            citation: apiJson.rcsb_primary_citation ? {
              title: apiJson.rcsb_primary_citation.title,
              journal: apiJson.rcsb_primary_citation.rcsb_journal_abbrev,
              year: apiJson.rcsb_primary_citation.year,
              authors: apiJson.rcsb_primary_citation.rcsb_authors?.join(", "),
              doi: apiJson.rcsb_primary_citation.pdbx_database_id_DOI,
            } : null,
          };
        }
        }
      } catch (metaErr) {
        // Fallback to headerMeta if REST API is blocked or slow
        console.warn("RCSB REST metadata fetch skipped, using header metadata:", metaErr);
      }

      setMetadata(enhancedMeta);
      setLoadingStatus(`Initializing 3Dmol WebGL canvas...`);

      // 4. Initialize 3Dmol.js viewer
      const module = await import("3dmol");
      if (controller.signal.aborted || !viewerElement.current) return;

      const createViewer =
        module.createViewer ||
        module.default?.createViewer ||
        module.$3Dmol?.createViewer;

      if (!createViewer) {
        throw new Error("Could not initialize 3Dmol WebGL viewer.");
      }

      // Clean up previous viewer instance if present
      if (viewerInstance.current) {
        try {
          viewerInstance.current.spin(false);
          viewerInstance.current.clear();
        } catch {}
      }
      if (viewerElement.current) {
        viewerElement.current.replaceChildren();
      }

      // Instantiate viewer
      const viewer = createViewer(viewerElement.current, {
        backgroundColor: "#08111f",
        antialias: true,
      });

      // Add Model
      viewer.addModel(pdbText, "pdb");

      // Apply cartoon and ligand representations
      applyStyles(viewer, colorScheme, showLigand);

      // Fit to camera bounds
      viewer.zoomTo();
      viewer.resize();
      viewer.render();

      initialViewRef.current = viewer.getView();
      viewerInstance.current = viewer;
      setIsSpinning(false);

      // Update confirmed loaded state
      setLoadedPdbId(rawId);
      if (typeof onStructureLoaded === "function") {
        onStructureLoaded(rawId, enhancedMeta);
      }
    } catch (err) {
      if (err.name !== "AbortError") {
        setError(err.message || `An error occurred while loading PDB '${rawId}'.`);
        setLoadedPdbId("");
      }
    } finally {
      if (!controller.signal.aborted) {
        setLoading(false);
        setLoadingStatus("");
      }
    }
  }, [pdbInput, colorScheme, showLigand, applyStyles, onStructureLoaded, sourceUrlForPdbId]);

  // Initial load on component mount for defaultPdbId (1M17)
  useEffect(() => {
    if (defaultPdbId) {
      handleLoadStructure(defaultPdbId);
    }

    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      if (viewerInstance.current) {
        try {
          viewerInstance.current.spin(false);
          viewerInstance.current.clear();
        } catch {}
      }
      viewerInstance.current = null;
      if (viewerElement.current) {
        viewerElement.current.replaceChildren();
      }
    };
  }, []);

  // Update styles when color scheme or ligand visibility changes
  useEffect(() => {
    if (viewerInstance.current && loadedPdbId) {
      applyStyles(viewerInstance.current, colorScheme, showLigand);
    }
  }, [colorScheme, showLigand, loadedPdbId, applyStyles]);

  // Window resize handler to maintain WebGL aspect ratio
  useEffect(() => {
    function handleResize() {
      if (viewerInstance.current) {
        viewerInstance.current.resize();
        viewerInstance.current.render();
      }
    }
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  // Viewer Camera Actions
  function handleZoomIn() {
    if (!viewerInstance.current) return;
    viewerInstance.current.zoom(1.25, 120);
    viewerInstance.current.render();
  }

  function handleZoomOut() {
    if (!viewerInstance.current) return;
    viewerInstance.current.zoom(0.8, 120);
    viewerInstance.current.render();
  }

  function handleRotate(axis, degrees = 30) {
    if (!viewerInstance.current) return;
    viewerInstance.current.rotate(degrees, axis);
    viewerInstance.current.render();
  }

  function handleFitToView() {
    if (!viewerInstance.current) return;
    viewerInstance.current.zoomTo();
    viewerInstance.current.render();
  }

  function handleResetCamera() {
    if (!viewerInstance.current) return;
    if (initialViewRef.current) {
      viewerInstance.current.setView(initialViewRef.current);
    } else {
      viewerInstance.current.zoomTo();
    }
    viewerInstance.current.render();
  }

  function handleToggleSpin() {
    if (!viewerInstance.current) return;
    if (isSpinning) {
      viewerInstance.current.spin(false);
      setIsSpinning(false);
    } else {
      viewerInstance.current.spin("y", 0.6);
      setIsSpinning(true);
    }
  }

  return (
    <div className="space-y-6">
      {/* Component Title & Purpose Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-slate-100 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-base font-bold text-slate-900 sm:text-lg">
              Target Macromolecule &amp; Protein PDB Viewer
            </h3>
            <span className="rounded bg-teal-100 text-teal-800 border border-teal-200 px-2 py-0.5 text-[10px] font-bold tracking-wider uppercase">
              3Dmol.js WebGL
            </span>
          </div>
          <p className="mt-1 text-xs text-slate-500">
            Interactive structure visualization with a heuristic non-water HETATM residue inventory.
          </p>
        </div>

        {loadedPdbId && (
          <div className="flex items-center gap-2">
            <span className="rounded-full bg-emerald-50 border border-emerald-200 px-3 py-1 text-xs font-semibold text-emerald-800 flex items-center gap-1.5">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
              Active Structure: <strong className="font-mono">{loadedPdbId}</strong>
            </span>
          </div>
        )}
      </div>

      {/* Main Two-Column Layout */}
      <div className={`grid grid-cols-1 ${compactLayout ? "" : "lg:grid-cols-12"} gap-6`}>
        {/* =========================================================================
            LEFT PANEL: Controls, Input Validation, Status, and Structure Metadata
            ========================================================================= */}
        <div className={`${compactLayout ? "" : "lg:col-span-5 xl:col-span-4"} space-y-4`}>
          {/* Card 1: PDB Input & Load Action */}
          {showStructureControls && <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm space-y-4">
            <div>
              <label htmlFor="pdb-id-input" className="block text-xs font-bold uppercase tracking-wider text-slate-700">
                PDB Accession ID
              </label>
              <p className="text-[11px] text-slate-500 mt-0.5">
                Enter any 4-character Protein Data Bank identifier.
              </p>
            </div>

            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleLoadStructure(pdbInput);
              }}
              className="space-y-3"
            >
              <div className="flex items-center gap-2">
                <div className="relative flex-1">
                  <input
                    id="pdb-id-input"
                    type="text"
                    maxLength={4}
                    value={pdbInput}
                    onChange={(e) => {
                      setPdbInput(e.target.value.toUpperCase());
                      if (inputError) setInputError("");
                    }}
                    placeholder="e.g. 1M17"
                    disabled={loading}
                    className={`w-full font-mono text-sm uppercase font-bold tracking-wider rounded-lg border px-3 py-2 text-slate-900 bg-slate-50 placeholder:text-slate-400 focus:bg-white focus:outline-none transition ${
                      inputError
                        ? "border-rose-400 focus:border-rose-500 focus:ring-1 focus:ring-rose-500"
                        : "border-slate-300 focus:border-teal-500 focus:ring-1 focus:ring-teal-500"
                    }`}
                  />
                  <span className="absolute right-3 top-2.5 text-[10px] font-mono text-slate-400">
                    {pdbInput.length}/4
                  </span>
                </div>

                <button
                  type="submit"
                  disabled={loading || pdbInput.trim().length !== 4}
                  className="inline-flex items-center justify-center gap-1.5 rounded-lg bg-teal-600 px-4 py-2 text-xs font-bold text-white shadow-sm hover:bg-teal-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-teal-500 disabled:cursor-not-allowed disabled:opacity-40 transition"
                >
                  {loading ? (
                    <>
                      <span className="inline-block h-3 w-3 animate-spin rounded-full border-2 border-white border-t-transparent" />
                      <span>Loading...</span>
                    </>
                  ) : (
                    <>
                      <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                      </svg>
                      <span>Load Structure</span>
                    </>
                  )}
                </button>
              </div>

              {/* Input Validation Error */}
              {inputError && (
                <p className="text-xs text-rose-600 font-medium flex items-center gap-1">
                  <svg className="w-3.5 h-3.5 shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                  <span>{inputError}</span>
                </p>
              )}
            </form>

            {/* Quick Presets */}
            <div>
              <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-2">
                Curated EGFR Presets
              </p>
              <div className="flex flex-wrap gap-1.5">
                {REFERENCE_PRESETS.map((preset) => {
                  const isCurrent = loadedPdbId === preset.id;
                  return (
                    <button
                      key={preset.id}
                      type="button"
                      onClick={() => {
                        setPdbInput(preset.id);
                        handleLoadStructure(preset.id);
                      }}
                      disabled={loading}
                      title={preset.description}
                      className={`rounded px-2.5 py-1 text-xs font-mono font-medium transition ${
                        isCurrent
                          ? "bg-teal-700 text-white shadow-xs font-bold"
                          : "bg-slate-100 text-slate-700 hover:bg-slate-200 hover:text-slate-900 border border-slate-200"
                      }`}
                    >
                      {preset.label}
                    </button>
                  );
                })}
              </div>
            </div>
          </div>}

          {/* Card 2: Loading State or Network Error */}
          {loading && (
            <div className="rounded-xl border border-teal-200 bg-teal-50/70 p-4 animate-pulse">
              <div className="flex items-center gap-3">
                <span className="inline-block h-5 w-5 animate-spin rounded-full border-2 border-teal-600 border-t-transparent shrink-0" />
                <div className="min-w-0">
                  <p className="text-xs font-bold text-teal-900">Retrieving Structure Data</p>
                  <p className="text-[11px] text-teal-700 truncate">{loadingStatus || "Loading from RCSB PDB..."}</p>
                </div>
              </div>
            </div>
          )}

          {error && !loading && (
            <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 space-y-2">
              <div className="flex items-start gap-2.5">
                <svg className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <div className="flex-1">
                  <p className="text-xs font-bold text-rose-900">Structure Load Failed</p>
                  <p className="text-xs text-rose-700 mt-0.5">{error}</p>
                </div>
              </div>
              {showStructureControls && <div className="pt-2 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => {
                    setPdbInput("1M17");
                    handleLoadStructure("1M17");
                  }}
                  className="rounded border border-rose-300 bg-white px-2.5 py-1 text-[11px] font-semibold text-rose-700 hover:bg-rose-100/50 transition"
                >
                  Reset to 1M17
                </button>
                <button
                  type="button"
                  onClick={() => handleLoadStructure(pdbInput)}
                  className="rounded bg-rose-600 px-2.5 py-1 text-[11px] font-semibold text-white hover:bg-rose-700 transition"
                >
                  Retry Load
                </button>
              </div>}
            </div>
          )}

          {/* Card 3: Structure Metadata & Ligand Evidence */}
          {metadata && !loading && (
            <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-700">
                  Crystallographic Provenance
                </span>
                {(sourceUrlForPdbId ? sourceCitationUrl : `https://www.rcsb.org/structure/${loadedPdbId}`) && (
                  <a
                    href={sourceUrlForPdbId ? sourceCitationUrl : `https://www.rcsb.org/structure/${loadedPdbId}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-[11px] font-medium text-teal-700 hover:text-teal-900 underline"
                    title="Open structure source in new tab"
                  >
                    <span>{sourceUrlForPdbId ? "Structure source" : `RCSB #${loadedPdbId}`}</span>
                    <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10v-4M14 4h6m0 0v6m0-6L10 14" />
                    </svg>
                  </a>
                )}
              </div>

              {/* Title & Target */}
              <div>
                <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Structure Title</p>
                <p className="text-xs font-semibold text-slate-900 mt-0.5 leading-snug">
                  {metadata.title}
                </p>
              </div>

              {/* Metrics Grid */}
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="rounded-lg border border-slate-100 bg-slate-50 p-2.5">
                  <span className="text-[10px] font-bold uppercase text-slate-400">Method</span>
                  <p className="font-semibold text-slate-900 mt-0.5 truncate">{metadata.method}</p>
                </div>
                <div className="rounded-lg border border-slate-100 bg-slate-50 p-2.5">
                  <span className="text-[10px] font-bold uppercase text-slate-400">Resolution</span>
                  <p className="font-data font-bold text-teal-800 mt-0.5">{metadata.resolution}</p>
                </div>
                <div className="rounded-lg border border-slate-100 bg-slate-50 p-2.5">
                  <span className="text-[10px] font-bold uppercase text-slate-400">Classification</span>
                  <p className="font-semibold text-slate-800 mt-0.5 truncate">{metadata.classification}</p>
                </div>
                <div className="rounded-lg border border-slate-100 bg-slate-50 p-2.5">
                  <span className="text-[10px] font-bold uppercase text-slate-400">Deposit Date</span>
                  <p className="font-mono text-slate-800 mt-0.5">{metadata.depositDate}</p>
                </div>
              </div>

              {/* Chains & Atoms */}
              <div className="flex items-center justify-between text-xs py-1 border-t border-slate-100">
                <span className="text-slate-500">Chains:</span>
                <span className="font-semibold text-slate-800">
                  {metadata.chains.length > 0 ? metadata.chains.join(", ") : "Single Chain"}
                </span>
              </div>
              <div className="flex items-center justify-between text-xs py-1 border-t border-slate-100">
                <span className="text-slate-500">Coordinates:</span>
                <span className="font-data text-slate-800">
                  {metadata.atomCount.toLocaleString()} protein atoms &middot; {metadata.hetatmCount} hetero atoms
                </span>
              </div>

              {/* Co-crystallized Ligands Section */}
              <div className="border-t border-slate-100 pt-3">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
                    Non-water HETATM groups ({metadata.ligands.length})
                  </span>
                  {metadata.ligands.length > 0 ? (
                    <span className="rounded bg-emerald-50 text-emerald-800 border border-emerald-200 px-1.5 py-0.2 text-[9px] font-bold">
                      HETATM Records Present
                    </span>
                  ) : (
                    <span className="text-[10px] text-slate-400">None detected</span>
                  )}
                </div>

                {metadata.ligands.length > 0 ? (
                  <div className="space-y-1.5">
                    {metadata.ligands.map((lig, idx) => (
                      <div
                        key={idx}
                        className="rounded-lg border border-emerald-200/80 bg-emerald-50/40 p-2 text-xs flex items-center justify-between"
                      >
                        <div className="flex items-center gap-2">
                          <span className="rounded bg-emerald-600 text-white font-mono font-bold text-[10px] px-1.5 py-0.5">
                            {lig.resn}
                          </span>
                          <div>
                            <p className="font-semibold text-slate-900">
                              HETATM component {lig.resn}
                            </p>
                            <p className="text-[10px] text-slate-500">
                              Chain {lig.chain} &middot; Res #{lig.resSeq}
                            </p>
                          </div>
                        </div>
                        <span className="font-data text-[11px] font-medium text-emerald-800">
                          {lig.count} atoms
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-400 italic">
                    No non-water HETATM groups were detected by this viewer parser.
                  </p>
                )}
              </div>
            </div>
          )}
        </div>

        {/* =========================================================================
            RIGHT PANEL: Interactive 3Dmol.js Canvas & Toolbar Controls
            ========================================================================= */}
        <div className={`${compactLayout ? "" : "lg:col-span-7 xl:col-span-8"} flex flex-col space-y-3`}>
          {/* Top Canvas Toolbar */}
          <div className="rounded-xl border border-slate-200 bg-white p-3 shadow-xs flex flex-wrap items-center justify-between gap-3">
            {/* Color Scheme Picker */}
            <div className="flex items-center gap-2 text-xs">
              <span className="text-slate-500 font-medium">Cartoon:</span>
              <div className="inline-flex rounded-lg border border-slate-200 bg-slate-100 p-0.5 text-xs">
                <button
                  type="button"
                  onClick={() => setColorScheme("spectrum")}
                  className={`rounded px-2.5 py-1 font-medium transition ${
                    colorScheme === "spectrum"
                      ? "bg-white text-slate-900 shadow-xs font-semibold"
                      : "text-slate-600 hover:text-slate-900"
                  }`}
                >
                  Spectrum
                </button>
                <button
                  type="button"
                  onClick={() => setColorScheme("ssJmol")}
                  className={`rounded px-2.5 py-1 font-medium transition ${
                    colorScheme === "ssJmol"
                      ? "bg-white text-slate-900 shadow-xs font-semibold"
                      : "text-slate-600 hover:text-slate-900"
                  }`}
                >
                  Secondary Structure
                </button>
                <button
                  type="button"
                  onClick={() => setColorScheme("chain")}
                  className={`rounded px-2.5 py-1 font-medium transition ${
                    colorScheme === "chain"
                      ? "bg-white text-slate-900 shadow-xs font-semibold"
                      : "text-slate-600 hover:text-slate-900"
                  }`}
                >
                  Chain
                </button>
                <button
                  type="button"
                  onClick={() => setColorScheme("cyan")}
                  className={`rounded px-2.5 py-1 font-medium transition ${
                    colorScheme === "cyan"
                      ? "bg-white text-cyan-900 shadow-xs font-semibold"
                      : "text-slate-600 hover:text-slate-900"
                  }`}
                >
                  Cyan
                </button>
              </div>
            </div>

            {/* Ligand Toggle & Spin Button */}
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setShowLigand(!showLigand)}
                className={`inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-1 text-xs font-medium transition ${
                  showLigand
                    ? "border-emerald-300 bg-emerald-50 text-emerald-800"
                    : "border-slate-200 bg-slate-50 text-slate-500"
                }`}
                title="Toggle non-water HETATM stick and sphere representation"
              >
                <span className={`h-2 w-2 rounded-full ${showLigand ? "bg-emerald-500" : "bg-slate-400"}`} />
                <span>Ligand {showLigand ? "Visible" : "Hidden"}</span>
              </button>

              <button
                type="button"
                onClick={handleToggleSpin}
                disabled={!loadedPdbId || loading}
                className={`inline-flex items-center gap-1 rounded-lg border px-2.5 py-1 text-xs font-medium transition disabled:opacity-40 ${
                  isSpinning
                    ? "border-amber-300 bg-amber-50 text-amber-800"
                    : "border-slate-200 bg-white text-slate-700 hover:bg-slate-50"
                }`}
              >
                <span>{isSpinning ? "⏸ Pause Spin" : "⟳ Auto-Spin"}</span>
              </button>
            </div>
          </div>

          {/* 3D Canvas Box */}
          <div className="relative overflow-hidden rounded-2xl border border-slate-800 bg-[#08111f] shadow-lg">
            {/* 3Dmol WebGL Container */}
            <div
              ref={viewerElement}
              className="h-[460px] w-full sm:h-[540px] lg:h-[580px]"
              aria-label="Interactive 3D Protein Macromolecule Viewer"
            />

            {/* Overlay: Active Ligand Indicator Pill */}
            {metadata?.ligands?.length > 0 && showLigand && !loading && (
              <div className="absolute top-3 left-3 pointer-events-none rounded-lg border border-emerald-500/40 bg-slate-950/80 px-2.5 py-1 text-[11px] text-emerald-300 backdrop-blur-xs flex items-center gap-1.5 shadow-sm">
                <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
                <span>HETATM component: <strong className="text-white font-mono">{metadata.ligands[0].resn}</strong> (Green Sticks)</span>
              </div>
            )}

            {/* Overlay: Loading Spinner */}
            {loading && (
              <div className="absolute inset-0 flex flex-col items-center justify-center bg-[#08111f]/90 p-6 text-center backdrop-blur-xs">
                <span className="inline-block h-8 w-8 animate-spin rounded-full border-3 border-teal-400 border-t-transparent" />
                <p className="mt-4 text-sm font-semibold text-slate-100">
                  {loadingStatus || "Preparing 3D Protein Canvas..."}
                </p>
                <p className="mt-1 text-xs text-slate-400">
                  Downloading coordinates and constructing WebGL cartoon meshes
                </p>
              </div>
            )}

            {/* Overlay: Empty State */}
            {!loadedPdbId && !loading && !error && (
              <div className="absolute inset-0 flex flex-col items-center justify-center bg-[#08111f] p-6 text-center">
                <div className="rounded-full bg-slate-800/80 p-4 mb-3 border border-slate-700">
                  <svg className="w-8 h-8 text-teal-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <circle cx="12" cy="12" r="3" strokeWidth="1.75" />
                    <ellipse cx="12" cy="12" rx="9" ry="4" transform="rotate(30 12 12)" strokeWidth="1.75" />
                    <ellipse cx="12" cy="12" rx="9" ry="4" transform="rotate(-30 12 12)" strokeWidth="1.75" />
                  </svg>
                </div>
                <p className="text-sm font-semibold text-slate-200">
                  Ready to Load Protein Structure
                </p>
                <p className="mt-1 text-xs text-slate-400 max-w-sm">
                  Enter any valid 4-character PDB code or select a curated preset (e.g., 1M17) to launch 3D visualization.
                </p>
              </div>
            )}

            {/* Overlay: Interactive Mouse Controls Help Bar */}
            {loadedPdbId && !loading && (
              <div className="absolute bottom-3 left-3 right-3 pointer-events-none flex flex-wrap items-center justify-between gap-2 rounded-lg bg-slate-950/70 border border-slate-800/80 px-3 py-1.5 text-[10px] text-slate-400 backdrop-blur-xs">
                <div className="flex items-center gap-3">
                  <span>🖱️ <strong>Left-Drag:</strong> Rotate</span>
                  <span>🔍 <strong>Scroll:</strong> Zoom</span>
                  <span>✋ <strong>Right-Drag:</strong> Pan</span>
                </div>
                <span className="font-mono text-teal-400/90">{loadedPdbId} &middot; {metadata?.resolution || "3Dmol"}</span>
              </div>
            )}
          </div>

          {/* Bottom Controls Bar: Zoom, Rotation, Fit to View, Reset Camera */}
          <div className="rounded-xl border border-slate-200 bg-white p-3 shadow-xs flex flex-wrap items-center justify-between gap-3">
            {/* Rotation Buttons */}
            <div className="flex items-center gap-1.5">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mr-1">Rotate:</span>
              <button
                type="button"
                onClick={() => handleRotate("y", -30)}
                disabled={!loadedPdbId || loading}
                title="Rotate Left (-30°)"
                className="rounded-lg border border-slate-200 bg-slate-50 px-2 py-1 text-xs font-semibold text-slate-700 hover:bg-slate-100 hover:text-slate-900 disabled:opacity-40 transition"
              >
                ⟲ Left
              </button>
              <button
                type="button"
                onClick={() => handleRotate("y", 30)}
                disabled={!loadedPdbId || loading}
                title="Rotate Right (+30°)"
                className="rounded-lg border border-slate-200 bg-slate-50 px-2 py-1 text-xs font-semibold text-slate-700 hover:bg-slate-100 hover:text-slate-900 disabled:opacity-40 transition"
              >
                ⟳ Right
              </button>
              <button
                type="button"
                onClick={() => handleRotate("x", -30)}
                disabled={!loadedPdbId || loading}
                title="Rotate Up (-30°)"
                className="rounded-lg border border-slate-200 bg-slate-50 px-2 py-1 text-xs font-semibold text-slate-700 hover:bg-slate-100 hover:text-slate-900 disabled:opacity-40 transition"
              >
                ▲ Up
              </button>
              <button
                type="button"
                onClick={() => handleRotate("x", 30)}
                disabled={!loadedPdbId || loading}
                title="Rotate Down (+30°)"
                className="rounded-lg border border-slate-200 bg-slate-50 px-2 py-1 text-xs font-semibold text-slate-700 hover:bg-slate-100 hover:text-slate-900 disabled:opacity-40 transition"
              >
                ▼ Down
              </button>
            </div>

            {/* Zoom, Fit to View, Reset Camera */}
            <div className="flex items-center gap-2">
              <div className="inline-flex rounded-lg border border-slate-200 bg-slate-50 p-0.5">
                <button
                  type="button"
                  onClick={handleZoomIn}
                  disabled={!loadedPdbId || loading}
                  title="Zoom In"
                  className="rounded px-2.5 py-1 text-xs font-bold text-slate-700 hover:bg-white hover:shadow-xs disabled:opacity-40 transition"
                >
                  + Zoom In
                </button>
                <button
                  type="button"
                  onClick={handleZoomOut}
                  disabled={!loadedPdbId || loading}
                  title="Zoom Out"
                  className="rounded px-2.5 py-1 text-xs font-bold text-slate-700 hover:bg-white hover:shadow-xs disabled:opacity-40 transition"
                >
                  - Zoom Out
                </button>
              </div>

              <button
                type="button"
                onClick={handleFitToView}
                disabled={!loadedPdbId || loading}
                className="inline-flex items-center gap-1 rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 hover:border-slate-400 disabled:opacity-40 transition"
                title="Fit structure to current viewport"
              >
                <svg className="w-3.5 h-3.5 text-teal-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
                </svg>
                <span>Fit to View</span>
              </button>

              <button
                type="button"
                onClick={handleResetCamera}
                disabled={!loadedPdbId || loading}
                className="inline-flex items-center gap-1 rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 hover:border-slate-400 disabled:opacity-40 transition"
                title="Reset camera to initial viewpoint"
              >
                <svg className="w-3.5 h-3.5 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                <span>Reset Camera</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
