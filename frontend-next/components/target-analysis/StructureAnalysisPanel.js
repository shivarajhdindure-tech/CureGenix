"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import ProteinPDBViewer from "../ProteinPDBViewer";
import { API_URL } from "@/lib/analysis";

async function responseJson(response) {
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(typeof payload.detail === "string" ? payload.detail : `Structure request failed (${response.status}).`);
  }
  return payload;
}

export default function StructureAnalysisPanel({ file = null, validation = null }) {
  const [curated, setCurated] = useState([]);
  const [selectedPdbId, setSelectedPdbId] = useState("1M17");
  const [uploadId, setUploadId] = useState(null);
  const [chainId, setChainId] = useState("");
  const [structure, setStructure] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const activeRequest = useRef(null);

  const beginRequest = useCallback(() => {
    activeRequest.current?.controller.abort();
    const request = { id: (activeRequest.current?.id || 0) + 1, controller: new AbortController() };
    activeRequest.current = request;
    setBusy(true);
    return request;
  }, []);

  const isCurrentRequest = useCallback((request) => activeRequest.current?.id === request.id, []);

  const loadCurated = useCallback(async (pdbId, selectedChain = "") => {
    const request = beginRequest();
    setError("");
    try {
      const query = selectedChain ? `?chain_id=${encodeURIComponent(selectedChain)}` : "";
      const data = await responseJson(await fetch(
        `${API_URL}/api/structures/curated/${encodeURIComponent(pdbId)}${query}`,
        { signal: request.controller.signal },
      ));
      if (!isCurrentRequest(request)) return;
      setStructure(data);
      setChainId(data.selected_chain_id || "");
    } catch (requestError) {
      if (isCurrentRequest(request) && requestError.name !== "AbortError") {
        setStructure(null);
        setError(requestError.message || "Could not analyze the curated structure.");
      }
    } finally {
      if (isCurrentRequest(request)) setBusy(false);
    }
  }, [beginRequest, isCurrentRequest]);

  const loadUpload = useCallback(async (id, selectedChain = "") => {
    const request = beginRequest();
    setError("");
    try {
      const query = selectedChain ? `?chain_id=${encodeURIComponent(selectedChain)}` : "";
      const data = await responseJson(await fetch(
        `${API_URL}/api/structures/uploads/${encodeURIComponent(id)}${query}`,
        { signal: request.controller.signal },
      ));
      if (!isCurrentRequest(request)) return;
      setStructure(data);
      setChainId(data.selected_chain_id || "");
    } catch (requestError) {
      if (isCurrentRequest(request) && requestError.name !== "AbortError") {
        setStructure(null);
        setError(requestError.message || "Could not analyze the uploaded structure.");
      }
    } finally {
      if (isCurrentRequest(request)) setBusy(false);
    }
  }, [beginRequest, isCurrentRequest]);

  useEffect(() => {
    const controller = new AbortController();
    let active = true;
    fetch(`${API_URL}/api/structures/curated`, { signal: controller.signal })
      .then(responseJson)
      .then((data) => {
        if (!active) return;
        setCurated(data.structures || []);
      })
      .catch((requestError) => {
        if (active) setError(requestError.message || "Could not load the curated structure registry.");
      });
    return () => { active = false; controller.abort(); };
  }, []);

  useEffect(() => {
    // Invalidate any previous structure request as soon as the parent file changes.
    activeRequest.current?.controller.abort();
    const request = {
      id: (activeRequest.current?.id || 0) + 1,
      controller: new AbortController(),
    };
    activeRequest.current = request;
    setStructure(null);
    setUploadId(null);
    setChainId("");
    setError("");

    if (file) {
      if (validation?.status === "checking") {
        setBusy(false);
        return () => request.controller.abort();
      }
      if (validation?.status !== "valid") {
        setBusy(false);
        setError(validation?.message || "The selected PDB file did not pass validation.");
        return () => request.controller.abort();
      }
      if (!file.name?.toLowerCase().endsWith(".pdb")) {
        setBusy(false);
        setError("Choose a PDB file with a .pdb filename. mmCIF upload is not supported yet.");
        return () => request.controller.abort();
      }
      if (file.size > 20 * 1024 * 1024) {
        setBusy(false);
        setError("PDB upload exceeds the 20 MiB limit.");
        return () => request.controller.abort();
      }

      const form = new FormData();
      form.append("file", file);
      setBusy(true);
      fetch(`${API_URL}/api/structures/uploads`, {
        method: "POST",
        body: form,
        signal: request.controller.signal,
      })
        .then(responseJson)
        .then((data) => {
          if (!isCurrentRequest(request)) return;
          setUploadId(data.upload_id);
          setChainId(data.selected_chain_id || "");
          setStructure(data);
        })
        .catch((requestError) => {
          if (isCurrentRequest(request) && requestError.name !== "AbortError") {
            setStructure(null);
            setError(requestError.message || "Could not validate the selected PDB file.");
          }
        })
        .finally(() => {
          if (isCurrentRequest(request)) setBusy(false);
        });
      return () => request.controller.abort();
    }

    setBusy(false);
    return () => request.controller.abort();
  }, [file, validation?.status, validation?.message, isCurrentRequest]);

  useEffect(() => {
    if (!file && curated.some((entry) => entry.pdb_id === selectedPdbId)) {
      loadCurated(selectedPdbId);
    }
  }, [file, curated, selectedPdbId, loadCurated]);

  function selectCurated(pdbId) {
    setSelectedPdbId(pdbId);
  }

  function selectChain(value) {
    setChainId(value);
    if (!value) {
      if (structure) setStructure({
        ...structure,
        selected_chain_id: null,
        validation: {
          ...structure.validation,
          status: structure.protein_chains?.length > 1 ? "chain_selection_required" : structure.validation?.status,
        },
      });
      return;
    }
    if (uploadId) loadUpload(uploadId, value);
    else if (selectedPdbId) loadCurated(selectedPdbId, value);
  }

  const viewerFileUrl = structure?.source?.file_url
    ? `${API_URL}${structure.source.file_url}`
    : null;
  const structureUrlForPdbId = useCallback(
    () => viewerFileUrl,
    [viewerFileUrl],
  );
  const chainAccessions = structure?.chain_accessions || {};
  const selectedAccessions = chainId ? chainAccessions[chainId] || [] : [];
  const warnings = structure?.validation?.warnings || [];

  return (
    <section className="space-y-5 rounded-xl border border-slate-200 bg-white p-5 shadow-sm" aria-labelledby="structure-analysis-title">
      <div>
        <h3 id="structure-analysis-title" className="text-base font-semibold text-slate-900">PDB Structure Analysis</h3>
        <p className="mt-1 text-xs text-slate-600">
          Preview the selected discovery PDB, or inspect a curated local EGFR structure when no file is selected. This section does not start molecule discovery or quantum calculations.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        <label className="text-xs font-semibold text-slate-700">
          Curated local structure
          <select
            aria-label="Curated local structure"
            className="mt-1 block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 font-mono text-sm"
            value={file ? "custom" : selectedPdbId}
            onChange={(event) => event.target.value !== "custom" && selectCurated(event.target.value)}
            disabled={busy || Boolean(file) || curated.length === 0}
          >
            {curated.map((entry) => (
              <option key={entry.pdb_id} value={entry.pdb_id}>{entry.pdb_id} · {entry.verified_structure_description}</option>
            ))}
            {file && <option value="custom">Selected file · {file.name}</option>}
          </select>
        </label>
        <p className="self-end text-xs leading-relaxed text-slate-600">
          The main PDB selection is previewed here. Selecting or replacing it does not start discovery.
        </p>
      </div>

      {error && <p role="alert" className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-800">{error}</p>}
      {busy && <p role="status" className="text-sm text-teal-800">Loading and validating {file ? file.name : "the curated structure"}…</p>}
      {file && validation?.status === "checking" && <p role="status" className="text-sm text-slate-600">Waiting for the selected PDB validation to finish…</p>}

      {structure && (
        <>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            <Info label="PDB ID" value={structure.pdb_id || "Not present in HEADER"} />
            <Info label="SHA-256" value={structure.source?.sha256 || "Unavailable"} mono />
            <Info label="Source" value={structure.source?.source_url || `Custom upload · ${structure.original_filename || "local file"}`} />
            <Info label="Protein chains" value={(structure.protein_chains || []).join(", ") || "None found"} />
            <Info label="Selected-chain DBREF accession" value={selectedAccessions.join(", ") || "Unresolved for selected chain"} />
            <Info label="Validation status" value={structure.validation?.status || "Unknown"} />
          </div>

          {(structure.protein_chains || []).length > 1 && (
            <label className="block max-w-md text-xs font-semibold text-slate-700">
              Select a protein chain (required for multi-chain structures)
              <select
                aria-label="Select protein chain"
                className="mt-1 block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 font-mono text-sm"
                value={chainId}
                onChange={(event) => selectChain(event.target.value)}
                disabled={busy}
                required
              >
                <option value="">Choose a chain…</option>
                {structure.protein_chains.map((chain) => <option key={chain} value={chain}>{chain === "_" ? "(blank)" : chain}</option>)}
              </select>
            </label>
          )}

          {warnings.length > 0 && (
            <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs text-amber-900">
              <p className="font-semibold">Structure warnings</p>
              <ul className="mt-1 list-disc space-y-1 pl-5">{warnings.map((warning, index) => <li key={`${index}-${warning}`}>{warning}</li>)}</ul>
            </div>
          )}

          <div className="grid gap-4 lg:grid-cols-2">
            <div className="rounded-lg border border-slate-200 p-4">
              <h4 className="text-sm font-semibold text-slate-900">Mutation annotations</h4>
              {(structure.mutation_annotations || []).length ? (
                <ul className="mt-2 space-y-1 text-xs text-slate-700">
                  {structure.mutation_annotations.map((mutation, index) => (
                    <li key={`${mutation.chain_id}-${mutation.pdb_residue_number}-${index}`}>
                      Chain {mutation.chain_id}, PDB residue {mutation.pdb_residue_number}: {mutation.reference_residue || "?"} → {mutation.observed_residue || "?"} ({mutation.accession || "accession unavailable"} {mutation.reference_residue_number || ""})
                    </li>
                  ))}
                </ul>
              ) : <p className="mt-2 text-xs text-slate-500">No explicit engineered mutation records were found.</p>}
            </div>
            <div className="rounded-lg border border-slate-200 p-4">
              <h4 className="text-sm font-semibold text-slate-900">Non-water HETATM residue inventory</h4>
              {(structure.non_water_hetatm_residues || []).length ? (
                <ul className="mt-2 max-h-40 space-y-1 overflow-auto text-xs text-slate-700">
                  {structure.non_water_hetatm_residues.map((residue, index) => (
                    <li key={`${residue.component_id}-${residue.chain_id}-${residue.residue_number}-${index}`}>
                      <span className="font-mono font-semibold">{residue.component_id}</span> · chain {residue.chain_id === "_" ? "(blank)" : residue.chain_id} · residue {residue.residue_number}{residue.insertion_code || ""} · {residue.atom_count} atoms
                    </li>
                  ))}
                </ul>
              ) : <p className="mt-2 text-xs text-slate-500">No non-water HETATM residues were found.</p>}
            </div>
          </div>

          <p className="rounded-lg bg-slate-50 p-3 text-xs leading-relaxed text-slate-600">
            HETATM inventory is not validated chemical extraction. Residue names do not establish molecular connectivity or bond orders. DBREF is a structure annotation only; this phase does not authorize calculations or assert affinity, efficacy, or target engagement.
          </p>

          {viewerFileUrl && (
            <ProteinPDBViewer
              key={`${structure.source?.kind}-${structure.upload_id || structure.pdb_id}-${viewerFileUrl}`}
              defaultPdbId={structure.pdb_id || "UPLD"}
              sourceUrlForPdbId={structureUrlForPdbId}
              sourceCitationUrl={structure.source?.source_url || null}
              showStructureControls={false}
              compactLayout
            />
          )}
        </>
      )}
    </section>
  );
}

function Info({ label, value, mono = false }) {
  return (
    <div className="min-w-0 rounded-lg border border-slate-200 bg-slate-50 p-3">
      <p className="text-[10px] font-bold uppercase tracking-wide text-slate-500">{label}</p>
      <p className={`mt-1 break-words text-xs text-slate-900 ${mono ? "font-mono" : ""}`}>{value}</p>
    </div>
  );
}
