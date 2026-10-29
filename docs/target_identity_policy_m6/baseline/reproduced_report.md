# Target identity policy evaluation

## Scope and provenance

This reproducible evaluation combines deterministic synthetic sequence scenarios with one existing real PDB file. Synthetic relationships are known only because each sequence was constructed by the stated transformation; they are not validated biological labels. The 1CRN real-structure record has conflicting engineering annotations and is shown separately, not scored as biological ground truth.

Fixture manifest: `docs/target_identity_policy_fixtures.json` (version 1.0.0).
Cases: 20 total; 19 synthetic scenarios scored; 1 real/source-conflict diagnostic excluded from performance totals.

The real fixture is repository-local `1crn.pdb`, RCSB PDB 1CRN chain A, with DBREF accession P01542. The official RCSB chain FASTA and UniProt P01542 canonical sequence were checked on 2026-10-26. The coordinate chain has Ile at position 25 while the canonical sequence has Leu. Local PDB COMPND records `ENGINEERED: YES`; the RCSB entry summary says `Mutation(s): No`. This conflict is retained, not resolved by assumption.

Sources: [RCSB 1CRN entry](https://www.rcsb.org/structure/1CRN), [RCSB 1CRN chain FASTA](https://www.rcsb.org/fasta/entry/1CRN/display), [UniProt P01542](https://www.uniprot.org/uniprotkb/P01542/entry). No project test makes a live network call; the fixture sequence is stored in the manifest.

## Policy evaluated

The evaluator uses explicit `SequenceValidationPolicy()` defaults, not environment overrides: 90% identity, 80% observed-chain coverage, 15% full-reference coverage, at least 100 informative aligned residues, and at most 10% internal-gap fraction. Alignment is affine-gap semi-global Gotoh (match +2, mismatch -2, gap-open -5, gap-extension -1), aligning the full observed chain to a substring of the reference.

Identity is identical informative residue/residue columns divided by informative aligned residue/residue columns (X/B/Z/J excluded). Observed coverage divides informative aligned pairs by all observed coordinate residues, including X. Reference coverage divides informative aligned pairs by the full reference sequence length. A result only enables generation after selected-chain DBREF linkage and exact accession lookup; external accession matches remain disabled.

## Synthetic decision results

Decision counts on 19 synthetic scenarios: 8 expected allows, 9 expected rejections, 2 false acceptances, and 0 false rejections. These are fixture counts, not biological performance estimates.

| Case | Category | Predicted state | Identity (informative n) | Observed coverage | Reference coverage | Gaps / substitutions | Sequence gate | Expected / actual generation | Scenario result |
|---|---|---|---:|---:|---:|---|---:|---:|---|
| `synthetic_exact_full_length` | exact/full-length | `structure_linked_sequence_validated` | 100.0% (n=500) | 100.0% | 100.0% | 0 ins / 0 del; 0 subst. | true | true / true | expected_allowance |
| `synthetic_terminal_truncation_60pct` | partial construct/terminal truncation | `structure_linked_partial_sequence_support` | 100.0% (n=300) | 100.0% | 60.0% | 0 ins / 0 del; 0 subst. | true | true / true | expected_allowance |
| `synthetic_engineered_substitutions_3` | engineered substitutions | `structure_linked_partial_sequence_support` | 99.4% (n=500) | 100.0% | 100.0% | 0 ins / 0 del; 3 subst. | true | true / true | expected_allowance |
| `synthetic_internal_deletion_12` | internal deletion/missing coordinates | `structure_linked_partial_sequence_support` | 100.0% (n=488) | 100.0% | 97.6% | 0 ins / 12 del; 0 subst. | true | true / true | expected_allowance |
| `synthetic_internal_insertion_8` | internal insertion | `structure_linked_partial_sequence_support` | 100.0% (n=500) | 98.4% | 100.0% | 8 ins / 0 del; 0 subst. | true | true / true | expected_allowance |
| `synthetic_close_homolog_8pct` | close homolog risk | `structure_linked_partial_sequence_support` | 91.6% (n=500) | 100.0% | 100.0% | 0 ins / 0 del; 42 subst. | true | false / true | false_acceptance |
| `synthetic_homolog_16pct` | homolog rejection control | `sequence_mismatch` | 83.4% (n=500) | 100.0% | 100.0% | 0 ins / 0 del; 83 subst. | false | false / false | expected_rejection |
| `synthetic_local_match_150_of_500` | low-coverage coincidental match | `structure_linked_partial_sequence_support` | 100.0% (n=150) | 100.0% | 30.0% | 0 ins / 0 del; 0 subst. | true | false / true | false_acceptance |
| `synthetic_local_match_60_of_500` | short local match | `insufficient_sequence_evidence` | 100.0% (n=60) | 100.0% | 12.0% | 0 ins / 0 del; 0 subst. | false | false / false | expected_rejection |
| `synthetic_unrelated_sequence` | unrelated sequence | `insufficient_sequence_evidence` | 52.1% (n=73) | 14.6% | 14.6% | 427 ins / 0 del; 35 subst. | false | false / false | expected_rejection |
| `synthetic_unknown_residues_10pct` | unknown residues | `structure_linked_partial_sequence_support` | 100.0% (n=450) | 90.0% | 90.0% | 0 ins / 0 del; 0 subst. | true | true / true | expected_allowance |
| `synthetic_recognized_mse` | modified residues | `structure_linked_sequence_validated` | 100.0% (n=500) | 100.0% | 100.0% | 0 ins / 0 del; 0 subst. | true | true / true | expected_allowance |
| `synthetic_blank_chain_id` | blank chain identifier | `structure_linked_sequence_validated` | 100.0% (n=500) | 100.0% | 100.0% | 0 ins / 0 del; 0 subst. | true | true / true | expected_allowance |
| `synthetic_reference_conflict` | DBREF/sequence conflict | `insufficient_sequence_evidence` | 52.1% (n=73) | 14.6% | 14.6% | 427 ins / 0 del; 35 subst. | false | false / false | expected_rejection |
| `synthetic_multiple_chains` | multiple-chain ambiguity | `ambiguous` | — (n=0) | — | — | 0 ins / 0 del; 0 subst. | false | false / false | expected_rejection |
| `synthetic_conflicting_dbref` | conflicting DBREF | `ambiguous` | — (n=0) | — | — | 0 ins / 0 del; 0 subst. | false | false / false | expected_rejection |
| `synthetic_missing_dbref_external_accession` | missing DBREF/user accession | `externally_verified` | 100.0% (n=500) | 100.0% | 100.0% | 0 ins / 0 del; 0 subst. | false | false / false | expected_rejection |
| `synthetic_unsupported_dbref1_dbref2` | unsupported DBREF1/DBREF2 | `externally_verified` | 100.0% (n=500) | 100.0% | 100.0% | 0 ins / 0 del; 0 subst. | false | false / false | expected_rejection |
| `synthetic_missing_dbref_no_accession` | missing DBREF/no accession | `unresolved` | — (n=0) | — | — | 0 ins / 0 del; 0 subst. | false | false / false | expected_rejection |
| `real_1crn_chain_a_p01542` | real structure diagnostic | `insufficient_sequence_evidence` | 97.8% (n=46) | 100.0% | 100.0% | 0 ins / 0 del; 1 subst. | false | false / false | diagnostic_only |

## False-acceptance and rejection analysis

- **False acceptance in synthetic scenario `synthetic_close_homolog_8pct`:** distinct synthetic homolog-like sequence with about 8% substitutions; not the mapped sequence by construction. The policy reported structure_linked_partial_sequence_support with 100.0% reference coverage and enabled generation.
- **False acceptance in synthetic scenario `synthetic_local_match_150_of_500`:** only a 150-residue local segment is shared by construction; remainder is unobserved. The policy reported structure_linked_partial_sequence_support with 30.0% reference coverage and enabled generation.
- No false rejections occurred among synthetic scenarios labeled as generation-eligible.

State-label differences (generation remained disabled where expected):
- `synthetic_unrelated_sequence`: expected `sequence_mismatch`, observed `insufficient_sequence_evidence`; 73 informative pairs, 52.1% identity, 14.6% reference coverage.
- `synthetic_reference_conflict`: expected `sequence_mismatch`, observed `insufficient_sequence_evidence`; 73 informative pairs, 52.1% identity, 14.6% reference coverage.
- **Real 1CRN diagnostic:** the default policy rejects sequence support as `insufficient_sequence_evidence` because the observed chain has only 46 residues, below the 100-residue minimum. P01542 also has no configured candidate reference in the current generator, so the product-level generation gate is disabled. A diagnostic evaluation using a 40-residue minimum reports 97.8% identity, 1 substitution(s), 100.0% observed coverage, and 100.0% reference coverage. That custom-threshold result is not the production decision.

## Calibration decision

No thresholds changed. The synthetic cases expose clear failure modes: an exact 150-residue local fragment from a 500-residue reference can pass the 15% reference-coverage and 100-residue floors, and a synthetic sequence with about 8% substitutions can pass at over 90% identity. These are intentionally constructed risks, not prevalence estimates. Raising thresholds based on this tiny synthetic set would overfit and could reject valid domains or engineered constructs; the defaults remain prototype settings and generation should not be described as biologically validated.

The 1CRN result also shows that accession linkage plus high sequence correspondence does not resolve engineered-construct metadata. The current default rejects this short sequence based on length. A lower diagnostic minimum yields partial sequence support, but the current generator has no configured P01542 reference, so product-level candidate generation would still remain disabled. This is evidence to retain the conservative default pending a larger, independently labeled real-structure set.

## Unsupported cases and limitations

- No representative real examples for homolog rejection, long partial constructs, known engineered EGFR variants, multi-chain target selection, or DBREF1/DBREF2 were available locally; those cases are synthetic policy/API tests only.
- DBREF1/DBREF2 accession mapping remains unsupported and correctly fails closed unless a user-selected accession verifies externally; external verification does not authorize generation.
- Alignment is sequence-based and does not prove biological identity, target function, binding-pocket validity, docking accuracy, affinity, efficacy, or quantum advantage.
- Thresholds are not calibrated on a representative biological cohort. The synthetic confusion counts must not be interpreted as sensitivity, specificity, or error rates in deployment.
- UniProt lookup tests are mocked. A separate manual source review was performed for the 1CRN sequence discrepancy; no network request was made by the evaluator or test suite.

## Reproduction

From the project root using the existing Windows environment:

```powershell
.venv-win\Scripts\python.exe scripts\evaluate_target_identity_policy.py
.venv-win\Scripts\python.exe -m py_compile scripts\evaluate_target_identity_policy.py backend\services\target_sequence.py tests\test_target_identity_policy_evaluation.py
.venv-win\Scripts\python.exe -m unittest tests.test_target_identity_policy_evaluation tests.test_target_aware_generation tests.test_benchmark_api tests.test_egfr_classical_quantum_comparison tests.test_egfr_scaffold_validation -v
```

Runtime recorded: Python 3.12.3, NumPy 2.5.3, RDKit 2026.09.1.

Machine-readable case results are saved in `docs/target_identity_policy_evaluation.json`.
