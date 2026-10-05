const RECORD_ATOM   = 'ATOM  ';
const RECORD_HETATM = 'HETATM';
const RECORD_SEQRES = 'SEQRES';
const RECORD_CONECT = 'CONECT';
const RECORD_MODEL  = 'MODEL ';
const RECORD_ENDMDL = 'ENDMDL';
const RECORD_HEADER = 'HEADER';
const RECORD_REMARK = 'REMARK';

/**
 * Parse a single ATOM or HETATM line into an atom object.
 * Follows the PDB format spec v3.3:
 * http://www.wwpdb.org/documentation/file-format-content/format33/sect9.html#ATOM
 * @param {String} line  - A single PDB line (trailing \r already stripped)
 * @param {Boolean} isHet - Whether this is a HETATM record
 * @returns {Object}
 */
function parseAtomLine(line, isHet) {
  return {
    serial:    parseInt(line.substring(6, 11),  10),
    name:      line.substring(12, 16).trim(),
    altLoc:    line.substring(16, 17).trim(),
    resName:   line.substring(17, 20).trim(),
    chainID:   line.substring(21, 22).trim(),
    resSeq:    parseInt(line.substring(22, 26), 10),
    iCode:     line.substring(26, 27).trim(),
    x:         parseFloat(line.substring(30, 38)),
    y:         parseFloat(line.substring(38, 46)),
    z:         parseFloat(line.substring(46, 54)),
    occupancy: parseFloat(line.substring(54, 60)),
    tempFactor:parseFloat(line.substring(60, 66)),
    element:   line.substring(76, 78).trim(),
    charge:    line.substring(78, 80).trim(),
    isHet:     isHet,
  };
}

/**
 * Parse a CONECT line into a connectivity object.
 * http://www.wwpdb.org/documentation/file-format-content/format33/sect10.html#CONECT
 * @param {String} line
 * @returns {Object} { serial, bonded: [] }
 */
function parseConectLine(line) {
  const parse = (s, e) => {
    const v = parseInt(line.substring(s, e), 10);
    return isNaN(v) ? null : v;
  };
  return {
    serial: parse(6, 11),
    bonded: [parse(11, 16), parse(16, 21), parse(21, 26), parse(26, 31)].filter(v => v !== null),
  };
}

/**
 * Build unique residues from a list of atoms (used when no SEQRES records exist,
 * e.g. small molecule PDB files).
 * @param {Array} atoms
 * @returns {Array}
 */
function deriveResiduesFromAtoms(atoms) {
  const seen = new Map(); // key: "chainID:resSeq:resName"
  const residues = [];
  atoms.forEach(atom => {
    const key = `${atom.chainID}:${atom.resSeq}:${atom.resName}`;
    if (!seen.has(key)) {
      seen.set(key, residues.length);
      residues.push({
        id:      residues.length,
        serNum:  atom.resSeq,
        chainID: atom.chainID,
        resName: atom.resName,
        atoms:   [],
      });
    }
    residues[seen.get(key)].atoms.push(atom);
  });
  return residues;
}

/**
 * Parses the given PDB string into a JSON-friendly object.
 *
 * Supports record types:
 *   ATOM, HETATM, SEQRES, CONECT, MODEL/ENDMDL, HEADER, REMARK
 *
 * @param {String} pdb  - Raw PDB file content
 * @returns {Object}
 */
