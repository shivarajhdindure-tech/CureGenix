"""
Orchestrator — The central controller that manages the agent pipeline.

Initializes all MCP servers, creates agents with MCP access,
and runs the full discovery pipeline in sequence.
This demonstrates MCP-powered intelligent orchestration.

v2: Accepts parsed PDB protein structure (AlphaFold-compatible JSON)
    instead of a disease query string.
"""

import time
from backend.mcp.web_mcp import WebMCPServer
from backend.mcp.memory_mcp import MemoryMCPServer
from backend.mcp.filesystem_mcp import FilesystemMCPServer
from backend.mcp.compute_mcp import ComputeMCPServer
from backend.mcp.molecule_mcp import MoleculeMCPServer

from backend.agents.target_agent import TargetAgent
from backend.agents.research_agent import ResearchAgent
from backend.agents.molecule_agent import MoleculeAgent
from backend.agents.quantum_analysis_agent import QuantumAnalysisAgent
from backend.agents.screening_agent import ScreeningAgent
from backend.agents.risk_agent import RiskAgent
from backend.agents.decision_agent import DecisionAgent




class Orchestrator:
    """
    MCP-powered orchestrator that:
    1. Initializes all MCP servers (tool providers)
    2. Creates agents with MCP registry access
    3. Accepts parsed protein structure from PDB upload
    4. Runs the 6-agent pipeline sequentially
    5. Returns the complete discovery result
    """

    def __init__(self):
        # Initialize MCP servers
        self.mcp_servers = {
            "web": WebMCPServer(),
            "memory": MemoryMCPServer(),
            "filesystem": FilesystemMCPServer(),
            "compute": ComputeMCPServer(),
            "molecule": MoleculeMCPServer(),
        }

        # Create agents with MCP access
        self.agents = [
            TargetAgent(self.mcp_servers),
            ResearchAgent(self.mcp_servers),
            MoleculeAgent(self.mcp_servers),
            QuantumAnalysisAgent(self.mcp_servers),
            ScreeningAgent(self.mcp_servers),
            RiskAgent(self.mcp_servers),
            DecisionAgent(self.mcp_servers),
        ]

    def run_pipeline(self, parsed_protein: dict, protein_metadata: dict | None = None):
        pipeline_start = time.time()
        protein_payload = protein_metadata or {}
        protein_name_for_pipeline = (
            protein_payload.get("base_name")
            or parsed_protein.get("protein", {}).get("name")
            or "Unknown"
        )

        # 1. Clear memory & init
        memory_mcp = self.mcp_servers["memory"]
        memory_mcp.init_pipeline("analyze_pdb", protein_name_for_pipeline)
        
        # 2. Store input for the Target agent
        memory_mcp._store("parsed_protein", parsed_protein)

        # 3. Execute agents sequentially
        results = {}
        for agent in self.agents:
            # We use .execute() to get timing/status wrappers
            results[agent.name.lower().replace(" ", "_")] = agent.execute({})
            
        # 4. Fetch the conclusive decisions from Memory MCP
        final_decisions = memory_mcp._retrieve("final_decisions").get("value") or []
        highlights = memory_mcp._retrieve("highlights").get("value") or {}
        research_result = memory_mcp._retrieve("research_result").get("value") or {}
        protein_info = memory_mcp._retrieve("protein_info").get("value") or {}

        pipeline_duration_ms = int((time.time() - pipeline_start) * 1000)
        resolved_protein_name = protein_info.get("protein_name", "Unknown")
        protein_name = protein_payload.get("name") or resolved_protein_name
        protein_pdb_id = protein_payload.get("pdb_id") or parsed_protein.get("metadata", {}).get("protein_id")
        protein_source = protein_payload.get("source") or "uploaded"
        top_candidate = final_decisions[0] if final_decisions else None

        # 5. Return structured output matching frontend expectations
        return {
            "status": "success",
            "protein": {
                "name": protein_name,
                "pdb_id": protein_pdb_id,
                "source": protein_source,
            },
            # Backward compatibility fields
            "protein_name": protein_name,
            "protein_id": protein_pdb_id if protein_pdb_id else resolved_protein_name,
            "uniprot_id": protein_info.get("uniprot_id"),
            "alphafold_url": research_result.get("alphafold_url"),
            "binder_search": research_result.get("binder_search"),
            "llm_analysis": research_result.get("llm_analysis"),
            "protein_info": {
                "sequence_length": protein_info.get("sequence_length", 0),
                "chains": protein_info.get("chains", []),
                "binding_sites_count": protein_info.get("binding_sites_count", 0),
                "binding_sites": protein_info.get("binding_sites", [])
            },
            "steps": [res for k, res in results.items()],
            "decisions": final_decisions,
            "top_candidate": {
                "drug_name": top_candidate.get("drug_name"),
                "smiles": top_candidate.get("smiles"),
                "category": top_candidate.get("category"),
                "rank": top_candidate.get("rank"),
                "adjusted_score": top_candidate.get("adjusted_score"),
            } if top_candidate else None,
            "highlights": highlights,
            "summary": (
                f"Analyzed '{protein_name}' — "
                f"{len(final_decisions)} drug candidates ranked."
            ),
            "pipeline_duration_ms": pipeline_duration_ms,
            "mcp_stats": self.get_mcp_stats()
        }


    def get_mcp_tools(self) -> dict:
        """Get all available MCP tools across all servers (for transparency/demo)."""
        return {
            name: server.list_tools()
            for name, server in self.mcp_servers.items()
        }

    def get_mcp_stats(self) -> dict:
        """Get the true live usage metrics (call counts and execution ms)."""
        return {
            name: server.get_stats()
            for name, server in self.mcp_servers.items()
        }
