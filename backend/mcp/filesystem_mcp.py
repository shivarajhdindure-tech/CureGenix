"""
Filesystem MCP Server

Provides tools for reading the curated molecule/disease knowledge base,
writing results, and caching pipeline outputs.
"""

import json
import os
import time
from backend.mcp.base_mcp import BaseMCPServer


DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")


class FilesystemMCPServer(BaseMCPServer):
    def __init__(self):
        super().__init__(
            server_name="FilesystemMCP",
            description="Deprecated compatibility MCP: retains file/database tools for /api/mcp-tools discovery"
        )
        self._cache: dict = {}
        self._register_all_tools()

    def _register_all_tools(self):
        self.register_tool(
            name="read_molecule_db",
            description="Read the curated molecule/disease knowledge base",
            handler=self._read_molecule_db,
            parameters={}
        )
        self.register_tool(
            name="get_disease_data",
            description="Get all data for a specific disease from the knowledge base",
            handler=self._get_disease_data,
            parameters={"disease_key": "str"}
        )
        self.register_tool(
            name="write_results",
            description="Write pipeline results to the results file",
            handler=self._write_results,
            parameters={"query": "str", "results": "dict"}
        )
        self.register_tool(
            name="read_cached",
            description="Check if cached results exist for a query",
            handler=self._read_cached,
            parameters={"query": "str"}
        )
        self.register_tool(
            name="resolve_disease_key",
            description="Resolve a user query to a disease key in the knowledge base",
            handler=self._resolve_disease_key,
            parameters={"query": "str"}
        )

    def _read_molecule_db(self) -> dict:
        """Read the full molecule database."""
        db_path = os.path.join(DATA_DIR, "molecules.json")
        try:
            with open(db_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {"status": "loaded", "diseases_available": list(data.get("diseases", {}).keys()), "data": data}
        except FileNotFoundError:
            return {"status": "error", "error": f"Database not found at {db_path}"}
        except json.JSONDecodeError as e:
            return {"status": "error", "error": f"Invalid JSON: {str(e)}"}

    def _get_disease_data(self, disease_key: str) -> dict:
        """Get data for a specific disease."""
        db_result = self._read_molecule_db()
        if db_result["status"] != "loaded":
            return db_result

        diseases = db_result["data"].get("diseases", {})
        if disease_key in diseases:
            return {"status": "found", "disease_key": disease_key, "data": diseases[disease_key]}

        return {"status": "not_found", "disease_key": disease_key, "available": list(diseases.keys())}

    def _write_results(self, query: str, results: dict) -> dict:
        """Write results to file and cache."""
        results_path = os.path.join(DATA_DIR, "results.json")
        try:
            existing = {}
            if os.path.exists(results_path):
                with open(results_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)

            if "results" not in existing:
                existing["results"] = []

            entry = {"query": query, "timestamp": time.time(), "data": results}
            existing["results"].append(entry)

            with open(results_path, "w", encoding="utf-8") as f:
                json.dump(existing, f, indent=2)

            self._cache[query.lower()] = results
            return {"status": "saved", "path": results_path}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _read_cached(self, query: str) -> dict:
        """Check cache for existing results."""
        if query.lower() in self._cache:
            return {"cached": True, "data": self._cache[query.lower()]}
        return {"cached": False}

    def _resolve_disease_key(self, query: str) -> dict:
        """Resolve a user query string to a disease key."""
        db_result = self._read_molecule_db()
        if db_result["status"] != "loaded":
            return {"resolved": False, "error": "Could not load database"}

        query_lower = query.lower()
        diseases = db_result["data"].get("diseases", {})

        for key, disease_data in diseases.items():
            aliases = disease_data.get("aliases", [])
            name = disease_data.get("name", "").lower()
            if any(alias in query_lower for alias in aliases) or key in query_lower or name in query_lower:
                return {"resolved": True, "disease_key": key, "disease_name": disease_data["name"]}

        return {
            "resolved": False,
            "available_diseases": {k: v["name"] for k, v in diseases.items()},
            "suggestion": "Could not match query to a known disease. Try one of the available diseases."
        }