module.exports = function parsePdb(pdb) {
  const atoms    = [];   // ATOM records
  const hetatms  = [];   // HETATM records
  const seqRes   = [];   // raw SEQRES entries
  const conect   = [];   // CONECT entries
  const models   = [];   // MODEL numbers found
  const remarks  = [];   // REMARK text lines
  let   header   = null; // HEADER record
  let   residues = [];   // derived from SEQRES (or atoms if no SEQRES)
  const chains   = new Map();

  let currentModel = null;

  const pdbLines = pdb.split('\n');

  pdbLines.forEach(rawLine => {
    // Strip Windows-style carriage return so substring offsets stay correct
    const line = rawLine.replace(/\r$/, '');
    if (line.length < 6) return;

    const record = line.substring(0, 6);

    // ── ATOM / HETATM ──────────────────────────────────────────────────────────
    if (record === RECORD_ATOM || record === RECORD_HETATM) {
      const isHet = record === RECORD_HETATM;
      const atom  = parseAtomLine(line, isHet);
      if (currentModel !== null) atom.model = currentModel;
      if (isHet) {
        hetatms.push(atom);
      } else {
        atoms.push(atom);
      }

    // ── SEQRES ─────────────────────────────────────────────────────────────────
    } else if (record === RECORD_SEQRES) {
      // http://www.wwpdb.org/documentation/file-format-content/format33/sect3.html#SEQRES
      const resNamesRaw = line.substring(19, 70).trim();
      // Remove multiple spaces (some files pad with extra spaces between residue names)
      const resNamesArr = resNamesRaw.split(/\s+/).filter(Boolean);
      const entry = {
        serNum:   parseInt(line.substring(7, 10), 10),
        chainID:  line.substring(11, 12).trim(),
        numRes:   parseInt(line.substring(13, 17), 10),
        resNames: resNamesArr,
      };
      seqRes.push(entry);

      // Build flat residue list
      entry.resNames.forEach(resName => {
        const id = residues.length;
        residues.push({
          id,
          serNum:  entry.serNum,
          chainID: entry.chainID,
          resName,
        });
      });

      // Register chain
      if (!chains.has(entry.chainID)) {
        chains.set(entry.chainID, {
          id:      chains.size,
          chainID: entry.chainID,
        });
      }

    // ── CONECT ─────────────────────────────────────────────────────────────────
    } else if (record === RECORD_CONECT) {
      const c = parseConectLine(line);
      if (c.serial !== null) conect.push(c);

    // ── MODEL / ENDMDL ─────────────────────────────────────────────────────────
    } else if (record === RECORD_MODEL) {
      currentModel = parseInt(line.substring(6).trim(), 10);
      if (!models.includes(currentModel)) models.push(currentModel);
    } else if (line.startsWith(RECORD_ENDMDL)) {
      currentModel = null;

    // ── HEADER ─────────────────────────────────────────────────────────────────
    } else if (record === RECORD_HEADER) {
      header = {
        classification: line.substring(10, 50).trim(),
        depDate:        line.substring(50, 59).trim(),
        idCode:         line.substring(62, 66).trim(),
      };

    // ── REMARK ─────────────────────────────────────────────────────────────────
    } else if (record === RECORD_REMARK) {
      remarks.push(line.substring(6).trim());
    }
  });

  // ── If no SEQRES, derive residues + chains from ATOM + HETATM records ────────
  if (seqRes.length === 0) {
    residues = deriveResiduesFromAtoms([...atoms, ...hetatms]);
    residues.forEach(residue => {
      if (!chains.has(residue.chainID)) {
        chains.set(residue.chainID, {
          id:      chains.size,
          chainID: residue.chainID,
        });
      }
    });
    // Attach residues to chains
    chains.forEach(chain => {
      chain.residues = residues.filter(r => r.chainID === chain.chainID);
    });
  } else {
    // ── Add residues to chains (protein path) ──────────────────────────────────
    chains.forEach(chain => {
      chain.residues = residues.filter(r => r.chainID === chain.chainID);
    });

    // ── Add atoms to residues (protein path) ───────────────────────────────────
    residues.forEach(residue => {
      residue.atoms = atoms.filter(
        atom => atom.chainID === residue.chainID && atom.resSeq === residue.serNum,
      );
    });
  }

  return {
    // Core coordinate records
    atoms,      // ATOM records only
    hetatms,    // HETATM records (ligands, water, small molecules)
    // Sequence / topology
    seqRes,     // raw SEQRES entries
    residues,   // derived residue objects (from SEQRES or atoms)
    chains,     // Map<chainID, chain>
    // Connectivity
    conect,     // CONECT bond records
    // Metadata
    models,     // MODEL numbers (empty array = single-model file)
    header,     // HEADER record (or null)
    remarks,    // REMARK lines
  };
};
