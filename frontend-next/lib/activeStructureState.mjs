/**
 * Global Active Structure State management and atomic transition logic.
 *
 * Enforces atomic clearing of stale discovery, candidate, and quantum calculation
 * state upon structure switching, and prevents race conditions from out-of-order
 * asynchronous responses.
 */

export function createInitialStructureContext(pdbId = "1M17") {
  return {
    structureSource: "curated",
    pdbId: pdbId,
    uploadId: null,
    sha256: "",
    fileUrl: `/api/structures/curated/${pdbId}/file`,
    sourceUrl: `https://files.rcsb.org/download/${pdbId}.pdb`,
    proteinName: "Epidermal growth factor receptor (EGFR)",
    targetAccession: "P00533",
    availableChains: ["A"],
    selectedChainId: "A",
    sequenceValidation: null,
    structureAnalysisRecordId: pdbId,
    discoveryResult: null,
    candidateGenerationStatus: null,
    coCrystallizedLigands: [],
    activeMolecularInput: null,
    activeQuantumJob: null,
    validationStatus: "valid",
    warnings: [],
    mutationAnnotations: [],
  };
}

/**
 * Atomically clear downstream discovery and calculation states when switching to a curated PDB.
 */
export function atomicSwitchCurated(prevContext, newPdbId) {
  return {
    ...(prevContext || {}),
    structureSource: "curated",
    pdbId: newPdbId,
    uploadId: null,
    sha256: "",
    fileUrl: `/api/structures/curated/${newPdbId}/file`,
    sourceUrl: `https://files.rcsb.org/download/${newPdbId}.pdb`,
    proteinName: `Loading ${newPdbId}…`,
    targetAccession: "P00533",
    availableChains: [],
    selectedChainId: "",
    // CRITICAL: Atomic reset of all downstream workspace state
    sequenceValidation: null,
    structureAnalysisRecordId: newPdbId,
    discoveryResult: null,
    candidateGenerationStatus: null,
    coCrystallizedLigands: [],
    activeMolecularInput: null,
    activeQuantumJob: null,
    validationStatus: "checking",
    warnings: [],
    mutationAnnotations: [],
  };
}

/**
 * Atomically clear downstream discovery and calculation states when uploading a custom PDB.
 */
export function atomicSwitchCustom(prevContext, filename) {
  const customId = filename.replace(/\.pdb$/i, "").toUpperCase();
  return {
    ...(prevContext || {}),
    structureSource: "custom",
    pdbId: customId,
    uploadId: null,
    sha256: "",
    fileUrl: "",
    sourceUrl: null,
    proteinName: filename,
    targetAccession: null,
    availableChains: [],
    selectedChainId: "",
    // CRITICAL: Atomic reset of all downstream workspace state
    sequenceValidation: null,
    structureAnalysisRecordId: customId,
    discoveryResult: null,
    candidateGenerationStatus: null,
    coCrystallizedLigands: [],
    activeMolecularInput: null,
    activeQuantumJob: null,
    validationStatus: "checking",
    warnings: [],
    mutationAnnotations: [],
    originalFilename: filename,
  };
}

/**
 * Update chain selection and clear chain-dependent hypotheses and calculations.
 */
export function updateChainSelection(prevContext, newChainId) {
  if (!prevContext) return null;
  return {
    ...prevContext,
    selectedChainId: newChainId,
    // Clear chain-dependent discovery result and calculations
    discoveryResult: null,
    candidateGenerationStatus: null,
    activeMolecularInput: null,
    activeQuantumJob: null,
  };
}

/**
 * Apply fetched structure analysis payload, protecting against stale out-of-order responses.
 */
export function applyStructureAnalysis(prevContext, analysisPayload, expectedToken, currentToken) {
  if (expectedToken !== currentToken) {
    // Stale async response discarded to prevent race condition
    return prevContext;
  }
  const defaultChain = analysisPayload.selected_chain_id || analysisPayload.protein_chains?.[0] || "A";
  return {
    ...prevContext,
    pdbId: analysisPayload.source?.pdb_id || prevContext.pdbId,
    sha256: analysisPayload.source?.sha256 || "",
    sourceUrl: analysisPayload.source?.source_url || prevContext.sourceUrl,
    fileUrl: analysisPayload.source?.file_url || prevContext.fileUrl,
    proteinName: analysisPayload.title || prevContext.proteinName,
    targetAccession: analysisPayload.target_identity?.accession || prevContext.targetAccession,
    availableChains: analysisPayload.protein_chains || ["A"],
    selectedChainId: defaultChain,
    sequenceValidation: analysisPayload.sequence_annotations || null,
    structureAnalysisRecordId: analysisPayload.source?.sha256 || prevContext.pdbId,
    coCrystallizedLigands: analysisPayload.co_crystallized_ligands || [],
    validationStatus: analysisPayload.validation?.status || "valid",
    warnings: analysisPayload.validation?.warnings || [],
    mutationAnnotations: analysisPayload.mutation_annotations || [],
  };
}

