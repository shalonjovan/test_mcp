from __future__ import annotations

import re
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False


SKIP_EXTENSIONS = {
    ".css", ".js", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico",
    ".woff", ".woff2", ".ttf", ".eot", ".mp4", ".webm", ".pdf",
    ".zip", ".tar", ".gz", ".bz2", ".doc", ".docx", ".xls", ".xlsx",
}

COMMON_FILES = [
    "robots.txt", "sitemap.xml", "security.txt", "humans.txt",
    "crossdomain.xml", ".well-known/security.txt",
    "favicon.ico",
]

ENDPOINT_PATTERNS = re.compile(
    r'(?:href|src|action|data-url|data-href|post)\s*=\s*["\']([^"\']+)["\']'
    r'|url\(["\']?([^"\'\)]+)["\']?\)'
    r'|@import\s+["\']([^"\']+)["\']',
    re.IGNORECASE,
)

ROUTE_PATTERNS_SRC = [
    (r"""['"`](/[a-zA-Z0-9_\-/.?=&]+)['"`]""", 1),
    (r"""path\s*\(\s*['"]([^'"]+)['"]""", 1),
    (r"""route\s*\(\s*['"]([^'"]+)['"]""", 1),
    (r"""@app\.(?:route|get|post|put|delete|patch)\s*\(\s*['"]([^'"]+)['"]""", 1),
    (r"""\.(?:get|post|put|delete|patch)\s*\(\s*['"]([^'"]+)['"]""", 1),
]


def _is_internal(url: str, base_domain: str) -> bool:
    try:
        return urlparse(url).netloc in ("", base_domain)
    except Exception:
        return False


def _normalize_url(href: str, base_url: str) -> str | None:
    joined = urljoin(base_url, href)
    parsed = urlparse(joined)
    if parsed.scheme not in ("http", "https", ""):
        return None
    path = parsed.path.split("?")[0]
    ext = Path(path).suffix.lower()
    if ext in SKIP_EXTENSIONS:
        return None
    return joined


def _extract_from_source(source: str, base_url: str) -> set[str]:
    urls: set[str] = set()
    for pattern, group_idx in ROUTE_PATTERNS_SRC:
        for m in re.finditer(pattern, source):
            path = m.group(group_idx)
            if path and not path.startswith("data:") and not path.startswith("javascript:"):
                full = _normalize_url(path, base_url)
                if full:
                    urls.add(full)
    return urls


def crawl_site(
    base_url: str,
    max_pages: int = 30,
    timeout: float = 5,
    crawl_source: bool = True,
) -> dict[str, Any]:
    if not HAS_HTTPX:
        return {"error": "httpx is required for crawling"}

    discovered: list[str] = []
    findings: list[dict[str, Any]] = []
    visited: set[str] = set()
    to_visit: list[str] = [base_url.rstrip("/") + "/"]
    host = urlparse(base_url).netloc

    try:
        with httpx.Client(verify=False, timeout=timeout, follow_redirects=True) as client:
            while to_visit and len(visited) < max_pages:
                url = to_visit.pop(0)
                if url in visited:
                    continue
                visited.add(url)
                discovered.append(url)

                try:
                    resp = client.get(url)
                    content_type = resp.headers.get("content-type", "")
                    source = resp.text

                    if "html" in content_type:
                        for m in ENDPOINT_PATTERNS.finditer(source):
                            for i in range(1, m.lastindex + 1):
                                href = m.group(i)
                                if href:
                                    full = _normalize_url(href, url)
                                    if full and full not in visited and full not in to_visit:
                                        if _is_internal(full, host):
                                            to_visit.append(full)

                    if crawl_source:
                        urls = _extract_from_source(source, url)
                        for u in urls:
                            if u not in visited and u not in to_visit:
                                if _is_internal(u, host):
                                    to_visit.append(u)

                    if resp.status_code >= 400:
                        findings.append({
                            "url": url,
                            "status": resp.status_code,
                            "type": "error-page",
                            "detail": f"HTTP {resp.status_code}",
                        })

                except (httpx.TimeoutException, httpx.RequestError):
                    continue

    except Exception as e:
        return {"error": str(e), "discovered": discovered, "findings": findings}

    # Check common files
    for common in COMMON_FILES:
        full_url = urljoin(base_url, common)
        try:
            with httpx.Client(verify=False, timeout=timeout) as client:
                resp = client.get(full_url)
                if resp.status_code == 200:
                    discovered.append(full_url)
                    findings.append({
                        "url": full_url,
                        "status": 200,
                        "type": "common-file",
                        "detail": f"Accessible: {common}",
                        "content_length": len(resp.content),
                    })
        except httpx.RequestError:
            continue

    return {
        "tool": "web-crawler",
        "base_url": base_url,
        "pages_visited": len(visited),
        "endpoints_discovered": discovered,
        "findings": findings,
    }
