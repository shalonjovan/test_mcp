from __future__ import annotations

import tempfile
from pathlib import Path

from testing_mcp.fix.migrations import extract_schema_migrations


def test_extract_migrations_no_schema():
    with tempfile.TemporaryDirectory() as d:
        Path(d, "main.py").write_text("x = 1\n")
        result = extract_schema_migrations(d, db_type="sqlite")
        assert result["migrations_created"] == []
        assert result["count"] == 0


def test_extract_migrations_detects_create_table():
    with tempfile.TemporaryDirectory() as d:
        Path(d, "models.py").write_text(
            'SCHEMA = """\nCREATE TABLE users (\n    id INTEGER PRIMARY KEY,\n    name TEXT\n);\n"""\n'
        )
        result = extract_schema_migrations(d, db_type="sqlite")
        assert result["count"] >= 1
        assert len(result["migrations_created"]) >= 1
        for mig in result["migrations_created"]:
            assert mig.endswith(".sql")


def test_extract_migrations_creates_migrations_dir():
    with tempfile.TemporaryDirectory() as d:
        Path(d, "db.py").write_text('sql = "CREATE TABLE posts (id INTEGER);"\n')
        result = extract_schema_migrations(d, db_type="sqlite", output_dir=str(Path(d, "db_migrations")))
        assert Path(d, "db_migrations").exists()
        assert result["count"] >= 1


def test_extract_migrations_skips_venv():
    with tempfile.TemporaryDirectory() as d:
        Path(d, ".venv", "lib.py").parent.mkdir(parents=True)
        Path(d, ".venv", "lib.py").write_text("CREATE TABLE foo (id INTEGER);")
        Path(d, "app.py").write_text("CREATE TABLE bar (id INTEGER);")
        result = extract_schema_migrations(d, db_type="sqlite")
        # Should find only bar, not foo in .venv
        found_files = [s["file"] for s in result["schemas_found"]]
        assert all(".venv" not in f for f in found_files)
