from pathlib import Path

from testing_mcp.utils.config import _deep_merge, load_config


def test_load_config_defaults():
    config = load_config()
    assert "server" in config
    assert config["server"]["host"] == "127.0.0.1"
    assert config["server"]["port"] == 8080
    assert "project" in config


def test_deep_merge():
    base = {"a": 1, "b": {"c": 2, "d": 3}}
    overlay = {"b": {"c": 99, "e": 4}, "f": 5}
    _deep_merge(base, overlay)
    assert base["a"] == 1
    assert base["b"]["c"] == 99
    assert base["b"]["d"] == 3
    assert base["b"]["e"] == 4
    assert base["f"] == 5
