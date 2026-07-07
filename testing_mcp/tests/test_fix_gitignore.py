from __future__ import annotations

import tempfile
from pathlib import Path

from testing_mcp.fix.gitignore import add_to_gitignore


def test_add_to_gitignore_creates_file():
    with tempfile.TemporaryDirectory() as d:
        result = add_to_gitignore(d, patterns=[".env", "__pycache__/"])
        assert result["modified"] is True
        assert ".env" in result["added"]
        assert "__pycache__/" in result["added"]
        assert Path(d, ".gitignore").exists()
        content = Path(d, ".gitignore").read_text()
        assert ".env" in content
        assert "__pycache__/" in content


def test_add_to_gitignore_appends_to_existing():
    with tempfile.TemporaryDirectory() as d:
        Path(d, ".gitignore").write_text("*.pyc\n")
        result = add_to_gitignore(d, patterns=[".env"])
        assert result["modified"] is True
        assert ".env" in result["added"]
        content = Path(d, ".gitignore").read_text()
        assert "*.pyc" in content
        assert ".env" in content


def test_add_to_gitignore_no_duplicates():
    with tempfile.TemporaryDirectory() as d:
        Path(d, ".gitignore").write_text(".env\n")
        result = add_to_gitignore(d, patterns=[".env", "__pycache__/"])
        assert result["modified"] is True
        assert ".env" in result["already_present"]
        assert "__pycache__/" in result["added"]


def test_add_to_gitignore_no_patterns():
    with tempfile.TemporaryDirectory() as d:
        result = add_to_gitignore(d, patterns=[])
        assert result["modified"] is False
        assert result["added"] == []


def test_add_to_gitignore_nothing_to_add():
    with tempfile.TemporaryDirectory() as d:
        Path(d, ".gitignore").write_text(".env\n__pycache__/\n")
        result = add_to_gitignore(d, patterns=[".env", "__pycache__/"])
        assert result["modified"] is False
        assert result["added"] == []
        assert len(result["already_present"]) == 2
