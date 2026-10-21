"use client";

import { useEffect, useRef, useState } from "react";

export default function Molecule3DExplorer({ candidates = [] }) {
  const [selectedId, setSelectedId] = useState("");
  const [structure, setStructure] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const viewerElement = useRef(null);
  const viewerInstance = useRef(null);

  const usableCandidates = candidates.filter(
    (candidate) =>
      candidate?.id &&
      typeof candidate.smiles === "string" &&
      candidate.smiles.trim()
  );

  useEffect(() => {
    if (!usableCandidates.length) {
      setSelectedId("");
      return;
    }

    if (!usableCandidates.some((candidate) => candidate.id === selectedId)) {
      setSelectedId(usableCandidates[0].id);
    }
  }, [usableCandidates, selectedId]);

  const selectedCandidate = usableCandidates.find(
    (candidate) => candidate.id === selectedId
  );

  useEffect(() => {
    if (!selectedCandidate) {
      setStructure(null);
      setError("");
      setLoading(false);
      return;
    }

    const controller = new AbortController();

    async function loadStructure() {
      setLoading(true);
      setError("");
      setStructure(null);

      try {
        const apiBase = (
          process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
        ).replace(/\/+$/, "");

        const response = await fetch(`${apiBase}/api/molecule/3d`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ smiles: selectedCandidate.smiles }),
          signal: controller.signal,
        });

        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
          throw new Error(
            data.detail || `Structure generation failed (${response.status}).`
          );
        }

        setStructure(data);
      } catch (err) {
        if (err.name !== "AbortError") {
          setError(err.message || "Could not generate this structure.");
        }
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }

    loadStructure();
    return () => controller.abort();
  }, [selectedCandidate?.id, selectedCandidate?.smiles]);

  useEffect(() => {
    let cancelled = false;
    let viewer = null;

    async function renderStructure() {
      if (!structure?.mol_block || !viewerElement.current) return;

      try {
        const module = await import("3dmol");
        if (cancelled || !viewerElement.current) return;

        const createViewer =
          module.createViewer ||
          module.default?.createViewer ||
          module.$3Dmol?.createViewer;

        if (!createViewer) {
          throw new Error("The 3Dmol viewer could not be initialized.");
        }

        viewer = createViewer(viewerElement.current, {
          backgroundColor: "#08111f",
          antialias: true,
        });

        viewer.addModel(structure.mol_block, "mol");
        viewer.setStyle({}, {
          stick: { radius: 0.16 },
          sphere: { scale: 0.24 },
        });
        viewer.zoomTo();
        viewer.resize();
        viewer.render();

        if (!cancelled) viewerInstance.current = viewer;
      } catch (err) {
        if (!cancelled) {
          setError(err.message || "Could not render the molecular structure.");
        }
      }
    }

    renderStructure();

    return () => {
      cancelled = true;
      if (viewer) {
        try {
          viewer.clear();
        } catch {
          // Viewer may already have been cleared.
        }
      }
      viewerInstance.current = null;
      if (viewerElement.current) viewerElement.current.replaceChildren();
    };
  }, [structure]);

  function resetView() {
    if (!viewerInstance.current) return;
    viewerInstance.current.zoomTo();
    viewerInstance.current.rotate(0, "y");
    viewerInstance.current.render();
  }

  return (
    <section className="panel space-y-5 p-5 md:p-6">
      <div>
        <p className="eyebrow !text-cyan-300/80">Molecular visualization</p>
        <h2 className="section-title mt-2">Interactive 3D Explorer</h2>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
          Explore generated molecular conformations for candidates in this
          analysis. Select a candidate, drag to rotate, and scroll to zoom.
        </p>
      </div>

      {usableCandidates.length === 0 ? (
        <p className="rounded-lg border border-white/10 p-4 text-sm text-slate-400">
          No candidates with SMILES strings are available for visualization.
        </p>
      ) : (
        <>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
            <label className="block flex-1">
              <span className="metric-label">Select candidate</span>
              <select
                value={selectedId}
                onChange={(event) => setSelectedId(event.target.value)}
                className="mt-2 w-full rounded-lg border border-white/10 bg-ink-950 px-3 py-3 text-sm text-white outline-none focus:border-cyan-300"
              >
                {usableCandidates.map((candidate) => (
                  <option key={candidate.id} value={candidate.id}>
                    {candidate.id}
                  </option>
                ))}
              </select>
            </label>

            <button
              type="button"
              onClick={resetView}
              disabled={!structure || loading}
              className="btn-ghost disabled:cursor-not-allowed disabled:opacity-40"
            >
              Reset view
            </button>
          </div>

          <div className="relative overflow-hidden rounded-xl border border-white/10 bg-[#08111f]">
            <div
              ref={viewerElement}
              className="h-[320px] w-full sm:h-[420px]"
              aria-label="Interactive three-dimensional molecular structure"
            />

            {(loading || error || !structure) && (
              <div className="absolute inset-0 flex items-center justify-center bg-[#08111f]/90 p-6 text-center">
                <p className="max-w-md text-sm text-slate-300">
                  {loading
                    ? "Generating and optimizing molecular conformation…"
                    : error
                      ? error
                      : "Waiting for molecular structure…"}
                </p>
              </div>
            )}
          </div>

          {structure && !loading && !error && (
            <div className="grid gap-3 sm:grid-cols-3">
              <div className="rounded-lg border border-white/[0.08] bg-white/[0.02] p-3">
                <p className="metric-label">Total atoms</p>
                <p className="font-data mt-2 text-xl text-white">
                  {structure.atom_count}
                </p>
              </div>
              <div className="rounded-lg border border-white/[0.08] bg-white/[0.02] p-3">
                <p className="metric-label">Heavy atoms</p>
                <p className="font-data mt-2 text-xl text-white">
                  {structure.heavy_atom_count}
                </p>
              </div>
              <div className="rounded-lg border border-white/[0.08] bg-white/[0.02] p-3">
                <p className="metric-label">Geometry optimization</p>
                <p className="mt-2 text-sm text-cyan-200">
                  {structure.geometry_optimization}
                </p>
              </div>
            </div>
          )}

          {selectedCandidate && (
            <div>
              <p className="metric-label">SMILES</p>
              <p className="font-data mt-2 break-all text-xs leading-5 text-slate-300">
                {selectedCandidate.smiles}
              </p>
            </div>
          )}

          <div className="rounded-lg border border-amber-400/20 bg-amber-400/[0.05] p-4">
            <p className="text-sm font-medium text-amber-200">
              Computational structure — not experimentally validated
            </p>
            <p className="mt-1 text-xs leading-5 text-slate-400">
              Generated from SMILES using RDKit ETKDGv3 and MMFF geometry
              optimization. This is a generated conformer, not an experimentally
              determined structure. A successful optimization does not establish
              biological activity, target binding, drug efficacy, or safety.
            </p>
          </div>
        </>
      )}
    </section>
  );
}
