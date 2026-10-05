"""
Memory MCP Server

Provides shared context and memory across the agent pipeline.
Agents store intermediate results and retrieve context from
previous agents. This enables context-aware orchestration —
each agent can see what prior agents discovered.
"""

import time
import copy
from backend.mcp.base_mcp import BaseMCPServer


class MemoryMCPServer(BaseMCPServer):
    def __init__(self):
        super().__init__(
            server_name="MemoryMCP",
            description="Shared memory and context management across agent pipeline"
        )
        self._memory: dict = {}
        self._pipeline_state: dict = {
            "current_query": "",
            "disease": "",
            "current_agent": "",
            "completed_agents": [],
            "accumulated_data": {}
        }
        self._history: list[dict] = []
        self._register_all_tools()

    def _register_all_tools(self):
        self.register_tool(
            name="store",
            description="Store a key-value pair in shared memory",
            handler=self._store,
            parameters={"key": "str", "value": "any"}
        )
        self.register_tool(
            name="retrieve",
            description="Retrieve a value from shared memory by key",
            handler=self._retrieve,
            parameters={"key": "str"}
        )
        self.register_tool(
            name="get_pipeline_state",
            description="Get the current pipeline execution state and accumulated context",
            handler=self._get_pipeline_state,
            parameters={}
        )
        self.register_tool(
            name="update_pipeline_state",
            description="Update pipeline state with new agent results",
            handler=self._update_pipeline_state,
            parameters={"agent_name": "str", "data": "dict"}
        )
        self.register_tool(
            name="get_agent_context",
            description="Get context relevant to a specific agent based on what previous agents produced",
            handler=self._get_agent_context,
            parameters={"agent_name": "str"}
        )
        self.register_tool(
            name="clear",
            description="Clear all memory for a fresh pipeline run",
            handler=self._clear,
            parameters={}
        )

    def _store(self, key: str, value) -> dict:
        self._memory[key] = copy.deepcopy(value)
        self._history.append({"action": "store", "key": key, "timestamp": time.time()})
        return {"stored": key, "memory_keys": list(self._memory.keys())}

    def _retrieve(self, key: str) -> dict:
        if key in self._memory:
            return {"key": key, "value": self._memory[key], "found": True}
        return {"key": key, "value": None, "found": False}

    def _get_pipeline_state(self) -> dict:
        return copy.deepcopy(self._pipeline_state)

    def _update_pipeline_state(self, agent_name: str, data: dict) -> dict:
        self._pipeline_state["completed_agents"].append(agent_name)
        self._pipeline_state["accumulated_data"][agent_name] = copy.deepcopy(data)
        self._pipeline_state["current_agent"] = agent_name
        return {
            "updated": True,
            "agent": agent_name,
            "completed_so_far": self._pipeline_state["completed_agents"]
        }

    def _get_agent_context(self, agent_name: str) -> dict:
        """Build context for an agent based on previous agents' outputs."""
        context = {
            "query": self._pipeline_state["current_query"],
            "disease": self._pipeline_state["disease"],
            "previous_agents": {}
        }
        for completed_agent in self._pipeline_state["completed_agents"]:
            context["previous_agents"][completed_agent] = (
                self._pipeline_state["accumulated_data"].get(completed_agent, {})
            )
        return context

    def _clear(self) -> dict:
        self._memory.clear()
        self._pipeline_state = {
            "current_query": "",
            "disease": "",
            "current_agent": "",
            "completed_agents": [],
            "accumulated_data": {}
        }
        self._history.clear()
        return {"cleared": True}

    def init_pipeline(self, query: str, disease: str):
        """Initialize pipeline state for a new query (convenience method)."""
        self._clear()
        self._pipeline_state["current_query"] = query
        self._pipeline_state["disease"] = disease
