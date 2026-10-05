"""
Research Agent — Retrieves known drugs, clinical trials, and evidence.

v3: LLM-POWERED. After gathering deterministic data from WebMCP and MemoryMCP,
    uses the LLM service to interpret biological relevance, explain protein
    function, and identify known binders with scientific reasoning.
    
    LLM is used for: reasoning, interpretation, explanation
    LLM is NOT used for: database lookup, scoring, parsing
"""

from backend.agents.base_agent import BaseAgent
from backend.services.llm_service import call_llm


class ResearchAgent(BaseAgent):
    def __init__(self, mcp_registry: dict):
        super().__init__("Research Agent", "Retrieves known drugs and clinical evidence with LLM-powered analysis", mcp_registry)

    def run(self, context: dict) -> dict:
        # ── Step 1: Get protein info from Memory MCP ──────────────────────
        info_result = self.mcp_call("memory", "retrieve", key="protein_info")
        protein_info = info_result.get("data", {}).get("value") or {}
        
        if not protein_info:
            return {"status": "error", "message": "No protein_info found in memory"}

        protein_name = protein_info.get("protein_name", "Unknown Protein")
        uniprot_id = protein_info.get("uniprot_id")
        sequence_length = protein_info.get("sequence_length", 0)
        binding_sites = protein_info.get("binding_sites", [])

        # ── Step 2: Verify AlphaFold Prediction via WebMCP ────────────────
        af_result = self.mcp_call("web", "verify_alphafold", uniprot_id=uniprot_id)
        alphafold_url = af_result.get("data", {}).get("url") if uniprot_id else None

        # ── Step 3: Search for known binders via WebMCP ───────────────────
        binder_result_raw = self.mcp_call("web", "search_binders", protein_name=protein_name)
        binder_result = binder_result_raw.get("data", {})

        # ── Step 4: LLM-Powered Reasoning ─────────────────────────────────
        # Build a rich prompt with all gathered deterministic data
        prompt = f"""You are a biomedical AI research assistant specializing in drug discovery.

Protein: {protein_name}
UniProt ID: {uniprot_id or 'Not available'}
Sequence Length: {sequence_length} residues
Binding Sites Detected: {len(binding_sites)}
AlphaFold Model: {'Available' if alphafold_url else 'Not available'}

Binder search data:
{binder_result.get('summary', 'No binder data available')}

Tasks:
1. Explain the biological function of this protein in 2-3 sentences
2. Assess the druggability of this target based on its structural features
3. Identify any known drugs or molecules that bind to it (from the binder data above)
4. If known binders exist, describe their mechanism of action briefly
5. If no confirmed binders exist, suggest what class of molecules might be effective

Keep your response concise, scientific, and formatted with clear headings.
Do NOT use markdown code blocks. Use plain text with ## headings."""

        llm_analysis = call_llm(prompt, temperature=0.7, max_tokens=1024)

        # ── Step 5: Construct output ──────────────────────────────────────
        agent_output = {
            "alphafold_url": alphafold_url,
            "binder_search": binder_result,
            "llm_analysis": llm_analysis
        }

        # ── Step 6: Store in Memory MCP for downstream agents ─────────────
        self.mcp_call("memory", "store", key="research_result", value=agent_output)

        summary = f"Generated AlphaFold mapping, binder search, and LLM analysis for '{protein_name}'"
        return {
            "summary": summary,
            "research_data": agent_output
        }
