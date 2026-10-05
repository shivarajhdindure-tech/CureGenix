/**
 * Standard 3-letter → 1-letter amino acid code mapping.
 * Includes the 20 standard amino acids plus common non-standard/modified residues.
 */
const THREE_TO_ONE = {
  // 20 standard amino acids
  ALA: 'A', ARG: 'R', ASN: 'N', ASP: 'D', CYS: 'C',
  GLU: 'E', GLN: 'Q', GLY: 'G', HIS: 'H', ILE: 'I',
  LEU: 'L', LYS: 'K', MET: 'M', PHE: 'F', PRO: 'P',
  SER: 'S', THR: 'T', TRP: 'W', TYR: 'Y', VAL: 'V',

  // Common non-standard / modified residues
  SEC: 'U',  // Selenocysteine
  PYL: 'O',  // Pyrrolysine
  ASX: 'B',  // Asparagine or Aspartic acid
  GLX: 'Z',  // Glutamine or Glutamic acid
  XLE: 'J',  // Leucine or Isoleucine
  XAA: 'X',  // Unknown
  MSE: 'M',  // Selenomethionine (treated as Met)
  HSD: 'H',  // Histidine (CHARMM naming)
  HSE: 'H',  // Histidine (CHARMM naming)
  HSP: 'H',  // Histidine protonated
  CYX: 'C',  // Cystine (disulfide-bonded cysteine)
};

/**
 * Convert a 3-letter residue name to its 1-letter code.
 * Returns 'X' for unknown residues.
 * @param {string} threeLetterCode
 * @returns {string} single character
 */
function toOneLetter(threeLetterCode) {
  return THREE_TO_ONE[threeLetterCode.toUpperCase()] || 'X';
}

/**
 * Check if a 3-letter code corresponds to a standard amino acid.
 * @param {string} threeLetterCode
 * @returns {boolean}
 */
function isAminoAcid(threeLetterCode) {
  return threeLetterCode.toUpperCase() in THREE_TO_ONE;
}

module.exports = { THREE_TO_ONE, toOneLetter, isAminoAcid };
