"""Resolve target identity while retaining PDB and UniProt evidence."""

from backend.agents.base_agent import BaseAgent
from backend.services.target_identity import resolve_target_identity
from backend.services.target_sequence import validate_chain_sequence
from backend.services.target_generation_policy import authorize_target_generation


class TargetAgent(BaseAgent):
    def __init__(self, mcp_registry: dict):
        super().__init__(
            "Target Agent",
            "Validates target identity against chain-specific PDB annotations and UniProt",
            mcp_registry,
        )

    def run(self, context: dict) -> dict:
        parsed_result = self.mcp_call("memory", "retrieve", key="parsed_protein")
        parsed_protein = parsed_result.get("data", {}).get("value") or {}
        if not parsed_protein:
            return {"status": "error", "message": "No parsed protein found in memory"}

        protein = parsed_protein.get("protein", {}) or {}
        parsed_metadata = parsed_protein.get("metadata", {}) or {}
        structure_summary = parsed_protein.get("structure_summary", {}) or {}
        selection_result = self.mcp_call("memory", "retrieve", key="target_selection")
        selection = selection_result.get("data", {}).get("value") or {}
        structure_evidence = (
            selection.get("structure_identity_evidence")
            or parsed_metadata.get("structure_identity_evidence")
            or {}
        )

        selected_chain = selection.get("selected_chain_id")
        chain_ids = structure_evidence.get("chain_ids") or []
        chosen_chain = selected_chain or (chain_ids[0] if len(chain_ids) == 1 else None)
        mappings = structure_evidence.get("chain_accessions") or {}
        chain_accessions = mappings.get(chosen_chain, []) if chosen_chain is not None else []
        selected_accession = str(selection.get("selected_uniprot_id") or "").strip().upper()
        lookup_accession = selected_accession or (chain_accessions[0] if len(chain_accessions) == 1 else "")

        if lookup_accession:
            response = self.mcp_call(
                "web", "uniprot_fetch_by_accession", accession=lookup_accession
            )
            lookup_result = response.get("data") or {
                "status": "tool_error",
                "found": False,
                "error": response.get("error", "UniProt lookup tool failed."),
            }
        else:
            lookup_result = {"status": "not_attempted", "found": False}

        target_identity = resolve_target_identity(
            structure_evidence=structure_evidence,
            selected_chain_id=selected_chain,
            selected_uniprot_id=selected_accession,
            lookup_result=lookup_result,
        )
        original_identity_state = target_identity["identity_state"]
        chosen_chain_id = target_identity.get("selected_chain_id")
        chain_sequence = (structure_evidence.get("chain_sequences") or {}).get(chosen_chain_id)
        if original_identity_state in {"structure_linked", "externally_verified"}:
            sequence_validation = validate_chain_sequence(
                chain_sequence or {}, lookup_result.get("sequence")
            )
            sequence_validation["uniprot_accession"] = target_identity.get("uniprot_id") or lookup_accession
            target_identity["sequence_validation"] = sequence_validation
            if original_identity_state == "structure_linked":
                target_identity["identity_state"] = sequence_validation["identity_state"]
                independent_evidence = None
                if sequence_validation["identity_state"] == "structure_linked_partial_sequence_support":
                    header_pdb_id = str(selection.get("pdb_header_id") or parsed_metadata.get("pdb_header_id") or "").upper()
                    if header_pdb_id:
                        response = self.mcp_call(
                            "web", "rcsb_verify_chain_accession",
                            pdb_id=header_pdb_id,
                            auth_chain_id=str(chosen_chain_id or ""),
                            accession=str(target_identity.get("uniprot_id") or lookup_accession),
                        )
                        independent_evidence = response.get("data") or {
                            "status": "tool_error", "verified": False,
                            "error": response.get("error", "RCSB verification tool failed."),
                        }
                        independent_evidence["requested_pdb_id"] = header_pdb_id
                        if independent_evidence.get("verified"):
                            entity_sequence = independent_evidence.get("entity_sequence")
                            entity_validation = validate_chain_sequence(
                                chain_sequence or {}, entity_sequence
                            )
                            independent_evidence["entity_sequence_validation"] = entity_validation
                    else:
                        independent_evidence = {
                            "status": "missing_pdb_header_id", "verified": False,
                            "reason": "A PDB ID from the uploaded HEADER record is required; filename-derived IDs are not independent evidence.",
                        }
                target_identity["independent_structure_evidence"] = independent_evidence
                generation_policy = authorize_target_generation(
                    sequence_validation["identity_state"], sequence_validation,
                    selected_chain_id=chosen_chain_id,
                    uniprot_accession=target_identity.get("uniprot_id"),
                    independent_structure_evidence=independent_evidence,
                )
                target_identity["generation_authorization"] = generation_policy
                target_identity["candidate_generation_allowed"] = generation_policy["allowed"]
                target_identity["structure_match_scope"] = (
                    generation_policy["reason"]
                    if target_identity["candidate_generation_allowed"]
                    else generation_policy["reason"]
                )
                if not generation_policy["allowed"]:
                    target_identity["warnings"].append(generation_policy["reason"])
                if independent_evidence and independent_evidence.get("status") not in {"verified", "missing_pdb_header_id"}:
                    target_identity["warnings"].append(
                        f"Independent RCSB chain verification unavailable or failed ({independent_evidence.get('status')}); partial-support generation is disabled."
                    )
            else:
                target_identity["candidate_generation_allowed"] = False
                target_identity["warnings"].append(
                    "The UniProt accession is not linked to this PDB chain by DBREF; sequence alignment alone does not satisfy the current generation policy."
                )
            target_identity["warnings"].extend(sequence_validation.get("warnings") or [])
            target_identity["warnings"] = list(dict.fromkeys(target_identity["warnings"]))
        official_name = lookup_result.get("name") if lookup_result.get("found") else None
        protein_name = official_name or protein.get("name") or "Unknown Protein"
        target_identity["protein_name"] = protein_name
        target_identity["organism"] = lookup_result.get("organism") if lookup_result.get("found") else None
        target_identity["pdb_id"] = selection.get("pdb_id") or parsed_metadata.get("protein_id")
        target_identity["pdb_header_id"] = selection.get("pdb_header_id") or parsed_metadata.get("pdb_header_id")
        target_identity["sequence_length"] = len(protein.get("sequence", ""))
        # This compatibility field mirrors the explicit, richer state.
        target_identity["identity_status"] = target_identity["identity_state"]
        target_identity["structure_link_status"] = (
            "pdb_dbref_uniprot_sequence_validated"
            if target_identity["candidate_generation_allowed"]
            else "pdb_dbref_uniprot_sequence_validation_failed"
            if original_identity_state == "structure_linked"
            else "not_verified"
        )
        target_identity["warning"] = " ".join(target_identity["warnings"]) or None

        protein_info = {
            "protein_name": protein_name,
            "resolved_uniprot_name": official_name,
            "uniprot_id": target_identity.get("uniprot_id"),
            "target_identity": target_identity,
            "sequence": protein.get("sequence", ""),
            "sequence_length": len(protein.get("sequence", "")),
            "chains": protein.get("chains", []),
            "binding_sites": structure_summary.get("binding_sites", []),
            "binding_sites_count": len(structure_summary.get("binding_sites", [])),
        }
        self.mcp_call("memory", "store", key="protein_info", value=protein_info)

        summary = f"Target identity {target_identity['identity_state']}: {protein_name}"
        if target_identity.get("uniprot_id"):
            summary += f" ({target_identity['uniprot_id']})"
        return {
            "summary": summary,
            "protein_info": protein_info,
            "target_identity": target_identity,
        }
