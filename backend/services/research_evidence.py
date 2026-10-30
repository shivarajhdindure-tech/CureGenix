"""Evidence gates for target-specific research summaries."""

from __future__ import annotations

import re


ACCEPTED_IDENTITY_STATES = {
    "structure_linked_sequence_validated",
    "structure_linked_partial_sequence_support",
}


def has_accepted_structure_identity(target_identity: dict | None) -> bool:
    identity = target_identity or {}
    return (
        identity.get("identity_state") in ACCEPTED_IDENTITY_STATES
        and identity.get("candidate_generation_allowed") is True
    )


def filter_binder_search_result(search_result: dict | None, target_identity: dict | None) -> dict:
    """Reject generic search hits as binder evidence unless target text is consistent.

    Wikipedia search is not a curated target-ligand database. Even a name
    match is returned as unverified context, never as a verified binder.
    """
    identity = target_identity or {}
    if not has_accepted_structure_identity(identity):
        return {
            "found": False,
            "status": "not_searched_identity_unverified",
            "summary": "Binder search was not performed because the uploaded chain did not pass target identity validation.",
        }

    result = search_result or {}
    title = str(result.get("title") or "")
    summary = str(result.get("summary") or "")
    evidence_text = f"{title} {summary}".casefold()
    target_name = re.sub(r"\s+", " ", str(identity.get("protein_name") or "").strip()).casefold()
    accession = str(identity.get("uniprot_id") or "").strip().casefold()
    consistent = bool(
        (target_name and len(target_name) >= 4 and target_name in evidence_text)
        or (accession and accession in evidence_text)
    )
    if not consistent:
        return {
            "found": False,
            "status": "rejected_target_mismatch",
            "rejected_title": title or None,
            "source": result.get("source"),
            "source_url": result.get("source_url"),
            "summary": "The generic search hit did not identify the validated target and was excluded from binder evidence.",
        }
    return {
        "found": False,
        "status": "unverified_search_context",
        "title": title or None,
        "source": result.get("source"),
        "source_url": result.get("source_url"),
        "summary": "A generic search hit mentions the target, but this source does not verify a target-ligand interaction; it is not counted as binder evidence.",
    }
