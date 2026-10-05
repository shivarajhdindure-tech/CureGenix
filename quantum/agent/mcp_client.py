import asyncio
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class QuantumMCPClient:

    def __init__(self):
        self.server_params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "quantum.mcp.server"],
        )

    async def connect(self):

        self.stdio_context = stdio_client(
            self.server_params
        )

        self.read_stream, self.write_stream = (
            await self.stdio_context.__aenter__()
        )

        self.session = ClientSession(
            self.read_stream,
            self.write_stream,
        )

        await self.session.__aenter__()

        await self.session.initialize()

        return self

    async def list_tools(self):

        response = await self.session.list_tools()

        return response.tools

    async def call_tool(
        self,
        tool_name: str,
        arguments: dict,
    ):

        result = await self.session.call_tool(
            tool_name,
            arguments,
        )

        return result

    async def close(self):

        await self.session.__aexit__(
            None,
            None,
            None,
        )

        await self.stdio_context.__aexit__(
            None,
            None,
            None,
        )
    async def call_tool_json(
        self,
        tool_name: str,
        arguments: dict,
    ):
        import json

        result = await self.call_tool(
            tool_name,
            arguments,
        )

        if result.is_error:
            raise RuntimeError(
                f"MCP tool '{tool_name}' failed"
            )

        for content in result.content:

            if content.type == "text":
                return json.loads(content.text)

        raise RuntimeError(
            f"MCP tool '{tool_name}' returned no JSON result"
        )


async def main():

    client = QuantumMCPClient()

    try:

        await client.connect()

        print("Connected to Quantum MCP Server")
        print()

        tools = await client.list_tools()

        print("Available tools:")

        for tool in tools:
            print(f"- {tool.name}")

        print()
        print("Calling molecular_info...")
        print()

        result = await client.call_tool_json(
            "molecular_info",
            {
                "atom": "Li 0 0 0; H 0 0 1.6",
                "basis": "sto3g",
                "charge": 0,
                "spin": 0,
            },
        )

        print("Parsed MCP result:")
        print(result)

    finally:

        await client.close()

if __name__ == "__main__":

    asyncio.run(main())