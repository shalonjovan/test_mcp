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


def test_security_scan_config_mode():
    with tempfile.TemporaryDirectory() as d:
        Path(d, "Dockerfile").write_text("FROM ubuntu:latest\n")
        result = run_security_scan(d, scan_type="config")
        assert "config_scanner" in result
        assert result["config_scanner"]["tool"] == "config-scanner"


def test_security_scan_with_report():
    with tempfile.TemporaryDirectory() as d:
        result = run_security_scan(d, scan_type="sast", generate_report=True)
        assert "report" in result
        assert "report_data" in result
        assert "SECURITY SCAN REPORT" in result["report"]


def test_security_scan_deps_mode():
    with tempfile.TemporaryDirectory() as d:
        Path(d, "requirements.txt").write_text("flask==2.0.1\nrequests>=2.25.0\n")
        result = run_security_scan(d, scan_type="deps")
        assert "dependencies" in result
        assert "osv_dependencies" in result


def test_security_scan_tls_requires_host():
    result = run_security_scan(".", scan_type="tls")
    assert "tls" in result
    assert "error" in result["tls"]


def test_security_scan_dast_requires_url():
    result = run_security_scan(".", scan_type="dast")
    assert "dast" in result
    assert "error" in result["dast"]


def test_security_scan_crawler_requires_url():
    result = run_security_scan(".", scan_type="crawler")
    assert "web_crawler" in result
    assert "error" in result["web_crawler"]
