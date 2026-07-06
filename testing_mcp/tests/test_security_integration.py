import tempfile
from pathlib import Path

from testing_mcp.security.scanner import run_security_scan


def test_security_scan_sast_mode():
    with tempfile.TemporaryDirectory() as d:
        result = run_security_scan(d, scan_type="sast")
        assert "sast" in result
        assert result["sast"]["tool"] == "sast"
        assert "findings" in result["sast"]
        assert "summary" in result["sast"]


def test_security_scan_secrets_mode():
    with tempfile.TemporaryDirectory() as d:
        Path(d, "clean.py").write_text("x = 1")
        result = run_security_scan(d, scan_type="secrets")
        assert "secrets" in result
        assert "scanned_files" in result["secrets"]


def test_security_scan_returns_project_path():
    result = run_security_scan(".", scan_type="sast")
    assert "project" in result
    assert Path(result["project"]).resolve() == Path.cwd().resolve()


def test_security_scan_all_modes():
    with tempfile.TemporaryDirectory() as d:
        Path(d, "test.py").write_text("x = 1")
        result = run_security_scan(d, scan_type="all")
        assert "sast" in result
        assert "secrets" in result
        assert "dependencies" in result
