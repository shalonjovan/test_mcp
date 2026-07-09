from __future__ import annotations

from fastmcp import FastMCP

from testing_mcp.log import get_logger
from testing_mcp.server.tools._helpers import _browser_sess, _resolve_command, _resolve_path, _resolve_url  # noqa: F401

log = get_logger(__name__)

TOOL_MODULES = [
    "testing_mcp.server.tools.core",
    "testing_mcp.server.tools.project",
    "testing_mcp.server.tools.api",
    "testing_mcp.server.tools.security",
    "testing_mcp.server.tools.performance",
    "testing_mcp.server.tools.ui",
    "testing_mcp.server.tools.database",
    "testing_mcp.server.tools.fix",
    "testing_mcp.server.tools.mobile",
    "testing_mcp.server.tools.game",
    "testing_mcp.server.tools.infra",
    "testing_mcp.server.tools.debug",
    "testing_mcp.server.tools.browser",
]


def register_tools(mcp: FastMCP) -> None:
    for mod_name in TOOL_MODULES:
        try:
            mod = __import__(mod_name, fromlist=["register_tools"])
            mod.register_tools(mcp)
            log.debug("registered tools from %s", mod_name)
        except Exception:
            log.exception("failed to load tool module %s", mod_name)
