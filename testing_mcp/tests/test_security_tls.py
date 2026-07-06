from testing_mcp.security.tls import check_tls


def test_tls_invalid_hostname():
    result = check_tls("nonexistent.invalid.example", timeout=2.0)
    assert result["passed"] is False
    assert "error" in result


def test_tls_bad_port():
    result = check_tls("example.com", port=1, timeout=2.0)
    assert result["passed"] is False
