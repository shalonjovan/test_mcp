from __future__ import annotations

from typing import Any
from urllib.parse import urljoin, urlparse, urlencode, parse_qs

from testing_mcp.security.headers import scan_headers

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False


SKIP_EXTENSIONS = {".css", ".js", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".woff", ".woff2", ".ttf", ".eot", ".mp4", ".webm", ".pdf", ".zip", ".tar", ".gz"}

COMMON_ENDPOINTS = [
    "/admin", "/login", "/api", "/graphql", "/swagger", "/api-docs",
    "/health", "/status", "/metrics", "/actuator", "/.env", "/config",
    "/backup", "/console", "/debug", "/test", "/.git/config",
    "/wp-admin", "/wp-content", "/phpmyadmin", "/server-status",
]

TECH_REGEXES: dict[str, list[str]] = {
    "PHP": [r"X-Powered-By:\s*PHP", r"\.php"],
    "Node.js": [r"x-powered-by:\s*Express", r"Server:\s*Node"],
    "Python": [r"WSGI", r"Python/", r"Django", r"Flask", r"FastAPI"],
    "Java": [r"Java", r"Apache Tomcat", r"Spring", r"JBoss"],
    "ASP.NET": [r"ASP\.NET", r"X-AspNet-Version", r"X-AspNetMvc-Version"],
    "Ruby": [r"Ruby", r"Rails", r"Passenger"],
    "WordPress": [r"wp-content", r"wp-json", r"WordPress"],
    "Nginx": [r"nginx"],
    "Apache": [r"Apache"],
    "Cloudflare": [r"cloudflare", r"__cfduid"],
}


def detect_tech(resp: httpx.Response) -> list[str]:
    detected: list[str] = []
    combined = ""
    for k, v in resp.headers.items():
        combined += f"{k}: {v}\n"
    combined += resp.text[:5000].lower()
    for tech, patterns in TECH_REGEXES.items():
        import re
        for pat in patterns:
            if re.search(pat, combined, re.IGNORECASE):
                detected.append(tech)
                break
    return detected


def test_endpoint(
    client: httpx.Client,
    base_url: str,
    endpoint: str,
    timeout: float = 5,
) -> dict[str, Any] | None:
    url = urljoin(base_url, endpoint)
    ext = "." + urlparse(url).path.rsplit(".", 1)[-1].lower() if "." in urlparse(url).path else ""
    if ext in SKIP_EXTENSIONS:
        return None

    try:
        resp = client.get(url, timeout=timeout, follow_redirects=False)
    except (httpx.TimeoutException, httpx.RequestError):
        return None

    return {
        "url": url,
        "status": resp.status_code,
        "content_length": len(resp.content),
        "content_type": resp.headers.get("content-type", ""),
        "headers_present": list(resp.headers.keys()),
    }


def test_common_paths(
    base_url: str,
    timeout: float = 5,
    max_retries: int = 2,
) -> dict[str, Any]:
    if not HAS_HTTPX:
        return {"error": "httpx is required for dynamic scanning"}

    results: dict[str, Any] = {
        "tool": "dast",
        "base_url": base_url,
        "endpoints": [],
        "findings": [],
        "technologies": [],
    }

    try:
        with httpx.Client(verify=False, http2=True) as client:
            # Detect tech from homepage
            try:
                home = client.get(base_url, timeout=timeout, follow_redirects=True)
                results["technologies"] = detect_tech(home)
                # Header scan
                hdr_scan = scan_headers(dict(home.headers), url=base_url)
                findings = hdr_scan.get("findings", [])
                for f in findings:
                    f["source"] = "header-scan"
                    results["findings"].append(f)
            except httpx.RequestError:
                pass

            # Test common endpoints
            for endpoint in COMMON_ENDPOINTS:
                result = test_endpoint(client, base_url, endpoint, timeout)
                if result:
                    results["endpoints"].append(result)
                    if result["status"] in (200, 204, 301, 302, 401, 403):
                        findings = _analyze_endpoint(result, base_url)
                        for f in findings:
                            results["findings"].append({
                                "source": "endpoint-discovery",
                                "severity": f["severity"],
                                "name": f["name"],
                                "url": result["url"],
                                "status": result["status"],
                                "detail": f.get("detail", ""),
                            })

    except Exception as e:
        results["error"] = str(e)

    return results


