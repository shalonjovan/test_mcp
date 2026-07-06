from pathlib import Path

from testing_mcp.security.sast import SAST_RULES, run_sast_scan, scan_file


def test_sast_rules_are_defined():
    assert len(SAST_RULES) > 0
    for rule in SAST_RULES:
        assert "id" in rule
        assert "patterns" in rule
        assert len(rule["patterns"]) > 0
        assert "severity" in rule


def test_scan_file_detects_sqli():
    tmp = Path("/tmp/test_sqli.py")
    tmp.write_text("import sqlite3\nconn = sqlite3.connect('test.db')\nconn.execute('SELECT * FROM users WHERE id = ' + user_input)")
    findings = scan_file(tmp)
    sqli = [f for f in findings if f["rule_id"] == "SQLI-001"]
    assert len(sqli) > 0
    tmp.unlink()


def test_scan_file_detects_xss():
    tmp = Path("/tmp/test_xss.py")
    tmp.write_text("element.innerHTML = user_input")
    findings = scan_file(tmp)
    xss = [f for f in findings if f["rule_id"] == "XSS-001"]
    assert len(xss) > 0
    tmp.unlink()


def test_scan_file_detects_hardcoded_password():
    tmp = Path("/tmp/test_secret.py")
    tmp.write_text('password = "super_secret_123"')
    findings = scan_file(tmp)
    secrets = [f for f in findings if f["rule_id"] == "SECRET-001"]
    assert len(secrets) > 0
    tmp.unlink()


def test_scan_file_detects_command_injection():
    tmp = Path("/tmp/test_cmdi.py")
    tmp.write_text('import os\nos.system(f"rm -rf {user_input}")')
    findings = scan_file(tmp)
    cmdi = [f for f in findings if f["rule_id"] == "CMDI-001"]
    assert len(cmdi) > 0
    tmp.unlink()


def test_scan_file_clean_code():
    tmp = Path("/tmp/test_clean.py")
    tmp.write_text("def hello():\n    return 'world'")
    findings = scan_file(tmp)
    assert len(findings) == 0
    tmp.unlink()


def test_run_sast_scan_returns_summary():
    result = run_sast_scan("/tmp")
    assert "tool" in result
    assert "findings" in result
    assert "summary" in result
    assert result["tool"] == "sast"
