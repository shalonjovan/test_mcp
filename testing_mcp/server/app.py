from fastmcp import FastMCP

from testing_mcp.server.tools import register_tools

mcp = FastMCP(
    "Testing MCP",
    instructions="Universal AI-powered testing server built on the Model Context Protocol",
    version="0.1.0",
)

register_tools(mcp)


def run_server(host: str = "127.0.0.1", port: int = 8080) -> None:
    mcp.run(host=host, port=port)
