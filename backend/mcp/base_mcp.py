"""
Base MCP (Model Context Protocol) Server

Provides a standardized interface for tools that agents can use.
Each MCP server registers tools, and agents invoke them by name.
This is the core abstraction that makes the system context-aware
and enables intelligent orchestration.
"""

from typing import Any, Callable
import time
import json


class MCPTool:
    """Represents a single tool exposed by an MCP server."""

    def __init__(self, name: str, description: str, handler: Callable, parameters: dict = None):
        self.name = name
        self.description = description
        self.handler = handler
        self.parameters = parameters or {}
        self.call_count = 0
        self.total_time_ms = 0

    def invoke(self, **kwargs) -> dict:
        """Invoke the tool with given parameters."""
        start = time.time()
        try:
            result = self.handler(**kwargs)
            elapsed_ms = int((time.time() - start) * 1000)
            self.call_count += 1
            self.total_time_ms += elapsed_ms
            return {
                "status": "success",
                "data": result,
                "duration_ms": elapsed_ms,
                "tool": self.name
            }
        except Exception as e:
            elapsed_ms = int((time.time() - start) * 1000)
            return {
                "status": "error",
                "error": str(e),
                "duration_ms": elapsed_ms,
                "tool": self.name
            }

    def get_schema(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }


class BaseMCPServer:
    """
    Base class for all MCP servers.

    An MCP server exposes a set of tools that agents can discover and invoke.
    This follows the Model Context Protocol pattern:
    - Tools are registered with name, description, and handler
    - Agents discover available tools via list_tools()
    - Agents invoke tools by name via call_tool()
    - All tool calls are logged for observability
    """

    def __init__(self, server_name: str, description: str):
        self.server_name = server_name
        self.description = description
        self._tools: dict[str, MCPTool] = {}
        self._call_log: list[dict] = []

    def register_tool(self, name: str, description: str, handler: Callable, parameters: dict = None):
        """Register a tool with this MCP server."""
        self._tools[name] = MCPTool(name, description, handler, parameters)

    def list_tools(self) -> list[dict]:
        """List all available tools (MCP discovery endpoint)."""
        return [tool.get_schema() for tool in self._tools.values()]

    def call_tool(self, tool_name: str, **kwargs) -> dict:
        """Invoke a tool by name (MCP invocation endpoint)."""
        if tool_name not in self._tools:
            return {
                "status": "error",
                "error": f"Tool '{tool_name}' not found in {self.server_name}",
                "available_tools": list(self._tools.keys())
            }

        result = self._tools[tool_name].invoke(**kwargs)

        self._call_log.append({
            "tool": tool_name,
            "params": kwargs,
            "status": result["status"],
            "duration_ms": result["duration_ms"],
            "timestamp": time.time()
        })

        return result

    def get_stats(self) -> dict:
        """Get usage statistics for this MCP server."""
        return {
            "server": self.server_name,
            "total_calls": len(self._call_log),
            "tools": {
                name: {
                    "calls": tool.call_count,
                    "total_time_ms": tool.total_time_ms
                }
                for name, tool in self._tools.items()
            }
        }

    def get_call_log(self) -> list[dict]:
        """Get the full call log for observability."""
        return self._call_log
