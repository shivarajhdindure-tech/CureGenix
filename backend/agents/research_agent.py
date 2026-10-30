"""Collect target research context only when structure identity is accepted."""

from backend.agents.base_agent import BaseAgent
from backend.services.research_evidence import (
    filter_binder_search_result,
    has_accepted_structure_identity,
)


class ResearchAgent(BaseAgent):
    def __init__(self, mcp_registry: dict):
        super().__init__("Research Agent", "Retrieves target-scoped research evidence", mcp_registry)

    def run(self, context: dict) -> dict:
        info_result = self.mcp_call("memory", "retrieve", key="protein_info")
        protein_info = info_result.get("data", {}).get("value") or {}
        if not protein_info:
            return {"status": "error", "message": "No protein_info found in memory"}

        protein_name = protein_info.get("protein_name", "Unknown Protein")
        target_identity = protein_info.get("target_identity") or {}
        uniprot_id = target_identity.get("uniprot_id") or protein_info.get("uniprot_id")
        identity_accepted = has_accepted_structure_identity(target_identity)
        alphafold_url = None
        binder_result = {
            "found": False,
            "status": "not_searched_identity_unverified",
            "summary": "Target-specific research was withheld because the selected-chain identity did not pass sequence validation.",
        }

        if identity_accepted:
            af_result = self.mcp_call("web", "verify_alphafold", uniprot_id=uniprot_id)
            alphafold_url = af_result.get("data", {}).get("url")
            raw_binder_search = self.mcp_call(
                "web", "search_binders", protein_name=protein_name
            ).get("data", {})
            binder_result = filter_binder_search_result(raw_binder_search, target_identity)

        sequence_validation = target_identity.get("sequence_validation") or {}
        if identity_accepted:
            llm_analysis = (
                "Template-based evidence summary: the selected PDB chain passed the configured "
                f"sequence identity policy for {protein_name} ({uniprot_id}), with "
                f"{sequence_validation.get('aligned_observed_residue_count', protein_info.get('sequence_length', 0))} "
                "aligned observed residues. The fetched record does not include a validated protein-function "
                "annotation. No target-specific binder evidence or druggability assessment is available; "
                "these properties were not assessed."
            )
        else:
            llm_analysis = (
                "Template-based evidence summary: the uploaded structure is annotated as "
                f"{protein_name or 'an unresolved target'}, but its selected-chain identity did not pass "
                f"sequence validation ({target_identity.get('identity_state', 'unresolved')}). "
                "Biological function, pathway, druggability, and binder claims were not assessed. "
                "No target-specific binder search was performed."
            )

        agent_output = {
            "alphafold_url": alphafold_url,
            "binder_search": binder_result,
            "llm_analysis": llm_analysis,
            "analysis_method": "template_based_evidence_summary",
        }
        self.mcp_call("memory", "store", key="research_result", value=agent_output)
        summary = (
            f"Research evidence summary for '{protein_name}'"
            if identity_accepted
            else f"Target-specific research withheld because identity was not sequence-validated for '{protein_name}'"
        )
        return {"summary": summary, "research_data": agent_output}
