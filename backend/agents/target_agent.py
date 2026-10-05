"""
Target Agent — Identifies therapeutic targets from uploaded protein structure.

v2: Works with parsed PDB protein data (AlphaFold-compatible) instead of
    disease-based filesystem lookups. Extracts target information from the
    protein structure, binding sites, and sequence data.
"""

from backend.agents.base_agent import BaseAgent


class TargetAgent(BaseAgent):
    def __init__(self, mcp_registry: dict):
        super().__init__("Target Agent", "Identifies therapeutic targets from protein structure", mcp_registry)

    def run(self, context: dict) -> dict:
        # Retrieve input data from Memory MCP
        parsed_result = self.mcp_call("memory", "retrieve", key="parsed_protein")
        parsed_protein = parsed_result.get("data", {}).get("value") or {}
        if not parsed_protein:
            return {"status": "error", "message": "No parsed protein found in memory"}

        protein_info = parsed_protein.get("protein", {})
        protein_name = protein_info.get("name", "Unknown Protein")
        sequence = protein_info.get("sequence", "")
        chains = protein_info.get("chains", [])
        
        structure_summary = parsed_protein.get("structure_summary", {})
        binding_sites = structure_summary.get("binding_sites", [])

        # Fetch Uniprot ID from WebMCP
        uniprot_result = self.mcp_call("web", "uniprot_search", protein_name=protein_name)
        uniprot_id = uniprot_result.get("data", {}).get("uniprot_id")
        resolved_uniprot_name = uniprot_result.get("data", {}).get("name")

        # Store the protein_info in memory for following agents
        agent_output = {
            "protein_name": protein_name,
            "resolved_uniprot_name": resolved_uniprot_name,
            "uniprot_id": uniprot_id,
            "sequence": sequence,
            "sequence_length": len(sequence),
            "chains": chains,
            "binding_sites": binding_sites,
            "binding_sites_count": len(binding_sites)
        }
        self.mcp_call("memory", "store", key="protein_info", value=agent_output)

        summary = f"Identified protein targets for uploaded protein '{protein_name}' via UniProt (ID: {uniprot_id})"
        return {
            "summary": summary,
            "protein_info": agent_output
        }
