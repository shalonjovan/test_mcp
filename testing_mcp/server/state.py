from __future__ import annotations

import time

from testing_mcp.utils.config import Settings

__all__ = ["get_settings", "set_settings", "get_start_time"]

_settings: Settings | None = None
_start_time: float = time.time()


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        from testing_mcp.utils.config import load_settings

        _settings = load_settings()
    return _settings


def set_settings(settings: Settings) -> None:
    global _settings
    _settings = settings


def get_start_time() -> float:
    global _start_time
    return _start_time
