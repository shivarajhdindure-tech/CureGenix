const parsePdb = require('./parse-pdb');
const { toOneLetter } = require('./amino-acids');

// ─────────────────────────────────────────────────────────────────────────────
// Constants
// ─────────────────────────────────────────────────────────────────────────────

const BINDING_SITE_CUTOFF = 5.0;
const WATER_NAMES = new Set(['HOH', 'WAT', 'H2O', 'DOD', 'DIS']);

// ─────────────────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────────────────

function atomDist(a, b) {
  const dx = a.x - b.x;
  const dy = a.y - b.y;
  const dz = a.z - b.z;
  return Math.sqrt(dx * dx + dy * dy + dz * dz);
}

/**
 * Build a single merged amino-acid sequence from all chains.
 * Also returns per-chain sequences for reference.
 */
function buildSequence(parsed) {
  const perChain = {};

  if (parsed.seqRes.length > 0) {
    parsed.seqRes.forEach(entry => {
      if (!perChain[entry.chainID]) perChain[entry.chainID] = '';
      entry.resNames.forEach(rn => {
        perChain[entry.chainID] += toOneLetter(rn);
      });
    });
  } else {
    // Fallback: derive from CA atoms
    const seen = new Set();
    parsed.atoms.forEach(atom => {
      if (atom.name !== 'CA') return;
      const key = `${atom.chainID}:${atom.resSeq}`;
      if (seen.has(key)) return;
      seen.add(key);
      if (!perChain[atom.chainID]) perChain[atom.chainID] = '';
      perChain[atom.chainID] += toOneLetter(atom.resName);
    });
  }

  // Merge all chains into one sequence (AlphaFold queries use full sequence)
  const sequence = Object.values(perChain).join('');
  return { sequence, perChain };
}

/**
 * Extract CA-only coordinates: one {x,y,z} per residue.
 */
function extractCACoords(parsed) {
  const coords = [];
  const seen = new Set();

  parsed.atoms.forEach(atom => {
    if (atom.name !== 'CA') return;
    const key = `${atom.chainID}:${atom.resSeq}`;
    if (seen.has(key)) return;
    seen.add(key);
    coords.push({
      chain:   atom.chainID,
      resSeq:  atom.resSeq,
      resName: atom.resName,
      x: Math.round(atom.x * 100) / 100,
      y: Math.round(atom.y * 100) / 100,
      z: Math.round(atom.z * 100) / 100,
    });
  });

  return coords;
}

/**
 * Detect binding-site residues within cutoff Å of any ligand atom.
 */
function detectBindingSites(parsed, cutoff) {
  const ligandAtoms = parsed.hetatms.filter(a => !WATER_NAMES.has(a.resName));
  if (ligandAtoms.length === 0) return [];

  // Group ligand atoms by identity
  const groups = new Map();
  ligandAtoms.forEach(la => {
    const key = `${la.resName}:${la.chainID}:${la.resSeq}`;
    if (!groups.has(key)) {
      groups.set(key, { name: la.resName, chain: la.chainID, atoms: [] });
    }
    groups.get(key).atoms.push(la);
  });

  const sites = [];
  groups.forEach(group => {
    const nearby = new Set();
    group.atoms.forEach(la => {
      parsed.atoms.forEach(pa => {
        if (atomDist(la, pa) <= cutoff) {
          nearby.add(`${pa.chainID}:${pa.resSeq}`);
        }
      });
    });

    if (nearby.size > 0) {
      const byChain = new Map();
      nearby.forEach(key => {
        const [chain, resSeqStr] = key.split(':');
        if (!byChain.has(chain)) byChain.set(chain, []);
        byChain.get(chain).push(parseInt(resSeqStr, 10));
      });

      byChain.forEach((residues, chain) => {
        sites.push({
          chain,
          residues: residues.sort((a, b) => a - b),
          ligand: group.name,
        });
      });
    }
  });

  return sites;
}

/**
 * Extract AlphaFold pLDDT confidence from B-factor column.
 */
function extractConfidence(parsed, isAlphaFold) {
  if (!isAlphaFold) return null;

  const plddt = [];
  const seen = new Set();

  parsed.atoms.forEach(atom => {
    if (atom.name !== 'CA') return;
    const key = `${atom.chainID}:${atom.resSeq}`;
    if (seen.has(key)) return;
    seen.add(key);
    plddt.push(atom.tempFactor);
  });

  if (plddt.length === 0) return null;

  const avg = Math.round((plddt.reduce((s, v) => s + v, 0) / plddt.length) * 10) / 10;

  // Low-confidence regions (pLDDT < 50)
  const lowRegions = [];
  let start = null;
  plddt.forEach((v, i) => {
    if (v < 50) {
      if (start === null) start = i + 1;
    } else {
      if (start !== null) {
        lowRegions.push([start, i]);
        start = null;
      }
    }
  });
  if (start !== null) lowRegions.push([start, plddt.length]);

  return {
    avg_plddt: avg,
    low_confidence_regions: lowRegions,
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// Main — AlphaFold-query-compatible output
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Extract a normalized, AlphaFold-query-compatible summary from a PDB string.
 *
 * Output schema:
 * {
 *   input_type: "pdb_upload",
 *   protein: { name, chains, sequence, sequence_length },
 *   structure_summary: { residue_count, ca_coordinates, binding_sites },
 *   metadata: { source, confidence }
 * }
 *
 * @param {string} pdbString
 * @param {Object} [options]
 * @param {string} [options.source]        - 'alphafold' | 'pdb_upload' | 'rcsb' etc.
 * @param {number} [options.bindingCutoff] - Å cutoff for binding sites (default: 5.0)
 * @returns {Object}
 */
function extractSummary(pdbString, options) {
  const opts = options || {};
  const parsed = parsePdb(pdbString);

  // Chains
  const chainIDs = [];
  parsed.chains.forEach((_, key) => chainIDs.push(key));

  // Sequence
  const { sequence } = buildSequence(parsed);

  // CA backbone
  const caCoords = extractCACoords(parsed);

  // Binding sites
  const cutoff = opts.bindingCutoff || BINDING_SITE_CUTOFF;
  const bindingSites = detectBindingSites(parsed, cutoff);

  // Confidence
  const isAlphaFold = (opts.source === 'alphafold') ||
    parsed.remarks.some(r => /alphafold/i.test(r));
  const confidence = extractConfidence(parsed, isAlphaFold);

  // Protein name from HEADER, COMPND, or TITLE
  let name = parsed.header ? parsed.header.classification : null;
  const molMatch = pdbString.match(/COMPND\s+\d*\s*MOLECULE:\s*(.*?);/i);
  if (molMatch && molMatch[1]) {
    name = molMatch[1].trim();
  } else {
    const titleMatch = pdbString.match(/TITLE\s+(.*)/i);
    if (titleMatch && titleMatch[1]) {
      name = titleMatch[1].trim();
    }
  }

  // Source
  const source = opts.source || 'uploaded_pdb';

  return {
    input_type: 'pdb_upload',

    protein: {
      name,
      chains:          chainIDs,
      sequence,
      sequence_length: sequence.length,
    },

    structure_summary: {
      residue_count:   caCoords.length,
      ca_coordinates:  caCoords,
      binding_sites:   bindingSites,
    },

    metadata: {
      source,
      confidence,
      protein_id: parsed.header ? parsed.header.idCode : null,
    },
  };
}

module.exports = extractSummary;
