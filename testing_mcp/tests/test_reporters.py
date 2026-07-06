from testing_mcp.reporters.report import generate_html_report, generate_json_report, generate_markdown_report


RESULTS = [
    {"passed": True, "name": "test_a", "duration": 0.5, "message": ""},
    {"passed": False, "name": "test_b", "duration": 1.2, "message": "AssertionError", "stderr": "assert 1 == 2"},
]


def test_markdown_report():
    report = generate_markdown_report(RESULTS)
    assert "# Test Report" in report
    assert "Total:" in report
    assert "Passed:" in report
    assert "Failed:" in report
    assert "test_a" in report
    assert "test_b" in report


def test_html_report():
    report = generate_html_report(RESULTS)
    assert "<h1>Test Report</h1>" in report
    assert "test_a" in report
    assert "test_b" in report
    assert "pass" in report.lower()
    assert "fail" in report.lower()


def test_json_report():
    report = generate_json_report(RESULTS)
    import json
    data = json.loads(report)
    assert data["title"] == "Test Report"
    assert data["summary"]["total"] == 2
    assert data["summary"]["passed"] == 1
    assert data["summary"]["failed"] == 1
    assert len(data["results"]) == 2
