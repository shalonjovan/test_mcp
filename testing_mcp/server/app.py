from __future__ import annotations

import time

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from testing_mcp import __version__
from testing_mcp.log import get_logger, setup_logging
from testing_mcp.server.state import get_settings, get_start_time, set_settings
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

    _add_health_route(mcp)
    register_tools(mcp)
    log.info("tools registered")
    return mcp


def _add_health_route(mcp: FastMCP) -> None:
    """Register a /health HTTP endpoint on the MCP server."""

    @mcp.custom_route("/health", methods=["GET"])
    async def health(request: Request) -> JSONResponse:
        uptime = time.time() - get_start_time()
        tool_count = 0
        for p in mcp.providers:
            try:
                components = getattr(p, "_components", {})
                tool_count += sum(1 for k in components if k.startswith("tool:"))
            except Exception:
                pass
        return JSONResponse({
            "status": "ok",
            "version": __version__,
            "uptime_seconds": round(uptime, 2),
            "tools_registered": tool_count,
        })

    @mcp.custom_route("/health/live", methods=["GET"])
    async def health_live(request: Request) -> JSONResponse:
        return JSONResponse({"status": "alive"})

    @mcp.custom_route("/health/ready", methods=["GET"])
    async def health_ready(request: Request) -> JSONResponse:
        return JSONResponse({"status": "ready"})


# Module-level mcp instance for backward compatibility
mcp = create_app()


def run_server(host: str | None = None, port: int | None = None) -> None:
    settings = get_settings()
    h = host or settings.host
    p = port or settings.port
    log.info("starting SSE server on %s:%s", h, p)
    mcp.run(transport="sse", host=h, port=p)
