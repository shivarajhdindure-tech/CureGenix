"use client";

import { TargetSequenceCoverageChart } from "../charts/ScientificCharts";
import UploadPanel from "../UploadPanel";
import StructureAnalysisPanel from "../target-analysis/StructureAnalysisPanel";
import CentralPDBSelector from "../CentralPDBSelector";

export default function TargetAnalysisWorkspace({
  result,
  derived,
  file,
  validation,
  onSelect,
  onRemove,
  onStart,
  disabled,
  targetUniprotId,
  onTargetUniprotIdChange,
  targetChainId,
  onTargetChainIdChange,
  activeStructure = null,
  curatedStructures = [],
  collectionMeta = null,
  onSelectCurated = null,
  onUploadCustom = null,
  structureLoading = false,
}) {
  const proteinInfo = derived?.proteinInfo || result?.protein_info || {};
  const identity = proteinInfo?.target_identity || {};
  const sequenceValidation = identity?.sequence_validation || null;
  const dbrefRecords = identity?.dbref_records || [];
  const chainAccessions = identity?.chain_accessions || {};
  const bindingSites = proteinInfo?.binding_sites || [];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-slate-200 pb-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-slate-900 sm:text-2xl">
            Target Analysis &amp; Sequence Evidence
          </h2>
          <p className="mt-1 text-sm text-slate-600">
            Protein structure verification, UniProt accession validation, crystallographic chain coverage, and pocket mapping.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="rounded-full bg-teal-50 border border-teal-200 px-3 py-1 text-xs font-semibold text-teal-800">
            {identity.identity_status || "Target Verification Active"}
          </span>
        </div>
      </div>

      {/* Central PDB Structure Selector */}
      <CentralPDBSelector
        curatedStructures={curatedStructures}
        collectionMeta={collectionMeta}
        activePdbId={activeStructure?.pdbId || "1M17"}
        activeStructure={activeStructure}
        onSelectCurated={onSelectCurated}
        onUploadCustom={onUploadCustom}
        loading={structureLoading}
      />

      {/* Main discovery input and synchronized structure preview */}
      <div className="grid items-start gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-slate-200/90 bg-white p-6 shadow-sm">
          <h3 className="text-base font-semibold text-slate-900 mb-2">
            Protein Target Structure &amp; Parameters
          </h3>
          <p className="text-xs text-slate-500 mb-6">
            Select a PDB to validate and preview it. Discovery runs only when you choose Start.
          </p>
          <UploadPanel
            file={file}
            validation={validation}
            onSelect={onSelect}
            onRemove={onRemove}
            onStart={onStart}
            disabled={disabled}
            targetUniprotId={targetUniprotId}
            onTargetUniprotIdChange={onTargetUniprotIdChange}
            targetChainId={targetChainId}
            onTargetChainIdChange={onTargetChainIdChange}
          />
        </div>
        <StructureAnalysisPanel file={file} validation={validation} />
      </div>

      {/* Visualization 6: Target Sequence Coverage Visualization */}
      <TargetSequenceCoverageChart
        sequenceValidation={sequenceValidation}
        proteinInfo={proteinInfo}
      />

      {/* Target Identity & DBREF Evidence Card */}
      <div className="rounded-xl border border-slate-200/90 bg-white p-6 shadow-sm">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <h3 className="text-base font-semibold text-slate-900">
            Crystallographic Chain Mapping &amp; DBREF Evidence
          </h3>
          <span className="text-xs text-slate-500">
            Source: {identity.identity_source || "PDB Header Parsing"}
          </span>
        </div>

        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <div className="rounded-lg border border-slate-200 bg-slate-50/60 p-4">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-600">
              Identified Target Identity
            </h4>
            <div className="mt-3 space-y-2 text-xs">
              <div className="flex justify-between py-1 border-b border-slate-200/60">
                <span className="text-slate-500">Target Name:</span>
                <span className="font-semibold text-slate-900">{activeStructure?.proteinName || identity.protein_name || proteinInfo.protein_name || "Not established"}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-200/60">
                <span className="text-slate-500">UniProt Accession:</span>
                <span className="font-mono font-bold text-teal-700">{activeStructure?.targetAccession || identity.uniprot_id || identity.selected_uniprot_id || "Not established"}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-200/60">
                <span className="text-slate-500">Selected Chain:</span>
                <span className="font-mono font-semibold text-slate-900">{activeStructure?.selectedChainId || identity.selected_chain_id || "Not selected"}</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-slate-500">UniProt Lookup Status:</span>
                <span className="text-slate-800">{identity.uniprot_lookup?.status || "Not attempted"}</span>
              </div>
            </div>
          </div>

          <div className="rounded-lg border border-slate-200 bg-slate-50/60 p-4">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-600">
              PDB Chain Accession Mapping
            </h4>
            <div className="mt-3 text-xs space-y-2">
              {Object.keys(chainAccessions).length > 0 ? (
                Object.entries(chainAccessions).map(([chain, accs]) => (
                  <div key={chain} className="flex justify-between py-1 border-b border-slate-200/60">
                    <span className="font-semibold text-slate-700">Chain {chain || "(blank)"}:</span>
                    <span className="font-mono text-slate-900">{accs.join(", ")}</span>
                  </div>
                ))
              ) : (
                <div className="py-2 text-slate-500">No DBREF-linked UniProt accession was parsed.</div>
              )}
            </div>
          </div>
        </div>

        {/* Alignment Text Details */}
        {sequenceValidation?.aligned_observed_sequence && (
          <div className="mt-5 rounded-lg border border-slate-200 bg-slate-900 p-4 text-xs font-mono text-slate-200">
            <p className="text-teal-400 font-bold mb-2">Detailed Sequence Alignment (Observed vs Reference):</p>
            <p className="overflow-x-auto whitespace-pre-wrap break-all text-slate-300">
              Observed:  {sequenceValidation.aligned_observed_sequence}
            </p>
            <p className="mt-1 overflow-x-auto whitespace-pre-wrap break-all text-slate-400">
              Reference: {sequenceValidation.aligned_reference_sequence}
            </p>
          </div>
        )}
      </div>

      {/* Detected Binding Sites */}
      <div className="rounded-xl border border-slate-200/90 bg-white p-6 shadow-sm">
        <h3 className="text-base font-semibold text-slate-900 mb-1">
          Detected Catalytic &amp; Binding Pockets
        </h3>
        <p className="text-xs text-slate-500 mb-4">
          Target-specific pocket annotations are shown only for a sequence-validated EGFR identity. PDB identity checks do not establish binding or affinity.
        </p>

        {identity.identity_state === "structure_linked_sequence_validated" && identity.uniprot_id === "P00533" ? <div className="grid gap-3 sm:grid-cols-3">
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
            <p className="text-xs font-semibold text-slate-800">ATP Cleft Pocket 1</p>
            <p className="mt-1 text-xs text-slate-600">Key residues: Met793 (hinge), Thr790 (gatekeeper), Leu718</p>
            <span className="mt-2 inline-block rounded bg-teal-100 text-teal-800 text-[10px] font-semibold px-2 py-0.5">
              Catalytically Active
            </span>
          </div>

          <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
            <p className="text-xs font-semibold text-slate-800">Allosteric Pocket (DFG-out)</p>
            <p className="mt-1 text-xs text-slate-600">Key residues: Asp855, Phe856, Gly857, Glu762</p>
            <span className="mt-2 inline-block rounded bg-slate-200 text-slate-700 text-[10px] font-semibold px-2 py-0.5">
              Conformational Site
            </span>
          </div>

          <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
            <p className="text-xs font-semibold text-slate-800">P-Loop Sub-pocket</p>
            <p className="mt-1 text-xs text-slate-600">Key residues: Gly719, Ser720, Phe723</p>
            <span className="mt-2 inline-block rounded bg-slate-200 text-slate-700 text-[10px] font-semibold px-2 py-0.5">
              Phosphate Region
            </span>
          </div>
        </div> : <p role="note" className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs text-amber-900">No target-specific EGFR pocket annotations are being applied to this structure because its identity is not validated as EGFR.</p>}
      </div>
    </div>
  );
}
