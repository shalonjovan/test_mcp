from testing_mcp.security.web_crawler import COMMON_FILES, SKIP_EXTENSIONS, _normalize_url, _is_internal, ENDPOINT_PATTERNS


def test_common_files_defined():
    assert len(COMMON_FILES) >= 5
    assert "robots.txt" in COMMON_FILES
    assert "sitemap.xml" in COMMON_FILES


def test_skip_extensions():
    assert ".css" in SKIP_EXTENSIONS
    assert ".png" in SKIP_EXTENSIONS


def test_normalize_url():
    result = _normalize_url("/about", "https://example.com")
    assert result == "https://example.com/about"


def test_normalize_url_relative():
    result = _normalize_url("about", "https://example.com/foo/")
    assert result is not None


def test_normalize_url_skip_ext():
    result = _normalize_url("image.png", "https://example.com/")
    assert result is None


def test_normalize_url_skip_data():
    result = _normalize_url("data:image/png;base64,abc", "https://example.com/")
    assert result is None


def test_is_internal_same_domain():
    assert _is_internal("/about", "example.com") is True


def test_is_internal_external():
    assert _is_internal("https://other.com", "example.com") is False


def test_endpoint_patterns_finds_href():
    text = '<a href="/contact">Contact</a>'
    matches = ENDPOINT_PATTERNS.findall(text)
    flat = [m for t in matches for m in t if m]
    assert "/contact" in flat


def test_endpoint_patterns_finds_src():
    text = '<img src="/logo.png" />'
    matches = ENDPOINT_PATTERNS.findall(text)
    flat = [m for t in matches for m in t if m]
    assert "/logo.png" in flat


def test_endpoint_patterns_finds_action():
    text = '<form action="/submit">'
    matches = ENDPOINT_PATTERNS.findall(text)
    flat = [m for t in matches for m in t if m]
    assert "/submit" in flat
