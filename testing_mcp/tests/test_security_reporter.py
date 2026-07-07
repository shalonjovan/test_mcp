from testing_mcp.security.reporter import build_report, _calculate_risk, report_to_text, report_to_json


def test_build_report_empty():
    report = build_report(target=".")
    assert "report" in report
    assert "summary" in report
    assert "findings" in report
    assert report["summary"]["total_findings"] == 0
    assert report["summary"]["risk_score"] == "NONE"


def test_build_report_with_findings():
    sast_result = {
        "findings": [
            {"rule_id": "SQLI-001", "name": "SQL Injection", "severity": "HIGH", "file": "test.py", "line": 1, "match": "execute('SELECT *' + x)", "description": "SQL injection", "remediation": "Use params"},
        ],
        "summary": {"high": 1},
        "scanned_files": 1,
    }
    report = build_report(target=".", sast_result=sast_result)
    assert report["summary"]["total_findings"] == 1
    assert report["summary"]["by_severity"]["HIGH"] == 1


def test_calculate_risk_none():
    assert _calculate_risk({}) == "NONE"


def test_calculate_risk_low():
    assert _calculate_risk({"LOW": 1}) != "NONE"


def test_calculate_risk_critical():
    assert _calculate_risk({"CRITICAL": 5}) == "CRITICAL"


def test_calculate_risk_high():
    assert _calculate_risk({"HIGH": 4}) == "HIGH"


def test_calculate_risk_medium():
    assert _calculate_risk({"MEDIUM": 3}) == "MEDIUM"


def test_report_to_text():
    report = build_report(target=".")
    text = report_to_text(report)
    assert "SECURITY SCAN REPORT" in text
    assert "SUMMARY" in text
    assert "END OF REPORT" in text


def test_report_to_json():
    report = build_report(target=".")
    json_str = report_to_json(report)
    assert '"report"' in json_str
    assert '"summary"' in json_str


def test_report_deduplication():
    sast_result = {
        "findings": [
            {"rule_id": "SQLI-001", "name": "Test", "severity": "HIGH", "file": "a.py", "line": 1, "match": "test", "description": "desc", "remediation": "fix"},
            {"rule_id": "SQLI-001", "name": "Test", "severity": "HIGH", "file": "a.py", "line": 1, "match": "test", "description": "desc", "remediation": "fix"},
        ],
        "summary": {"high": 2},
        "scanned_files": 1,
    }
    report = build_report(target=".", sast_result=sast_result)
    assert report["summary"]["total_findings"] == 1
