from pathlib import Path

from testing_mcp.runners.integration import run_integration_tests, run_smoke_tests


def test_run_integration_no_tests():
    result = run_integration_tests(Path("/tmp"))
    assert result["test_count"] == 0
    assert result["passed"] is False


def test_smoke_tests_no_targets():
    result = run_smoke_tests(Path.cwd())
    assert result["passed"] is False


def test_smoke_tests_with_endpoints():
    result = run_smoke_tests(Path.cwd(), endpoints=["https://example.com"])
    assert result["test_count"] == 1
