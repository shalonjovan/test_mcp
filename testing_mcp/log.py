from __future__ import annotations

import logging
import sys
from typing import Literal

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


def setup_logging(level: LogLevel = "INFO") -> None:
    """Configure structured logging for the testing-mcp server."""
    logger = logging.getLogger("testing_mcp")
    logger.setLevel(getattr(logging, level))

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setLevel(getattr(logging, level))
        fmt = logging.Formatter(
            "[%(asctime)s] %(levelname)-8s %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(fmt)
        logger.addHandler(handler)

    # Silence noisy third-party loggers
    for name in ("httpx", "httpcore", "urllib3", "playwright", "asyncio"):
        logging.getLogger(name).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a child logger under the testing_mcp namespace."""
    if name.startswith("testing_mcp."):
        return logging.getLogger(name)
    return logging.getLogger(f"testing_mcp.{name}")
