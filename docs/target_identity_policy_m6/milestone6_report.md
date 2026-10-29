# Milestone 6 — Real-World Identity Validation and Safer Generation Gating

## Baseline and revised policy

Milestone 5 baseline is preserved under `baseline/` and was reproduced before this change. Its sequence thresholds and classifications are unchanged. The revised product gate allows exact full sequence correspondence as before. Partial sequence support requires independent RCSB/SIFTS chain-to-UniProt evidence, a PDB ID from the uploaded HEADER, an exact author-chain match, and passing sequence support against the RCSB entity sequence. Externally verified accession alone never authorizes generation.

| Dataset | M5 false accepts | M6 false accepts | M5 false rejects | M6 false rejects |
|---|---:|---:|---:|---:|
| Synthetic constructed scenarios (n=19) | 2 | 0 | 0 | 5 |
| Real source-labeled chain cases (n=4, entries=2) | — | 0 | — | 0 |

Synthetic examples are policy stress tests and are not biological-performance estimates. The existing 1CRN source-conflict diagnostic is excluded from these totals and from the separately curated real-source dataset. Real cases are only two PDB entries (three positive chain records plus one wrong-target negative control), so they are development/evidence checks, not an independent validation cohort.

## Synthetic false-acceptance cases

M5 false accepts: synthetic_close_homolog_8pct, synthetic_local_match_150_of_500.
M6 false accepts: none.
M6 false rejections against the constructed labels: synthetic_terminal_truncation_60pct, synthetic_engineered_substitutions_3, synthetic_internal_deletion_12, synthetic_internal_insertion_8, synthetic_unknown_residues_10pct.

The close-homolog and short exact-fragment cases have no independent structure-to-target evidence in the synthetic fixtures and are blocked. Partial synthetic cases that were labeled allowable are also blocked absent such evidence; this is the conservative tradeoff and must not be interpreted as calibrated sensitivity.

M5 1CRN source-conflict diagnostic: `real_1crn_chain_a_p01542` remains separately reported in JSON under `diagnostics`; it is not scored because its fixture explicitly records a source conflict.

## Real-source cases

| PDB chain | Supplied accession | DBREF | RCSB/SIFTS | UniProt identity | Reference coverage | Decision | Expected |
|---|---|---|---|---:|---:|---|---|
| 1M17:A | P00533 | DBREF  1M17 A  671   998  UNP    P00533   EGFR_HUMAN     695   1022 | P00533 | 100.00% | 25.8% | allow | allow |
| 3PP0:A | P04626 | DBREF  3PP0 A  706  1009  UNP    P04626   ERBB2_HUMAN    706   1009 | P04626 | 98.95% | 22.8% | allow | allow |
| 3PP0:B | P04626 | DBREF  3PP0 B  706  1009  UNP    P04626   ERBB2_HUMAN    706   1009 | P04626 | 98.99% | 23.6% | allow | allow |
| 3PP0:A | P00533 | DBREF  3PP0 A  706  1009  UNP    P04626   ERBB2_HUMAN    706   1009 | no match | 82.46% | 23.6% | deny | deny |

RCSB PDB/UniProt mapping and PDB SEQADV annotations supply the labels independently of the alignment score. 1M17 is an EGFR kinase-domain construct mapped to P00533; 3PP0 is an engineered HER2 kinase-domain construct with chains A/B mapped to P04626 and documented engineered substitutions. The 3PP0-as-P00533 row is a close-family wrong-target control.

## Reproduction and limitations

Run with `.venv-win\Scripts\python.exe scripts\evaluate_target_identity_policy_m6.py`. Unit tests use deterministic mocked RCSB responses; the versioned files in `real_pdb/` are source snapshots fetched from RCSB and UniProt during manual curation. The application uses the live RCSB Data API only for partial sequence support; network failures, malformed API responses, chain remapping, or accession conflicts fail closed. API availability and the PDB API's author/label chain mapping remain operational limitations.

The real fixture labels and source snapshot checksums are recorded in `real_world_fixture_manifest.json`; the full per-case evaluation is in `milestone6_results.json`.

This policy validates chain-to-target identity evidence only. It does not validate a binding pocket, ligand pose, binding affinity, target engagement, efficacy, or a quantum advantage.

## Sources

- [RCSB 1M17](https://www.rcsb.org/structure/1M17); [RCSB 3PP0](https://www.rcsb.org/structure/3PP0)
- [RCSB Data API](https://data.rcsb.org/)
- [UniProt P00533](https://www.uniprot.org/uniprotkb/P00533/entry); [UniProt P04626](https://www.uniprot.org/uniprotkb/P04626/entry)