def _analyze_endpoint(result: dict[str, Any], base_url: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    path = urlparse(result["url"]).path
    status = result["status"]

    if path in ("/.env", "/.git/config", "/backup", "/config", "/.git"):
        findings.append({
            "severity": "CRITICAL",
            "name": "Sensitive File Exposed",
            "detail": f"Sensitive path returned {status}",
        })
    elif path in ("/admin", "/console", "/phpmyadmin", "/debug"):
        findings.append({
            "severity": "HIGH",
            "name": "Admin Panel Exposed",
            "detail": f"Admin interface returned {status}",
        })
    elif path in ("/health", "/status", "/metrics", "/actuator"):
        findings.append({
            "severity": "MEDIUM",
            "name": "Information Leak Endpoint",
            "detail": f"Info endpoint returned {status}",
        })
    elif status == 401 and path != base_url and path not in ("/login",):
        findings.append({
            "severity": "MEDIUM",
            "name": "Authenticated Endpoint Discovered",
            "detail": f"Endpoint requires authentication: {path}",
        })
    elif status in (301, 302):
        findings.append({
            "severity": "LOW",
            "name": "Redirect Endpoint",
            "detail": f"Redirects to: {result.get('location', 'unknown')}",
        })

    return findings


def test_sqli_endpoint(url: str, param: str, value: str, timeout: float = 5) -> dict[str, Any]:
    if not HAS_HTTPX:
        return {"error": "httpx is required"}

    sqli_payloads = ["'", "\"", "1' OR '1'='1", "1\" OR \"1\"=\"1", "' OR 1=1--", "' UNION SELECT NULL--"]
    errors = ["sql", "syntax", "mysql", "oracle", "postgres", "odbc", "driver", "db2", "microsoft"]

    result: dict[str, Any] = {"url": url, "payloads_tested": [], "vulnerable": False}

    try:
        with httpx.Client(verify=False, timeout=timeout) as client:
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            params[param] = [value]

            for payload in sqli_payloads:
                try:
                    test_params = dict(params)
                    test_params[param] = [payload]
                    test_url = parsed._replace(query=urlencode(test_params, doseq=True)).geturl()

                    resp = client.get(test_url)
                    result["payloads_tested"].append(payload)

                    body_lower = resp.text.lower()
                    for err in errors:
                        if err in body_lower:
                            result["vulnerable"] = True
                            result["error_hint"] = err
                            result["trigger_payload"] = payload
                            break
                    if result.get("vulnerable"):
                        break
                except httpx.RequestError:
                    continue
    except Exception as e:
        result["error"] = str(e)

    return result


def test_xss_endpoint(url: str, param: str, value: str, timeout: float = 5) -> dict[str, Any]:
    if not HAS_HTTPX:
        return {"error": "httpx is required"}

    xss_payloads = [
        "<script>alert(1)</script>",
        "<img src=x onerror=alert(1)>",
        "\"><script>alert(1)</script>",
        "';alert(1);//",
    ]

    result: dict[str, Any] = {"url": url, "payloads_tested": [], "vulnerable": False}

    try:
        with httpx.Client(verify=False, timeout=timeout) as client:
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            params[param] = [value]

            for payload in xss_payloads:
                try:
                    test_params = dict(params)
                    test_params[param] = [payload]
                    test_url = parsed._replace(query=urlencode(test_params, doseq=True)).geturl()

                    resp = client.get(test_url)
                    result["payloads_tested"].append(payload)

                    if payload in resp.text and "html" in resp.headers.get("content-type", "").lower():
                        result["vulnerable"] = True
                        result["trigger_payload"] = payload
                        break
                except httpx.RequestError:
                    continue
    except Exception as e:
        result["error"] = str(e)

    return result


def run_dast_scan(
    url: str,
    check_sqli: bool = False,
    check_xss: bool = False,
    sqli_param: str | None = None,
    sqli_value: str | None = None,
    xss_param: str | None = None,
    xss_value: str | None = None,
    timeout: float = 5,
) -> dict[str, Any]:
    results = test_common_paths(url, timeout=timeout)

    if check_sqli and sqli_param:
        sqli_result = test_sqli_endpoint(url, sqli_param, sqli_value or "1", timeout)
        results["sqli_test"] = sqli_result
    if check_xss and xss_param:
        xss_result = test_xss_endpoint(url, xss_param, xss_value or "1", timeout)
        results["xss_test"] = xss_result

    return results
