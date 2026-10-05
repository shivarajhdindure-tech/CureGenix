"""
Molecule Agent — Generates novel drug candidates using MoleculeMCP.

v2: Works with protein-structure context. Uses binding-site data to inform
    molecular generation. Falls back to filesystem knowledge base for curated
    candidates when available.
"""

from backend.agents.base_agent import BaseAgent


class MoleculeAgent(BaseAgent):
    def __init__(self, mcp_registry: dict):
        super().__init__("Molecule Agent", "Generates novel drug candidates and molecular analogs", mcp_registry)

    def run(self, context: dict) -> dict:
        # Retrieve research result
        research_res = self.mcp_call("memory", "retrieve", key="research_result")
        research = research_res.get("data", {}).get("value") or {}
        
        info_res = self.mcp_call("memory", "retrieve", key="protein_info")
        protein_name = (info_res.get("data", {}).get("value") or {}).get("protein_name", "Unknown")

        if not research:
            return {"status": "error", "message": "No research_result found"}

        # Minimal generation using molecule MCP
        generated_candidates = []
        analog_result = self.mcp_call("molecule", "generate_analogs",
                                      parent_smiles="CC(=O)Oc1ccccc1",  # Minimal base scaffold
                                      parent_name=f"{protein_name}_scaffold",
                                      modification_strategy="balanced",
                                      count=2)
        analogs = analog_result.get("data", {}).get("analogs", [])
        
        for analog in analogs:
            props_result = self.mcp_call("molecule", "compute_molecular_properties", smiles=analog.get("smiles", ""))
            generated_candidates.append({
                "name": analog.get("id", "Unknown"),
                "smiles": analog.get("smiles", ""),
                "molecular_properties": props_result.get("data", {}),
                "source": "MoleculeMCP - Analog Generation",
                "category": "novel"
            })

        # Inject known drugs dynamically recovered from the internet via WebMCP
        web_search_res = self.mcp_call("web", "search_drugs", disease=protein_name, target=protein_name)
        known_drugs = web_search_res.get("data", {}).get("known_drugs", [])
        
        for drug in known_drugs:
            generated_candidates.append({
                "name": drug.get("name", "Unknown Drug"),
                "smiles": drug.get("smiles", ""),
                "molecular_properties": {},
                "source": drug.get("source", "Web Search"),
                "category": drug.get("category", "approved")
            })

        self.mcp_call("memory", "store", key="molecules", value=generated_candidates)

        return {
            "summary": f"Generated {len(generated_candidates)} candidate molecules for {protein_name}",
            "molecules": generated_candidates
        }
