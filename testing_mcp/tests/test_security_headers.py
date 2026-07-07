from testing_mcp.security.headers import HEADER_CHECKS, scan_headers


def test_header_checks_defined():
    assert len(HEADER_CHECKS) >= 10
    ids = [c["id"] for c in HEADER_CHECKS]
    assert "HDR-001" in ids
    assert "HDR-002" in ids
    assert "HDR-003" in ids
    assert "HDR-004" in ids
    assert "HDR-014" in ids
    assert "HDR-015" in ids


def test_scan_headers_missing_all():
    result = scan_headers({}, url="https://example.com")
    assert result["status"] == "fail"
    assert result["total_checks"] >= 10
    assert result["checks_passed"] < result["total_checks"]
    assert "strict-transport-security" in result["missing"]


def test_scan_headers_all_present():
    headers = {
        "strict-transport-security": "max-age=63072000; includeSubDomains",
        "x-content-type-options": "nosniff",
        "x-frame-options": "DENY",
        "content-security-policy": "default-src 'self'",
        "x-xss-protection": "1; mode=block",
        "referrer-policy": "strict-origin-when-cross-origin",
        "permissions-policy": "geolocation=()",
        "cache-control": "no-store",
        "server": "Apache/2.4.41",
        "x-powered-by": "Express",
    }
    result = scan_headers(headers)
    assert result["status"] == "fail"
    findings = {f["rule_id"] for f in result["findings"]}
    assert "HDR-009" in findings
    assert "HDR-010" in findings


def test_scan_headers_weak_hsts():
    headers = {
        "strict-transport-security": "max-age=86400",
    }
    result = scan_headers(headers)
    hsts = [f for f in result["findings"] if f["rule_id"] == "HDR-011"]
    assert len(hsts) > 0


def test_scan_headers_unsafe_csp():
    headers = {
        "content-security-policy": "default-src 'unsafe-inline' 'unsafe-eval'",
    }
    result = scan_headers(headers)
    csp = [f for f in result["findings"] if f["rule_id"] == "HDR-015"]
    assert len(csp) > 0


def test_scan_headers_no_findings():
    headers = {
        "strict-transport-security": "max-age=31536000; includeSubDomains",
        "x-content-type-options": "nosniff",
        "x-frame-options": "DENY",
        "content-security-policy": "default-src 'self'",
        "x-xss-protection": "1; mode=block",
        "referrer-policy": "strict-origin-when-cross-origin",
        "permissions-policy": "geolocation=()",
        "cache-control": "no-store",
        "cross-origin-embedder-policy": "require-corp",
        "cross-origin-opener-policy": "same-origin-allow-popups",
        "cross-origin-resource-policy": "same-origin",
    }
    result = scan_headers(headers)
    severity_high = [f for f in result["findings"] if f.get("severity") == "HIGH"]
    if result["status"] == "fail":
        assert all(f.get("severity") != "HIGH" for f in result["findings"])
