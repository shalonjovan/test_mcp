from __future__ import annotations

import json
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


def load_config(path: Path | None = None) -> dict[str, Any]:
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
