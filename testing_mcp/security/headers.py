from __future__ import annotations

from typing import Any

import httpx

SECURITY_HEADERS = {
    "Strict-Transport-Security": {
        "description": "Enforces HTTPS connections",
        "expected": "max-age=",
        "severity": "HIGH",
    },
    "Content-Security-Policy": {
        "description": "Controls resources the browser can load",
        "expected": None,
        "severity": "HIGH",
    },
    "X-Content-Type-Options": {
        "description": "Prevents MIME type sniffing",
        "expected": "nosniff",
        "severity": "MEDIUM",
    },
    "X-Frame-Options": {
        "description": "Prevents clickjacking",
        "expected": "DENY",
        "severity": "MEDIUM",
    },
    "Referrer-Policy": {
        "description": "Controls referrer information sent with requests",
        "expected": None,
        "severity": "LOW",
    },
    "Permissions-Policy": {
        "description": "Controls browser API access",
        "expected": None,
        "severity": "LOW",
    },
    "X-XSS-Protection": {
        "description": "Cross-site scripting filter (deprecated but still relevant)",
        "expected": "1; mode=block",
        "severity": "MEDIUM",
    },
    "Cache-Control": {
        "description": "Controls caching behavior for sensitive data",
        "expected": "no-store",
        "severity": "MEDIUM",
    },
    "Access-Control-Allow-Origin": {
        "description": "CORS allowlist - overly permissive",
        "expected_not": "*",
        "severity": "MEDIUM",
    },
}


async def scan_headers(url: str, timeout: float = 15.0) -> dict[str, Any]:
    results: dict[str, Any] = {
        "url": url,
        "headers_found": {},
        "missing_headers": [],
        "weak_headers": [],
        "passed": True,
        "overall_score": 0,
        "total_checks": len(SECURITY_HEADERS),
    }

    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.get(url)
            headers = dict(response.headers)
    except httpx.ConnectError:
        return {"url": url, "error": f"Could not connect to {url}", "passed": False}
    except httpx.TimeoutException:
        return {"url": url, "error": f"Connection timed out", "passed": False}
    except Exception as e:
        return {"url": url, "error": str(e), "passed": False}

    for header_name, config in SECURITY_HEADERS.items():
        actual = headers.get(header_name, "")

        if not actual:
            results["missing_headers"].append({
                "header": header_name,
                "severity": config["severity"],
                "description": config["description"],
            })
            continue

        results["headers_found"][header_name] = actual

        expected = config.get("expected")
        expected_not = config.get("expected_not")

        if expected and expected not in actual:
            results["weak_headers"].append({
                "header": header_name,
                "severity": config["severity"],
                "description": f"{config['description']}: expected '{expected}', got '{actual[:80]}'",
            })
        elif expected_not and expected_not in actual:
            results["weak_headers"].append({
                "header": header_name,
                "severity": config["severity"],
                "description": f"{config['description']}: contains '{expected_not}' (overly permissive)",
            })

    missing_count = len(results["missing_headers"])
    weak_count = len(results["weak_headers"])
    passed_count = results["total_checks"] - missing_count - weak_count
    results["overall_score"] = round((passed_count / results["total_checks"]) * 100, 1) if results["total_checks"] else 0
    results["passed"] = missing_count == 0 and weak_count == 0

    return results


def scan_headers_sync(url: str, timeout: float = 15.0) -> dict[str, Any]:
    import asyncio
    return asyncio.run(scan_headers(url, timeout=timeout))
