"""Conservative authorization policy for target-informed candidate generation."""

from __future__ import annotations


def authorize_target_generation(
    identity_state: str,
    sequence_validation: dict | None,
    *,
    selected_chain_id: str | None,
    uniprot_accession: str | None,
    independent_structure_evidence: dict | None = None,
) -> dict:
    """Authorize exact matches directly; require independent RCSB evidence for partials.

    Sequence similarity alone is not sufficient for a partial construct. The
    independent evidence must identify the selected author chain and accession
    through a curated PDB-to-UniProt mapping (SIFTS) and include a passing
    sequence check against the PDB polymer-entity construct sequence.
    """
    validation = sequence_validation or {}
    accession = str(uniprot_accession or "").upper()
    exact = (
        identity_state == "structure_linked_sequence_validated"
        and validation.get("validation_outcome") == "passed_full"
        and validation.get("identity_fraction") == 1.0
        and validation.get("substitution_count", 0) == 0
        and validation.get("insertion_count", 0) == 0
        and validation.get("deletion_count", 0) == 0
    )
    if exact:
        return {
            "allowed": True,
            "policy_state": "exact_sequence_correspondence",
            "evidence": ["selected-chain DBREF accession", "exact UniProt accession lookup", "full observed-sequence correspondence"],
            "reason": "The selected chain has exact full-sequence correspondence to the linked UniProt reference.",
        }

    if identity_state == "structure_linked_partial_sequence_support":
        independent = independent_structure_evidence or {}
        mapping = independent.get("mapping") or {}
        entity_validation = independent.get("entity_sequence_validation") or {}
        verified = (
            independent.get("status") == "verified"
            and str(independent.get("pdb_id") or "").upper() == str(independent.get("requested_pdb_id") or "").upper()
            and str(independent.get("auth_chain_id") or "") == str(selected_chain_id or "")
            and str(mapping.get("database_accession") or mapping.get("accession") or "").upper() == accession
            and mapping.get("database_name") == "UniProt"
            and mapping.get("provenance_source") == "SIFTS"
            and entity_validation.get("validation_outcome") in {"passed_full", "passed_partial"}
            and entity_validation.get("informative_aligned_residues", 0) >= 100
        )
        if verified:
            return {
                "allowed": True,
                "policy_state": "independently_documented_partial_construct",
                "evidence": ["selected-chain DBREF accession", "exact UniProt accession lookup", "RCSB/SIFTS chain-to-accession mapping", "observed sequence support against RCSB entity sequence"],
                "reason": "Partial sequence support is accompanied by an independently documented RCSB/SIFTS mapping for this chain and accession.",
            }
        return {
            "allowed": False,
            "policy_state": "partial_support_unverified",
            "evidence": [],
            "reason": "Partial sequence support alone cannot establish target identity; independent chain-to-accession evidence and entity-sequence support are required.",
        }

    return {
        "allowed": False,
        "policy_state": "insufficient_or_conflicting_evidence",
        "evidence": [],
        "reason": "Target-specific generation requires exact sequence correspondence or independently documented partial-construct evidence.",
    }
