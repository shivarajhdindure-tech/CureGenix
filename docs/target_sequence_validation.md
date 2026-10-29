# PDB chain-to-UniProt sequence validation

## Evidence flow

The upload path extracts a sequence from observed coordinate records on each
PDB chain and stores it with the chain-specific `DBREF` evidence. `TargetAgent`
first requires an explicit chain when more than one chain is present, then
retrieves the exact DBREF or user-selected UniProt accession. It validates the
accession response and, for a DBREF-linked accession, aligns the selected
chain's observed sequence to the UniProt sequence. The resulting evidence is
kept under `target_identity.sequence_validation`, returned by the orchestrator,
and copied into generated-candidate provenance, screening, ranking, and the
results evidence display.

A user-entered accession that resolves remains `externally_verified`; matching
sequence alone does not change that state to structure-linked. Generation
requires a chain-specific PDB `DBREF`, exact primary-accession lookup, a
selected chain, and one of the accepted sequence-validation outcomes below.
This is sequence correspondence evidence only. It does not establish biological
function, binding-pocket validity, ligand binding, docking accuracy, affinity,
or therapeutic efficacy.

## Observed-residue policy

Only coordinate residues are counted. Standard amino-acid names map to their
one-letter codes. A fixed, documented set of common modified residues is
normalized (including MSE to M and SEP to S); a `MODRES` parent mapping to a
standard residue takes precedence for other modified residues. Unknown observed
residues are represented as `X`. `SEQRES` can identify an otherwise unknown
`HETATM` coordinate residue as polymer, but never creates an observed residue.
Unrecognized `HETATM` records that are not declared as polymer are reported as
ignored heterogens because PDB records alone do not reliably distinguish an
unknown modified amino acid from a ligand in that case.

Alternate conformations count once per residue identifier. The selected
variant is the one with highest mean atom occupancy, then atom count, then a
tie preference for blank, `A`, and other alternate-location labels. Insertion
codes are included in residue identity and reported. Numbering gaps are
reported without filling in or guessing missing residues. For multi-model PDBs,
only the first coordinate model is used. Blank chain IDs are represented as
`_` in evidence.

## Alignment and denominators

The extractor uses affine-gap Gotoh alignment in semi-global mode: the complete
observed chain is aligned against a substring of the full UniProt sequence, so
unobserved reference termini do not incur gap penalties. Default scores are
match `+2`, mismatch `-2`, gap-open `-5`, and gap-extension `-1`. Alignments
above 8,000,000 matrix cells fail closed. Substitutions, internal insertions
and deletions, unaligned termini, and PDB residue identifiers are retained in
the evidence rather than normalized away.

The reported identity denominator is aligned residue/residue columns with
informative amino acids (the canonical 20 plus U and O); X, B, Z, and J are
excluded from both numerator and denominator. Observed-chain coverage divides
informative aligned pairs by every observed coordinate residue, including X.
Reference coverage divides informative aligned pairs by the complete verified
UniProt sequence length. Thus identity is always presented with both coverage
values, and a short perfect fragment cannot pass on identity alone.

## Prototype acceptance policy

Defaults are intentionally conservative starting values, not universal
biological identity cutoffs:

- Minimum identity: 90% of informative aligned pairs.
- Minimum observed-chain coverage: 80%.
- Minimum full-reference coverage: 15%.
- Minimum informative aligned length: 100 residues.
- Maximum internal gap fraction: 10% of aligned informative residues plus
  gap residues.
- Full validation additionally requires full reference coverage, complete
  informative identity, no internal indels, full observed coverage, and no X.

The combination of length, identity, observed coverage, reference coverage,
and gap limits is intended to prevent a weak coincidental fragment from
passing because its few aligned residues are identical. A full exact match is
reported as `structure_linked_sequence_validated`. A threshold-passing but
partial or locally different alignment is reported as
`structure_linked_partial_sequence_support`. Both may enable target-informed
generation only when the accession is DBREF-linked to the explicitly selected
chain. Sequence disagreement is `sequence_mismatch`; missing, malformed,
short, or computationally bounded evidence is
`insufficient_sequence_evidence`. Ambiguous, unresolved, externally verified,
or conflicting identity states remain ineligible.

Every threshold is configurable through `CUREGENIX_SEQUENCE_*` environment
settings and the policy object. The defaults have not been calibrated against
a representative collection of engineered constructs, isoforms, homologs, or
PDB annotation errors. In particular, DBREF1/DBREF2 accession resolution is
not implemented, and no live UniProt lookup was performed as part of the test
suite.
