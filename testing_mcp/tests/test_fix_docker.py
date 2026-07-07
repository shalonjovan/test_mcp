from __future__ import annotations

import tempfile
from pathlib import Path

from testing_mcp.fix.docker import generate_dockerfile


def test_generate_dockerfile_python():
    with tempfile.TemporaryDirectory() as d:
        Path(d, "pyproject.toml").write_text("[project]\nname = 'test'\n")
        result = generate_dockerfile(d)
        assert result["language"] == "python"
        assert "FROM python:" in result["content"]
        assert Path(result["path"]).exists()


def test_generate_dockerfile_returns_content():
    with tempfile.TemporaryDirectory() as d:
        Path(d, "pyproject.toml").write_text("[project]\nname = 'test'\n")
        result = generate_dockerfile(d)
        assert "lines" in result
        assert result["lines"] > 0
        assert result["content"].endswith("\n")


def test_generate_dockerfile_no_project():
    with tempfile.TemporaryDirectory() as d:
        result = generate_dockerfile(d)
        assert Path(result["path"]).exists()
        assert result["language"] in ("unknown", "python")
