from __future__ import annotations

from testing_mcp.log import get_logger
from testing_mcp.server.app import mcp

log = get_logger(__name__)


def run_stdio() -> None:
    log.info("starting stdio transport")
    mcp.run(transport="stdio")
