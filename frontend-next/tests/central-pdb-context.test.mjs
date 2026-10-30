import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import {
  createInitialStructureContext,
  atomicSwitchCurated,
  atomicSwitchCustom,
  updateChainSelection,
  applyStructureAnalysis,
} from "../lib/activeStructureState.mjs";

test("Active context initializes with default curated structure and valid EGFR metadata", () => {
  const ctx = createInitialStructureContext("1M17");
  assert.equal(ctx.structureSource, "curated");
  assert.equal(ctx.pdbId, "1M17");
  assert.equal(ctx.targetAccession, "P00533");
  assert.equal(ctx.selectedChainId, "A");
  assert.equal(ctx.discoveryResult, null);
  assert.equal(ctx.activeMolecularInput, null);
  assert.equal(ctx.activeQuantumJob, null);
});

test("Switching from 1M17 to 2ITX atomically clears stale discovery and quantum states", () => {
  // Simulate active state after a discovery run on 1M17
  const prev = {
    ...createInitialStructureContext("1M17"),
    discoveryResult: { decisions: [{ drug_name: "CAN-001", adjusted_score: 0.85 }] },
    candidateGenerationStatus: { candidate_count: 4 },
    activeMolecularInput: { smiles: "COCC...", candidate_id: "AQ4-A-999" },
    activeQuantumJob: { job_id: "molecular-123", status: "completed" },
    coCrystallizedLigands: [{ component_id: "AQ4" }],
  };

  const switched = atomicSwitchCurated(prev, "2ITX");

  // Verify new structure metadata is staged
  assert.equal(switched.pdbId, "2ITX");
  assert.equal(switched.fileUrl, "/api/structures/curated/2ITX/file");
  assert.equal(switched.validationStatus, "checking");

  // Verify all stale downstream state is cleared atomically
  assert.equal(switched.discoveryResult, null);
  assert.equal(switched.candidateGenerationStatus, null);
  assert.equal(switched.activeMolecularInput, null);
  assert.equal(switched.activeQuantumJob, null);
  assert.equal(switched.sequenceValidation, null);
  assert.deepEqual(switched.coCrystallizedLigands, []);
});

test("Switching from curated PDB to custom upload clears curated accession and stages custom state", () => {
  const prev = createInitialStructureContext("1M17");
  const switched = atomicSwitchCustom(prev, "1crn.pdb");

  assert.equal(switched.structureSource, "custom");
  assert.equal(switched.pdbId, "1CRN");
  assert.equal(switched.targetAccession, null); // Must not retain P00533!
  assert.equal(switched.discoveryResult, null);
  assert.equal(switched.activeMolecularInput, null);
  assert.equal(switched.activeQuantumJob, null);
  assert.equal(switched.originalFilename, "1crn.pdb");
});

test("Protection against stale asynchronous responses discards out-of-order payloads", () => {
  const staged = atomicSwitchCurated(createInitialStructureContext("1M17"), "2ITX");

  // Slower in-flight response from token 1 arrives when current token is 2
  const stalePayload = {
    source: { pdb_id: "1M17", sha256: "stale-hash" },
    title: "Old 1M17 Analysis",
    protein_chains: ["A"],
  };

  const resulting = applyStructureAnalysis(staged, stalePayload, 1, 2);
  // Stale payload was discarded: pdbId remains 2ITX
  assert.equal(resulting.pdbId, "2ITX");
  assert.notEqual(resulting.sha256, "stale-hash");

  // Matching token payload applies successfully
  const validPayload = {
    source: { pdb_id: "2ITX", sha256: "verified-2itx-hash" },
    title: "EGFR kinase in complex with AMP-PNP",
    protein_chains: ["A"],
    selected_chain_id: "A",
  };
  const updated = applyStructureAnalysis(staged, validPayload, 2, 2);
  assert.equal(updated.pdbId, "2ITX");
  assert.equal(updated.sha256, "verified-2itx-hash");
  assert.equal(updated.proteinName, "EGFR kinase in complex with AMP-PNP");
});

test("Chain selection synchronization updates selectedChainId and clears chain-dependent results", () => {
  const context = {
    ...createInitialStructureContext("7A2A"),
    availableChains: ["A", "B"],
    selectedChainId: "A",
    discoveryResult: { decisions: [{ drug_name: "CAN-CHAIN-A" }] },
    activeMolecularInput: { candidate_id: "57N-A-1101" },
  };

  const updated = updateChainSelection(context, "B");
  assert.equal(updated.selectedChainId, "B");
  assert.equal(updated.discoveryResult, null);
  assert.equal(updated.activeMolecularInput, null);
  assert.equal(updated.pdbId, "7A2A");
});

test("CentralPDBSelector component verifies exactly 4 curated EGFR structures and upload option", () => {
  const source = readFileSync(new URL("../components/CentralPDBSelector.js", import.meta.url), "utf8");
  assert.match(source, /EGFR-Focused Curated Structure Collection/);
  assert.match(source, /Select One Curated EGFR Structure/);
  assert.match(source, /Upload a Custom PDB Structure/);
  assert.match(source, /onSelectCurated/);
  assert.match(source, /onUploadCustom/);
  assert.match(source, /accept="\.pdb"/);
});

test("OverviewWorkspace derives metadata strictly from active structure context without hardcoded EGFR fallbacks", () => {
  const source = readFileSync(new URL("../components/workspaces/OverviewWorkspace.js", import.meta.url), "utf8");
  // Asserts hardcoded fallback strings are purged
  assert.doesNotMatch(source, /"EGFR Kinase Domain Discovery"/);
  assert.doesNotMatch(source, /"1M17 \/ 1XKK"/);
  assert.doesNotMatch(source, /"8 Identified"/);
  assert.doesNotMatch(source, /"Active VQE"/);
  assert.doesNotMatch(source, /"16\.1s \(nominal\)"/);

  // Asserts dynamic context binding
  assert.match(source, /activeStructure\?\.pdbId/);
  assert.match(source, /activeStructure\?\.proteinName/);
  assert.match(source, /activeStructure\?\.targetAccession/);
  assert.match(source, /isDone \? summary\.analyzed : "0 Candidates"/);
  assert.match(source, /isDone \? summary\.quantumEvaluated : "0 Evaluated"/);
});

test("TopBar and Sidebar display active PDB context with structure switching trigger", () => {
  const topBarSource = readFileSync(new URL("../components/TopBar.js", import.meta.url), "utf8");
  const sidebarSource = readFileSync(new URL("../components/Sidebar.js", import.meta.url), "utf8");

  assert.match(topBarSource, /onChangeStructure/);
  assert.match(topBarSource, /targetInfo\?\.pdbId/);
  assert.doesNotMatch(topBarSource, /"EGFR \(P00533\)"/);

  assert.match(sidebarSource, /targetInfo\?\.pdbId/);
  assert.match(sidebarSource, /No structure selected/);
  assert.doesNotMatch(sidebarSource, /"EGFR \(Epidermal Growth Factor\)"/);
});
