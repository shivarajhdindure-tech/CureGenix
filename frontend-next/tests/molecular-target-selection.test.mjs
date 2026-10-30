import test from "node:test";
import assert from "node:assert/strict";

import {
  extractCalculationTargets,
  setActiveMolecularInput,
  setActiveQuantumJob,
  BENCHMARK_TARGETS,
  createInitialStructureContext,
  atomicSwitchCurated,
  updateChainSelection,
} from "../lib/activeStructureState.mjs";

test("extractCalculationTargets includes benchmarks and extracts co-crystallized ligands from active structure", () => {
  const mockActiveStructure = {
    pdbId: "1M17",
    selectedChainId: "A",
    coCrystallizedLigands: [
      {
        ligand_id: "AQ4-A-999",
        component_id: "AQ4",
        chain_id: "A",
        residue_number: "999",
        name: "Erlotinib",
        formula: "C22H23N3O4",
        heavy_atom_count: 29,
        observed_atom_count: 29,
        smiles: "COCCOc1cc2ncnc(Nc3cccc(c3)C#C)c2cc1OCCOC",
        molecular_weight: 393.443,
        verification_status: "verified_ccd",
        is_drug_candidate: true,
        resource_preflight: {
          status: "skipped_resource_limit",
          eligible: false,
          reasons: [
            "Heavy-atom count 29 exceeds configured limit 20.",
            "Estimated STO-3G basis-function count 168 exceeds configured limit 100.",
          ],
          resource_metrics: {
            heavy_atom_count: 29,
            estimated_sto3g_basis_functions: 168,
          },
        },
      },
      {
        ligand_id: "HOH-A-1",
        component_id: "HOH",
        chain_id: "A",
        is_drug_candidate: false,
      },
    ],
  };

  const targets = extractCalculationTargets(mockActiveStructure);

  // Benchmarks must always be present
  assert.ok(targets.some((t) => t.targetId === "BENCHMARK-H2" && t.type === "benchmark"));
  assert.ok(targets.some((t) => t.targetId === "BENCHMARK-H2O" && t.type === "benchmark"));

  // Extracted drug-candidate ligand AQ4 must be present; solvent HOH must be excluded
  const aq4 = targets.find((t) => t.targetId === "AQ4-A-999");
  assert.ok(aq4, "AQ4-A-999 must be present");
  assert.equal(aq4.name, "Erlotinib");
  assert.equal(aq4.heavyAtoms, 29);
  assert.equal(aq4.resourceEligibility.status, "skipped_resource_limit");
  assert.equal(aq4.resourceEligibility.reasons.length, 2);
  assert.equal(aq4.isChainMatched, true);

  assert.ok(!targets.some((t) => t.targetId === "HOH-A-1"), "Solvent HOH should not be in drug targets");
});

test("Curated EGFR ligands accurately report honest resource preflight skips (>20 heavy atoms)", () => {
  const curatedCases = [
    { pdbId: "1M17", comp: "AQ4", heavy: 29 },
    { pdbId: "2ITX", comp: "ANP", heavy: 31 },
    { pdbId: "4G5J", comp: "0WN", heavy: 34 },
    { pdbId: "7A2A", comp: "57N", heavy: 25 },
    { pdbId: "7A2A", comp: "7G9", heavy: 31 },
  ];

  for (const c of curatedCases) {
    const mockStructure = {
      pdbId: c.pdbId,
      selectedChainId: "A",
      coCrystallizedLigands: [
        {
          ligand_id: `${c.comp}-A-100`,
          component_id: c.comp,
          chain_id: "A",
          name: `${c.comp} Ligand`,
          heavy_atom_count: c.heavy,
          smiles: "C".repeat(c.heavy),
          verification_status: "verified_ccd",
          is_drug_candidate: true,
          resource_preflight: {
            status: "skipped_resource_limit",
            eligible: false,
            reasons: [`Heavy-atom count ${c.heavy} exceeds configured limit 20.`],
          },
        },
      ],
    };

    const targets = extractCalculationTargets(mockStructure);
    const target = targets.find((t) => t.componentId === c.comp);
    assert.ok(target, `Target ${c.comp} should be extracted`);
    assert.equal(target.resourceEligibility.status, "skipped_resource_limit");
    assert.ok(target.heavyAtoms > 20, "All 4 curated PDB ligands exceed 20 heavy atoms");
    assert.match(target.resourceEligibility.reasons[0], /exceeds configured limit 20/);
  }
});

test("Small-molecule benchmarks H2 and H2O evaluate as eligible without resource skips", () => {
  for (const benchmark of BENCHMARK_TARGETS) {
    assert.equal(benchmark.resourceEligibility.status, "eligible");
    assert.equal(benchmark.resourceEligibility.eligible, true);
    assert.equal(benchmark.resourceEligibility.reasons.length, 0);
    assert.ok(benchmark.heavyAtoms <= 20, "Benchmark molecules must be within 20 heavy-atom limit");
  }
});

test("Unverified raw PDB ligands withhold SMILES and report unverified verification status", () => {
  const mockStructure = {
    pdbId: "CUSTOM",
    selectedChainId: "A",
    coCrystallizedLigands: [
      {
        ligand_id: "UNK-A-1",
        component_id: "UNK",
        chain_id: "A",
        name: "Co-crystallized Ligand UNK",
        heavy_atom_count: 15,
        smiles: null, // Withheld
        verification_status: "unverified_raw_pdb_coordinates",
        is_drug_candidate: true,
        resource_preflight: {
          status: "unverified",
          reasons: ["Molecular connectivity cannot be established from coordinates alone."],
        },
      },
    ],
  };

  const targets = extractCalculationTargets(mockStructure);
  const unk = targets.find((t) => t.targetId === "UNK-A-1");
  assert.ok(unk);
  assert.equal(unk.smiles, null);
  assert.equal(unk.verificationStatus, "unverified_raw_pdb_coordinates");
  assert.equal(unk.resourceEligibility.status, "unverified");
});

test("Molecular target and job setters update context and atomic switches reset state cleanly", () => {
  let ctx = createInitialStructureContext("1M17");
  assert.equal(ctx.activeMolecularInput, null);
  assert.equal(ctx.activeQuantumJob, null);

  // Set active molecular input
  ctx = setActiveMolecularInput(ctx, { targetId: "AQ4-A-999", name: "Erlotinib" });
  assert.equal(ctx.activeMolecularInput.targetId, "AQ4-A-999");
  assert.equal(ctx.activeQuantumJob, null);

  // Set active quantum job
  ctx = setActiveQuantumJob(ctx, { job_id: "job-123", status: "running" });
  assert.equal(ctx.activeQuantumJob.job_id, "job-123");

  // Atomic switch to another curated structure resets molecular input and job
  const switchedCtx = atomicSwitchCurated(ctx, "2ITX");
  assert.equal(switchedCtx.pdbId, "2ITX");
  assert.equal(switchedCtx.activeMolecularInput, null, "Active molecular input must be reset on PDB switch");
  assert.equal(switchedCtx.activeQuantumJob, null, "Active quantum job must be reset on PDB switch");

  // Chain update also clears active molecular input and job
  ctx = setActiveMolecularInput(ctx, { targetId: "AQ4-A-999" });
  ctx = setActiveQuantumJob(ctx, { job_id: "job-456", status: "completed" });
  const chainUpdated = updateChainSelection(ctx, "B");
  assert.equal(chainUpdated.selectedChainId, "B");
  assert.equal(chainUpdated.activeMolecularInput, null, "Chain switch must reset active molecular input");
  assert.equal(chainUpdated.activeQuantumJob, null, "Chain switch must reset active quantum job");
});
