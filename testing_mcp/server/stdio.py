from __future__ import annotations

from testing_mcp.server.app import mcp


def run_stdio() -> None:
    mcp.run(transport="stdio")
