"""
Base Agent class.

All agents inherit from this. Each agent declares which MCP tools it needs,
and it receives an MCP registry to call tools through. This enforces that
agents never access data directly — all interactions go through MCP.
"""

import time
from typing import Any


class BaseAgent:
    """Base class for all pipeline agents."""

    def __init__(self, name: str, description: str, mcp_registry: dict):
        self.name = name
        self.description = description
        self.mcp = mcp_registry  # dict of MCP server instances
        self.start_time = 0
        self.end_time = 0

    def mcp_call(self, server_name: str, tool_name: str, **kwargs) -> dict:
        """Call an MCP tool. All data access goes through this."""
        server = self.mcp.get(server_name)
        if not server:
            return {"status": "error", "error": f"MCP server '{server_name}' not found"}
        return server.call_tool(tool_name, **kwargs)

    def run(self, context: dict) -> dict:
        """Execute the agent. Override in subclasses."""
        raise NotImplementedError

    def execute(self, context: dict) -> dict:
        """Wrapper that times execution and formats result."""
        self.start_time = time.time()
        try:
            result = self.run(context)
            self.end_time = time.time()
            duration_ms = int((self.end_time - self.start_time) * 1000)

            # Store result in MemoryMCP
            self.mcp_call("memory", "update_pipeline_state",
                          agent_name=self.name, data=result)

            return {
                "agent_name": self.name,
                "status": "completed",
                "duration_ms": duration_ms,
                "summary": result.get("summary", ""),
                "data": result
            }
        except Exception as e:
            self.end_time = time.time()
            duration_ms = int((self.end_time - self.start_time) * 1000)
            return {
                "agent_name": self.name,
                "status": "error",
                "duration_ms": duration_ms,
                "summary": f"Error: {str(e)}",
                "data": {"error": str(e)}
            }
