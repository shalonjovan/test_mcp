import pytest

from testing_mcp.api.testing import run_api_test_sync


def test_api_test_invalid_url():
    result = run_api_test_sync(base_url="http://localhost:1", method="GET", path="/", timeout=1.0)
    assert result["passed"] is False
    assert "error" in result


def test_api_test_result_fields():
    result = run_api_test_sync(base_url="http://localhost:1", method="GET", path="/", timeout=1.0)
    assert "name" in result
    assert "passed" in result
    assert result["passed"] is False
