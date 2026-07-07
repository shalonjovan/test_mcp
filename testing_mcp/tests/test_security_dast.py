from testing_mcp.security.dast import _analyze_endpoint, COMMON_ENDPOINTS, SKIP_EXTENSIONS, detect_tech


def test_common_endpoints_defined():
    assert len(COMMON_ENDPOINTS) > 10
    assert "/admin" in COMMON_ENDPOINTS
    assert "/.env" in COMMON_ENDPOINTS
    assert "/.git/config" in COMMON_ENDPOINTS


def test_skip_extensions():
    assert ".css" in SKIP_EXTENSIONS
    assert ".js" in SKIP_EXTENSIONS
    assert ".png" in SKIP_EXTENSIONS


def test_analyze_endpoint_admin():
    result = _analyze_endpoint({"url": "https://example.com/admin", "status": 200}, "https://example.com")
    sev_high = [f for f in result if f["severity"] == "HIGH"]
    assert len(sev_high) > 0


def test_analyze_endpoint_sensitive():
    result = _analyze_endpoint({"url": "https://example.com/.env", "status": 200}, "https://example.com")
    sev_critical = [f for f in result if f["severity"] == "CRITICAL"]
    assert len(sev_critical) > 0


def test_analyze_endpoint_health():
    result = _analyze_endpoint({"url": "https://example.com/health", "status": 200}, "https://example.com")
    sev_medium = [f for f in result if f["severity"] == "MEDIUM"]
    assert len(sev_medium) > 0


def test_analyze_endpoint_clean():
    result = _analyze_endpoint({"url": "https://example.com/about", "status": 200}, "https://example.com")
    assert len(result) == 0


def test_detect_tech_php():
    class MockResp:
        headers = {"X-Powered-By": "PHP/7.4"}
        text = "<html><body>hello</body></html>"
    tech = detect_tech(MockResp())
    assert "PHP" in tech


def test_detect_tech_python():
    class MockResp:
        headers = {"Server": "WSGIServer/0.2"}
        text = ""
    tech = detect_tech(MockResp())
    assert "Python" in tech


def test_detect_tech_nginx():
    class MockResp:
        headers = {"Server": "nginx/1.20.1"}
        text = ""
    tech = detect_tech(MockResp())
    assert "Nginx" in tech


def test_detect_tech_wordpress():
    class MockResp:
        headers = {}
        text = '<html><link href="/wp-content/themes/style.css" /></html>'
    tech = detect_tech(MockResp())
    assert "WordPress" in tech
