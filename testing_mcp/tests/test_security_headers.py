import pytest

from testing_mcp.security.headers import SECURITY_HEADERS, scan_headers


def test_security_headers_defined():
    assert len(SECURITY_HEADERS) >= 5
    assert "Strict-Transport-Security" in SECURITY_HEADERS
    assert "Content-Security-Policy" in SECURITY_HEADERS


@pytest.mark.asyncio
async def test_scan_headers_example():
    result = await scan_headers("https://example.com", timeout=10.0)
    assert result["passed"] is False
    assert "missing_headers" in result
    assert "overall_score" in result


@pytest.mark.asyncio
async def test_scan_headers_invalid_url():
    result = await scan_headers("https://nonexistent.invalid", timeout=2.0)
    assert result["passed"] is False
    assert "error" in result
