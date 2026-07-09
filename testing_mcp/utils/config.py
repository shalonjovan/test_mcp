from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import toml

DEFAULT_CONFIG_PATHS = [
    Path("testing-mcp.toml"),
    Path(".testing-mcp.toml"),
]


def _load_file(path: Path) -> dict[str, Any]:
    if path.suffix == ".json":
        return json.loads(path.read_text())
    return toml.load(path)


def load_raw_config(path: Path | None = None) -> dict[str, Any]:
    config: dict[str, Any] = {
        "server": {"host": "127.0.0.1", "port": 8080},
        "project": {},
        "plugins": {"enabled": []},
    }

    search_paths = [path] if path else DEFAULT_CONFIG_PATHS
    for config_path in search_paths:
        if config_path and config_path.exists():
            raw = _load_file(config_path)
            _deep_merge(config, raw)
            break

    return config


def _deep_merge(base: dict, overlay: dict) -> None:
    for key, value in overlay.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value


@dataclass
class Settings:
    host: str = "127.0.0.1"
    port: int = 8080
    log_level: str = "INFO"
    version: str = "0.1.0"
    config: dict[str, Any] = field(default_factory=dict)


def load_settings(config_path: Path | None = None) -> Settings:
    raw = load_raw_config(config_path)

    server_cfg = raw.get("server", {})

    host = (
        os.environ.get("TESTING_MCP_HOST")
        or server_cfg.get("host")
        or "127.0.0.1"
    )
    port = int(
        os.environ.get("TESTING_MCP_PORT")
        or server_cfg.get("port")
        or 8080
    )
    log_level = (
        os.environ.get("TESTING_MCP_LOG_LEVEL")
        or server_cfg.get("log_level")
        or "INFO"
    )

    return Settings(
        host=str(host),
        port=int(port),
        log_level=str(log_level).upper(),
        config=raw,
    )
