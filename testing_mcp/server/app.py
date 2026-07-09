from __future__ import annotations

from fastmcp import FastMCP

from testing_mcp.log import get_logger, setup_logging
from testing_mcp.server.state import get_settings, set_settings
from testing_mcp.server.tools import register_tools
from testing_mcp.utils.config import Settings, load_settings

log = get_logger(__name__)


def create_app(settings: Settings | None = None) -> FastMCP:
    if settings is not None:
        set_settings(settings)
    else:
        set_settings(load_settings())

    setup_logging(get_settings().log_level)

    mcp = FastMCP(
        "Testing MCP",
        instructions="Universal AI-powered testing server built on the Model Context Protocol",
        version=get_settings().version,
    )

    register_tools(mcp)
    log.info("tools registered")
    return mcp


# Module-level mcp instance for backward compatibility
mcp = create_app()


def run_server(host: str | None = None, port: int | None = None) -> None:
    settings = get_settings()
    h = host or settings.host
    p = port or settings.port
    log.info("starting SSE server on %s:%s", h, p)
    mcp.run(transport="sse", host=h, port=p)
