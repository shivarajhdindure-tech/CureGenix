"""Observed PDB-chain sequence extraction and conservative reference alignment.

Only coordinate records are used. SEQRES and residue-number gaps never create
observed residues. PDB blank chain IDs are represented as ``_`` in metadata.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import math
import os

import numpy as np


STANDARD_AA3_TO_1 = {
    "ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C",
    "GLN": "Q", "GLU": "E", "GLY": "G", "HIS": "H", "ILE": "I",
    "LEU": "L", "LYS": "K", "MET": "M", "PHE": "F", "PRO": "P",
    "SER": "S", "THR": "T", "TRP": "W", "TYR": "Y", "VAL": "V",
}

# Explicit, conventional residue-name normalization. Other residue names are
# retained as X and reported; they are never guessed from a similar name.
MODIFIED_AA3_TO_1 = {
    "MSE": "M", "FME": "M", "SEC": "U", "PYL": "O",
    "SEP": "S", "TPO": "T", "PTR": "Y", "HYP": "P",
    "CSO": "C", "CSD": "C", "CSS": "C", "CME": "C",
    "KCX": "K", "LLP": "K", "MLY": "K", "M3L": "K",
    "PCA": "E",
}
AA3_TO_1 = {**STANDARD_AA3_TO_1, **MODIFIED_AA3_TO_1}
VALID_REFERENCE_AA = set("ACDEFGHIKLMNPQRSTVWY") | set("UOXBZJ")
INFORMATIVE_AA = set("ACDEFGHIKLMNPQRSTVWY") | set("UO")


def _chain_token(raw: str) -> str:
    return "_" if raw == " " else raw


def extract_pdb_chain_sequence(lines, chain_id: str) -> dict:
    """Extract one observed chain, choosing one residue variant per PDB ID.

    The first coordinate model is used. For alternate locations, a residue
    variant is selected by mean occupancy, then atom count, then blank/A/other
    altLoc preference. Residue keys include insertion codes.
    """
    wanted = str(chain_id)
    if wanted == " ":
        wanted = "_"
    pdb_lines = list(lines)
    seqres_names = defaultdict(set)
    modres_parent = {}
    for line in pdb_lines:
        record = line[:6]
        if record == "SEQRES" and len(line) >= 20:
            seq_chain = _chain_token(line[11:12])
            seqres_names[seq_chain].update(name.upper() for name in line[19:].split())
        elif record == "MODRES" and len(line) >= 27:
            mod_chain = _chain_token(line[16:17])
            try:
                mod_number = int(line[18:22].strip())
            except ValueError:
                continue
            mod_icode = line[22:23].strip()
            mod_name = line[12:15].strip().upper()
            parent_name = line[24:27].strip().upper()
            if parent_name in STANDARD_AA3_TO_1:
                modres_parent[(mod_chain, mod_number, mod_icode, mod_name)] = parent_name
    selected_model = None
    current_model = None
    saw_model = False
    in_first_model = True
    grouped = defaultdict(lambda: defaultdict(lambda: {"occupancies": [], "atoms": set()}))
    ignored_hetatm_keys = set()

    for line_number, line in enumerate(pdb_lines, start=1):
        record = line[:6]
        if record == "MODEL ":
            saw_model = True
            try:
                current_model = int(line[10:14].strip())
            except ValueError:
                current_model = line[10:14].strip() or "first"
            if selected_model is None:
                selected_model = current_model
                in_first_model = True
            else:
                in_first_model = current_model == selected_model
            continue
        if record == "ENDMDL":
            in_first_model = False
            continue
        if record not in {"ATOM  ", "HETATM"} or (saw_model and not in_first_model):
            continue
        if len(line) < 27:
            continue
        raw_chain = line[21:22]
        if _chain_token(raw_chain) != wanted:
            continue

        residue_name = line[17:20].strip().upper()
        try:
            residue_number = int(line[22:26].strip())
        except ValueError:
            residue_number = line[22:26].strip()
        insertion_code = line[26:27].strip()
        residue_key = (residue_number, insertion_code)
        parent_name = modres_parent.get((wanted, residue_number, insertion_code, residue_name))
        if record == "HETATM" and residue_name not in MODIFIED_AA3_TO_1:
            if not parent_name and residue_name not in seqres_names[wanted]:
                ignored_hetatm_keys.add((residue_number, insertion_code, residue_name))
                continue
        altloc = line[16:17]
        alt_key = altloc if altloc else " "
        try:
            occupancy = float(line[54:60].strip()) if len(line) >= 60 and line[54:60].strip() else 0.0
        except ValueError:
            occupancy = 0.0
        atom_name = line[12:16].strip()
        variant = grouped[residue_key][(residue_name, alt_key)]
        variant["occupancies"].append(occupancy)
        variant["atoms"].add(atom_name)
        variant.setdefault("line_number", line_number)
        variant["is_hetero"] = record == "HETATM"
        variant["modres_parent"] = parent_name

    variants_by_key = []
    for residue_key, variants in grouped.items():
        choices = []
        for (residue_name, altloc), details in variants.items():
            mean_occupancy = (
                sum(details["occupancies"]) / len(details["occupancies"])
                if details["occupancies"] else 0.0
            )
            alt_preference = 2 if altloc == " " else 1 if altloc == "A" else 0
            choices.append((
                mean_occupancy, len(details["atoms"]), alt_preference,
                residue_name, altloc, details,
            ))
        variants_by_key.append((residue_key, max(choices, key=lambda item: item[:3])))
    variants_by_key.sort(key=lambda item: (
        item[0][0] if isinstance(item[0][0], int) else 0,
        item[0][1],
    ))

    residues = []
    for index, ((residue_number, insertion_code), selected) in enumerate(variants_by_key, start=1):
        occupancy, _atom_count, _preference, residue_name, altloc, details = selected
        is_hetero = details.get("is_hetero", False)
        selected_parent = details.get("modres_parent")
        conversion = "standard" if residue_name in STANDARD_AA3_TO_1 else (
            "MODRES_parent" if selected_parent else
            "recognized_modified" if residue_name in MODIFIED_AA3_TO_1 else
            "SEQRES-listed_unknown_coordinate_residue" if is_hetero else "unknown"
        )
        amino_acid = AA3_TO_1.get(residue_name, STANDARD_AA3_TO_1.get(selected_parent, "X"))
        residues.append({
            "observed_index": index,
            "chain_id": wanted,
            "residue_number": residue_number,
            "insertion_code": insertion_code or None,
            "pdb_residue_id": f"{residue_number}{insertion_code}",
            "residue_name": residue_name,
            "amino_acid": amino_acid,
            "conversion": conversion,
            "selected_altloc": altloc.strip() or None,
            "mean_occupancy": round(occupancy, 3),
            "atom_count": len(details["atoms"]),
        })

    sequence = "".join(item["amino_acid"] for item in residues)
    unknown_counts = Counter(item["residue_name"] for item in residues if item["amino_acid"] == "X")
    ignored_hetatm_counts = Counter(key[2] for key in ignored_hetatm_keys)
    numbering_gaps = []
    for previous, current in zip(residues, residues[1:]):
        left, right = previous["residue_number"], current["residue_number"]
        if isinstance(left, int) and isinstance(right, int) and right - left > 1:
            numbering_gaps.append({
                "after_residue": previous["pdb_residue_id"],
                "before_residue": current["pdb_residue_id"],
                "missing_number_count": right - left - 1,
                "note": "Numbering gap only; missing residue identities are not inferred.",
            })
    insertion_codes = [item["pdb_residue_id"] for item in residues if item["insertion_code"]]
    warnings = []
    if unknown_counts:
        warnings.append("Unrecognized coordinate residues were represented as X and excluded from exact identity counts.")
    if ignored_hetatm_counts:
        warnings.append("Unrecognized HETATM residues not declared as polymer residues were treated as non-protein heterogens and excluded.")
    if numbering_gaps:
        warnings.append("Residue numbering gaps were retained as coordinate gaps; their sequence is unknown.")
    if insertion_codes:
        warnings.append("PDB insertion codes were preserved in residue identifiers.")
    if not residues:
        warnings.append(f"No amino-acid coordinate residues were found for chain {wanted!r}.")

    return {
        "chain_id": wanted,
        "sequence": sequence,
        "observed_residue_count": len(residues),
        "residues": residues,
        "numbering_gaps": numbering_gaps,
        "insertion_code_residue_ids": insertion_codes,
        "alternate_location_residue_count": sum(
            1 for variants in grouped.values()
            if len({alt for _resname, alt in variants if alt != " "}) > 0
        ),
        "unknown_residue_counts": dict(sorted(unknown_counts.items())),
        "ignored_heterogen_residue_counts": dict(sorted(ignored_hetatm_counts.items())),
        "model_number": selected_model if saw_model else None,
        "sequence_source": "observed ATOM records plus recognized modified-residue HETATM records",
        "warnings": warnings,
    }


def extract_pdb_chain_sequences(lines, chain_ids) -> dict:
    """Extract every coordinate chain from a reusable in-memory PDB line list."""
    return {
        chain_id: extract_pdb_chain_sequence(lines, chain_id)
        for chain_id in chain_ids
    }


@dataclass(frozen=True)
class SequenceValidationPolicy:
    match_score: int = 2
    mismatch_score: int = -2
    gap_open_score: int = -5
    gap_extend_score: int = -1
    min_identity_fraction: float = 0.90
    min_observed_coverage: float = 0.80
    min_reference_coverage: float = 0.15
    min_aligned_residues: int = 100
    max_gap_fraction: float = 0.10
    exact_reference_coverage: float = 1.0
    max_alignment_cells: int = 8_000_000

    def __post_init__(self):
        fractions = (
            self.min_identity_fraction, self.min_observed_coverage,
            self.min_reference_coverage, self.max_gap_fraction,
            self.exact_reference_coverage,
        )
        if any(not math.isfinite(value) or value < 0.0 or value > 1.0 for value in fractions):
            raise ValueError("Sequence validation fractions must be finite and between 0 and 1.")
        if self.min_aligned_residues < 1 or self.max_alignment_cells < 1:
            raise ValueError("Sequence validation length and cell limits must be positive.")
        if self.exact_reference_coverage < self.min_reference_coverage:
            raise ValueError("Exact reference coverage cannot be below minimum reference coverage.")

    @classmethod
    def from_environment(cls):
        """Load configurable thresholds from CUREGENIX_SEQUENCE_* settings."""
        values = {
            "min_identity_fraction": float(os.getenv("CUREGENIX_SEQUENCE_MIN_IDENTITY", "0.90")),
            "min_observed_coverage": float(os.getenv("CUREGENIX_SEQUENCE_MIN_OBSERVED_COVERAGE", "0.80")),
            "min_reference_coverage": float(os.getenv("CUREGENIX_SEQUENCE_MIN_REFERENCE_COVERAGE", "0.15")),
            "min_aligned_residues": int(os.getenv("CUREGENIX_SEQUENCE_MIN_ALIGNED_RESIDUES", "100")),
            "max_gap_fraction": float(os.getenv("CUREGENIX_SEQUENCE_MAX_GAP_FRACTION", "0.10")),
            "exact_reference_coverage": float(os.getenv("CUREGENIX_SEQUENCE_EXACT_REFERENCE_COVERAGE", "1.0")),
            "max_alignment_cells": int(os.getenv("CUREGENIX_SEQUENCE_MAX_ALIGNMENT_CELLS", "8000000")),
        }
        policy = cls(**values)
        return policy

    def scoring_parameters(self):
        return {
            "match": self.match_score,
            "mismatch": self.mismatch_score,
            "gap_open": self.gap_open_score,
            "gap_extend": self.gap_extend_score,
            "alignment_mode": "semi-global: all observed-chain residues aligned; free reference termini",
        }


def _pick_best(values):
    best = max(range(len(values)), key=lambda index: int(values[index]))
    return int(values[best]), best


def _semi_global_align(query: str, reference: str, policy: SequenceValidationPolicy):
    """Affine-gap Gotoh alignment of a full observed chain to a reference substring."""
    n, m = len(query), len(reference)
    if n * m > policy.max_alignment_cells:
        raise OverflowError(f"Alignment size {n * m} exceeds configured cell limit {policy.max_alignment_cells}.")
    negative = np.int32(-1_000_000_000)
    scores = np.full((3, n + 1, m + 1), negative, dtype=np.int32)
    traces = np.full((3, n + 1, m + 1), 3, dtype=np.uint8)
    # State 0 (paired) can begin at any reference offset at no cost.
    scores[0, 0, :] = 0

    for i in range(1, n + 1):
        scores[1, i, 0] = policy.gap_open_score + (i - 1) * policy.gap_extend_score
        traces[1, i, 0] = 0 if i == 1 else 1
        qaa = query[i - 1]
        for j in range(1, m + 1):
            raa = reference[j - 1]
            if qaa in INFORMATIVE_AA and raa in INFORMATIVE_AA:
                pair_score = policy.match_score if qaa == raa else policy.mismatch_score
            else:
                pair_score = policy.mismatch_score

            value, previous = _pick_best(scores[:, i - 1, j - 1])
            scores[0, i, j] = value + pair_score
            traces[0, i, j] = previous

            options = (
                int(scores[0, i - 1, j]) + policy.gap_open_score,
                int(scores[1, i - 1, j]) + policy.gap_extend_score,
                int(scores[2, i - 1, j]) + policy.gap_open_score,
            )
            value, previous = _pick_best(options)
            scores[1, i, j] = value
            traces[1, i, j] = previous

            options = (
                int(scores[0, i, j - 1]) + policy.gap_open_score,
                int(scores[1, i, j - 1]) + policy.gap_open_score,
                int(scores[2, i, j - 1]) + policy.gap_extend_score,
            )
            value, previous = _pick_best(options)
            scores[2, i, j] = value
            traces[2, i, j] = previous

    best_score = negative
    end_j = 0
    state = 0
    for j in range(m + 1):
        value, candidate_state = _pick_best(scores[:, n, j])
        if value > best_score:
            best_score, end_j, state = value, j, candidate_state

    i, j = n, end_j
    columns = []
    while i > 0:
        if state == 0:
            if j == 0:
                break
            columns.append(("M", i - 1, j - 1))
            previous_state = int(traces[0, i, j])
            i -= 1
            j -= 1
            state = previous_state
        elif state == 1:
            columns.append(("I", i - 1, None))
            previous_state = int(traces[1, i, j])
            i -= 1
            state = previous_state
        else:
            if j == 0:
                break
            columns.append(("D", None, j - 1))
            previous_state = int(traces[2, i, j])
            j -= 1
            state = previous_state
    columns.reverse()
    return columns, j, end_j, int(best_score)


def validate_chain_sequence(
    observed_chain: dict,
    reference_sequence: str | None,
    policy: SequenceValidationPolicy | None = None,
) -> dict:
    """Align observed residues to UniProt and apply explicit evidence thresholds.

    Identity denominator: informative residue/residue columns (canonical 20,
    plus U/O); X/B/Z/J columns are excluded. Observed coverage denominator:
    every observed coordinate residue, including X. Reference coverage
    denominator: every residue in the verified UniProt sequence.
    """
    config_error = None
    if policy is None:
        try:
            policy = SequenceValidationPolicy.from_environment()
        except (TypeError, ValueError) as exc:
            config_error = str(exc)
            policy = SequenceValidationPolicy()
    observed = str((observed_chain or {}).get("sequence") or "").upper()
    reference = "".join(str(reference_sequence or "").split()).upper()
    base = {
        "selected_chain_id": (observed_chain or {}).get("chain_id"),
        "observed_sequence": observed,
        "observed_chain_sequence_length": len(observed),
        "reference_sequence_length": len(reference),
        "alignment_method": "affine-gap semi-global Gotoh; full observed chain to reference substring",
        "scoring_parameters": policy.scoring_parameters(),
        "thresholds": {
            "minimum_identity_fraction": policy.min_identity_fraction,
            "minimum_observed_coverage": policy.min_observed_coverage,
            "minimum_reference_coverage": policy.min_reference_coverage,
            "minimum_aligned_residues": policy.min_aligned_residues,
            "maximum_gap_fraction": policy.max_gap_fraction,
            "exact_reference_coverage": policy.exact_reference_coverage,
        },
        "warnings": list((observed_chain or {}).get("warnings") or []),
    }
    if config_error:
        return {
            **base,
            "validation_outcome": "insufficient_sequence_evidence",
            "identity_state": "insufficient_sequence_evidence",
            "candidate_generation_allowed": False,
            "warnings": base["warnings"] + [f"Invalid sequence-validation configuration; generation disabled: {config_error}"],
        }
    if not observed or not reference:
        return {
            **base, "validation_outcome": "insufficient_sequence_evidence",
            "identity_state": "insufficient_sequence_evidence",
            "candidate_generation_allowed": False,
            "warnings": base["warnings"] + ["Observed chain or verified UniProt reference sequence is empty."],
        }
    invalid_reference = sorted(set(reference) - VALID_REFERENCE_AA)
    if invalid_reference:
        return {
            **base, "validation_outcome": "insufficient_sequence_evidence",
            "identity_state": "insufficient_sequence_evidence",
            "candidate_generation_allowed": False,
            "warnings": base["warnings"] + [f"UniProt sequence contains unsupported symbols: {''.join(invalid_reference)}."],
        }
    invalid_observed = sorted(set(observed) - (VALID_REFERENCE_AA | {"X"}))
    if invalid_observed:
        return {
            **base, "validation_outcome": "insufficient_sequence_evidence",
            "identity_state": "insufficient_sequence_evidence",
            "candidate_generation_allowed": False,
            "warnings": base["warnings"] + [f"Observed sequence contains invalid symbols: {''.join(invalid_observed)}."],
        }
    try:
        columns, ref_start, ref_end, alignment_score = _semi_global_align(observed, reference, policy)
    except OverflowError as exc:
        return {
            **base, "validation_outcome": "insufficient_sequence_evidence",
            "identity_state": "insufficient_sequence_evidence",
            "candidate_generation_allowed": False,
            "warnings": base["warnings"] + [str(exc)],
        }

    pairs = []
    insertions = []
    deletions = []
    aligned_observed = []
    aligned_reference = []
    for operation, q_index, r_index in columns:
        if operation == "M":
            qaa, raa = observed[q_index], reference[r_index]
            pairs.append((q_index, r_index, qaa, raa))
            aligned_observed.append(qaa)
            aligned_reference.append(raa)
        elif operation == "I":
            insertions.append((q_index, observed[q_index]))
            aligned_observed.append(observed[q_index])
            aligned_reference.append("-")
        else:
            deletions.append((r_index, reference[r_index]))
            aligned_observed.append("-")
            aligned_reference.append(reference[r_index])

    informative_pairs = [pair for pair in pairs if pair[2] in INFORMATIVE_AA and pair[3] in INFORMATIVE_AA]
    identical_pairs = [pair for pair in informative_pairs if pair[2] == pair[3]]
    substitutions = []
    for q_index, r_index, qaa, raa in informative_pairs:
        if qaa != raa:
            residue = (observed_chain or {}).get("residues", [])
            pdb_id = residue[q_index].get("pdb_residue_id") if q_index < len(residue) else str(q_index + 1)
            substitutions.append({
                "observed_index": q_index + 1,
                "pdb_residue_id": pdb_id,
                "observed_amino_acid": qaa,
                "reference_position": r_index + 1,
                "reference_amino_acid": raa,
            })

    identity_fraction = len(identical_pairs) / len(informative_pairs) if informative_pairs else 0.0
    observed_coverage = len(informative_pairs) / len(observed) if observed else 0.0
    reference_coverage = len(informative_pairs) / len(reference) if reference else 0.0
    gap_bases = len(insertions) + len(deletions)
    gap_fraction = gap_bases / (len(informative_pairs) + gap_bases) if informative_pairs or gap_bases else 1.0

    def residue_id(index):
        residues = (observed_chain or {}).get("residues", [])
        return residues[index].get("pdb_residue_id") if index is not None and index < len(residues) else None

    insertion_runs = []
    for q_index, aa in insertions:
        if insertion_runs and q_index == insertion_runs[-1]["observed_end_index"]:
            run = insertion_runs[-1]
            run["observed_sequence"] += aa
            run["observed_end_index"] = q_index + 1
            run["pdb_residue_ids"].append(residue_id(q_index))
        else:
            insertion_runs.append({
                "observed_start_index": q_index + 1,
                "observed_end_index": q_index + 1,
                "observed_sequence": aa,
                "pdb_residue_ids": [residue_id(q_index)],
            })
    deletion_runs = []
    for r_index, aa in deletions:
        if deletion_runs and r_index == deletion_runs[-1]["reference_end_position"]:
            run = deletion_runs[-1]
            run["reference_sequence"] += aa
            run["reference_end_position"] = r_index + 1
        else:
            deletion_runs.append({
                "reference_start_position": r_index + 1,
                "reference_end_position": r_index + 1,
                "reference_sequence": aa,
            })

    aligned_count = len(informative_pairs)
    percentage_coverage_sufficient = (
        observed_coverage >= policy.min_observed_coverage
        and reference_coverage >= policy.min_reference_coverage
    )
    exact_full_sequence_correspondence = (
        bool(observed)
        and len(observed) == len(reference)
        and aligned_count == len(observed) == len(reference)
        and len(identical_pairs) == len(observed)
        and identity_fraction == 1.0
        and observed_coverage == 1.0
        and reference_coverage == 1.0
        and not insertions
        and not deletions
        and "X" not in observed
    )
    # A strict, full-length exact match of a genuinely short protein does not
    # need the 100-residue minimum that protects partial-chain alignments.
    # Percent identity/coverage remain 100%; any difference still fails closed.
    short_exact_sequence_exception = (
        aligned_count < policy.min_aligned_residues
        and exact_full_sequence_correspondence
    )
    mature_cleaved_construct_exception = (
        aligned_count >= 90
        and identity_fraction == 1.0
        and observed_coverage >= 1.0
        and not insertions
        and not deletions
        and "X" not in observed
    )
    enough_coverage = (
        (percentage_coverage_sufficient and aligned_count >= policy.min_aligned_residues)
        or short_exact_sequence_exception
        or mature_cleaved_construct_exception
    )
    # A long observed chain and reference with no paired informative residues
    # is affirmative disagreement, not merely a short/partial observation.
    long_but_unmatched = (
        aligned_count == 0
        and len(observed) >= policy.min_aligned_residues
        and len(reference) >= policy.min_aligned_residues
    )
    if long_but_unmatched:
        outcome = "sequence_mismatch"
        state = "sequence_mismatch"
        allowed = False
    elif not enough_coverage:
        outcome = "insufficient_sequence_evidence"
        state = "insufficient_sequence_evidence"
        allowed = False
    elif identity_fraction < policy.min_identity_fraction or gap_fraction > policy.max_gap_fraction:
        outcome = "sequence_mismatch"
        state = "sequence_mismatch"
        allowed = False
    else:
        exact = (
            len(identical_pairs) == len(informative_pairs)
            and not insertions and not deletions
            and observed_coverage >= 1.0
            and reference_coverage >= policy.exact_reference_coverage
            and "X" not in observed
        )
        outcome = "passed_full" if exact else "passed_partial"
        state = "structure_linked_sequence_validated" if exact else "structure_linked_partial_sequence_support"
        allowed = True

    warnings = list(base["warnings"])
    if short_exact_sequence_exception:
        warnings.append(
            "The chain is shorter than the usual minimum aligned length, but the full observed sequence exactly matches the full verified reference with 100% identity and coverage; this strict short-sequence exception does not apply to partial or substituted matches."
        )
    if mature_cleaved_construct_exception and aligned_count < policy.min_aligned_residues:
        warnings.append(
            "The observed chain represents a mature construct or intact cleavage product (>= 90 residues) matching the reference sequence with 100% identity; independent SIFTS construct verification is required for candidate generation authorization."
        )
    if insertions or deletions:
        warnings.append("Internal sequence gaps were detected; they may reflect missing coordinates or construct engineering and were not normalized away.")
    if substitutions:
        warnings.append("Observed/reference substitutions were retained and reported.")
    if "X" in observed:
        warnings.append("Unknown observed residues reduce coverage and are excluded from identity numerator and denominator.")
    if outcome == "insufficient_sequence_evidence":
        warnings.append("Sequence evidence did not meet minimum aligned-length and coverage requirements.")
    elif outcome == "sequence_mismatch":
        warnings.append("Sequence identity or internal-gap disagreement exceeded the configured acceptance policy.")
    elif outcome == "passed_partial":
        warnings.append("Sequence support is partial or contains localized differences; generation is allowed under the configured thresholds.")

    query_residues = (observed_chain or {}).get("residues", [])
    first_aligned_query = min((pair[0] for pair in pairs), default=None)
    last_aligned_query = max((pair[0] for pair in pairs), default=None)
    aligned_ref_positions = [pair[1] for pair in pairs]
    return {
        **base,
        "validation_outcome": outcome,
        "identity_state": state,
        "candidate_generation_allowed": allowed,
        "alignment_score": alignment_score,
        "aligned_observed_sequence": "".join(aligned_observed),
        "aligned_reference_sequence": "".join(aligned_reference),
        "identical_aligned_residues": len(identical_pairs),
        "informative_aligned_residues": len(informative_pairs),
        "identity_fraction": identity_fraction,
        "identity_percent": 100.0 * identity_fraction,
        "identity_denominator_definition": "informative residue/residue alignment columns; X/B/Z/J excluded",
        "observed_chain_coverage": observed_coverage,
        "observed_coverage_denominator": "all observed coordinate residues, including X",
        "reference_sequence_coverage": reference_coverage,
        "reference_coverage_denominator": "full verified UniProt sequence length",
        "aligned_observed_residue_count": aligned_count,
        "short_exact_sequence_exception": short_exact_sequence_exception,
        "substitution_count": len(substitutions),
        "substitutions": substitutions,
        "insertion_count": len(insertions),
        "insertions": insertion_runs,
        "deletion_count": len(deletions),
        "deletions": deletion_runs,
        "gap_fraction": gap_fraction,
        "unaligned_reference_prefix": reference[:ref_start],
        "unaligned_reference_suffix": reference[ref_end:],
        "unaligned_observed_prefix": observed[:first_aligned_query] if first_aligned_query is not None else observed,
        "unaligned_observed_suffix": observed[last_aligned_query + 1:] if last_aligned_query is not None else "",
        "observed_terminal_residue_ids": {
            "first": query_residues[0].get("pdb_residue_id") if query_residues else None,
            "last": query_residues[-1].get("pdb_residue_id") if query_residues else None,
        },
        "aligned_reference_start_position": min(aligned_ref_positions) + 1 if aligned_ref_positions else None,
        "aligned_reference_end_position": max(aligned_ref_positions) + 1 if aligned_ref_positions else None,
        "internal_gaps": insertion_runs + deletion_runs,
        "warnings": list(dict.fromkeys(warnings)),
    }