export const BENCHMARK_TARGETS = [
  {
    targetId: "BENCHMARK-H2",
    name: "Dihydrogen (H₂)",
    type: "benchmark",
    category: "Small-Molecule Benchmark",
    formula: "H2",
    heavyAtoms: 0,
    totalAtoms: 2,
    basisFunctionsEstimate: 2,
    smiles: "[H][H]",
    verificationStatus: "verified_benchmark",
    resourceEligibility: {
      status: "eligible",
      eligible: true,
      reasons: [],
    },
    description: "Minimal 2-qubit benchmark system for VQE ground-state simulation.",
  },
  {
    targetId: "BENCHMARK-H2O",
    name: "Water (H₂O)",
    type: "benchmark",
    category: "Small-Molecule Benchmark",
    formula: "H2O",
    heavyAtoms: 1,
    totalAtoms: 3,
    basisFunctionsEstimate: 7,
    smiles: "O",
    verificationStatus: "verified_benchmark",
    resourceEligibility: {
      status: "eligible",
      eligible: true,
      reasons: [],
    },
    description: "Standard 4e/4o active-space benchmark molecule with PySCF Jordan–Wigner mapping.",
  },
];

/**
 * Extract unified calculation targets from active structure, discovery candidates, and benchmarks.
 */
export function extractCalculationTargets(activeStructure, derived = null) {
  const targets = [];

  // 1. Co-crystallized ligands extracted from active PDB
  const coCryst = activeStructure?.coCrystallizedLigands || [];
  for (const lig of coCryst) {
    if (lig.is_drug_candidate || lig.category === "co_crystallized_ligand") {
      const isChainMatched = !activeStructure?.selectedChainId || lig.chain_id === activeStructure.selectedChainId;
      targets.push({
        targetId: lig.ligand_id || `${lig.component_id}-${lig.chain_id}-${lig.residue_number}`,
        name: lig.name || `Ligand ${lig.component_id}`,
        chemicalName: lig.chemical_name || null,
        type: "co_crystallized_ligand",
        category: `Co-Crystallized Ligand (${activeStructure?.pdbId || "PDB"})`,
        sourcePdbId: activeStructure?.pdbId || "",
        chainId: lig.chain_id || "",
        residueNumber: lig.residue_number || "",
        componentId: lig.component_id || "",
        formula: lig.formula || "",
        heavyAtoms: lig.heavy_atom_count ?? null,
        totalAtoms: lig.observed_atom_count ?? null,
        basisFunctionsEstimate: lig.resource_preflight?.resource_metrics?.estimated_sto3g_basis_functions ?? null,
        smiles: lig.smiles || null,
        molecularWeight: lig.molecular_weight || null,
        verificationStatus: lig.verification_status || "unverified_raw_pdb_coordinates",
        ccdSource: lig.ccd_source || null,
        role: lig.role || null,
        isChainMatched,
        resourceEligibility: lig.resource_preflight || {
          status: "unverified",
          reasons: ["Verification preflight not available."],
        },
      });
    }
  }

  // 2. Generated candidates / references from discovery pipeline (if available)
  const candidates = derived?.candidates || [];
  for (const c of candidates) {
    const heavyAtoms = c.heavyAtoms ?? c.screening?.heavyAtoms ?? null;
    targets.push({
      targetId: c.id,
      name: c.name || c.id,
      type: c.isNovel ? "novel_candidate" : "reference_compound",
      category: c.isNovel ? "Discovery Candidate" : "Curated Reference",
      sourcePdbId: activeStructure?.pdbId || "",
      chainId: activeStructure?.selectedChainId || "",
      formula: c.formula || "",
      heavyAtoms: heavyAtoms,
      totalAtoms: null,
      basisFunctionsEstimate: null,
      smiles: c.smiles || null,
      molecularWeight: c.screening?.mw ?? null,
      verificationStatus: c.verificationStatus || "candidate",
      resourceEligibility: c.quantum?.resource_eligibility || {
        status: (heavyAtoms ?? 0) > 20 ? "skipped_resource_limit" : "eligible",
        reasons: (heavyAtoms ?? 0) > 20
          ? [`Heavy-atom count ${heavyAtoms} exceeds configured limit 20.`]
          : [],
      },
    });
  }

  // 3. Benchmarks (always available)
  for (const b of BENCHMARK_TARGETS) {
    targets.push({
      ...b,
      sourcePdbId: activeStructure?.pdbId || "BENCHMARK",
      chainId: "",
    });
  }

  return targets;
}

export function setActiveMolecularInput(prevContext, molecularInput) {
  if (!prevContext) return null;
  return {
    ...prevContext,
    activeMolecularInput: molecularInput,
    activeQuantumJob: null,
  };
}

export function setActiveQuantumJob(prevContext, quantumJob) {
  if (!prevContext) return null;
  return {
    ...prevContext,
    activeQuantumJob: quantumJob,
  };
}

