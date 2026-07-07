from __future__ import annotations

import re
from typing import Any

HEADER_CHECKS: list[dict[str, Any]] = [
    {
        "id": "HDR-001",
        "name": "Missing Strict-Transport-Security",
        "severity": "MEDIUM",
        "header": "strict-transport-security",
        "description": "HSTS header not set; enables SSL stripping attacks",
        "remediation": "Add Strict-Transport-Security: max-age=31536000; includeSubDomains",
    },
    {
        "id": "HDR-002",
        "name": "Missing X-Content-Type-Options",
        "severity": "MEDIUM",
        "header": "x-content-type-options",
        "description": "MIME type sniffing protection not enabled",
        "remediation": "Add X-Content-Type-Options: nosniff",
    },
    {
        "id": "HDR-003",
        "name": "Missing X-Frame-Options",
        "severity": "MEDIUM",
        "header": "x-frame-options",
        "description": "Clickjacking protection not enabled",
        "remediation": "Add X-Frame-Options: DENY or SAMEORIGIN",
    },
    {
        "id": "HDR-004",
        "name": "Missing Content-Security-Policy",
        "severity": "HIGH",
        "header": "content-security-policy",
        "description": "CSP header not set; enables XSS and data injection",
        "remediation": "Add Content-Security-Policy with appropriate directives",
    },
    {
        "id": "HDR-005",
        "name": "Missing X-XSS-Protection",
        "severity": "LOW",
        "header": "x-xss-protection",
        "description": "XSS filter not enabled (deprecated but still used)",
        "remediation": "Add X-XSS-Protection: 1; mode=block",
    },
    {
        "id": "HDR-006",
        "name": "Missing Referrer-Policy",
        "severity": "LOW",
        "header": "referrer-policy",
        "description": "Referrer policy not set; may leak URL info",
        "remediation": "Add Referrer-Policy: strict-origin-when-cross-origin",
    },
    {
        "id": "HDR-007",
        "name": "Missing Permissions-Policy",
        "severity": "LOW",
        "header": "permissions-policy",
        "description": "Permissions policy not set; allows all browser features",
        "remediation": "Add Permissions-Policy to restrict camera, mic, geolocation etc.",
    },
    {
        "id": "HDR-008",
        "name": "Missing Cache-Control for sensitive pages",
        "severity": "MEDIUM",
        "header": "cache-control",
        "description": "Cache-Control not set for sensitive endpoints",
        "remediation": "Add Cache-Control: no-store, no-cache, must-revalidate for auth pages",
    },
    {
        "id": "HDR-009",
        "name": "Server Version Disclosure",
        "severity": "LOW",
        "header": "server",
        "description": "Server header reveals software version",
        "expected_value": None,
        "remediation": "Remove or obfuscate Server header to avoid version disclosure",
    },
    {
        "id": "HDR-010",
        "name": "X-Powered-By Present",
        "severity": "LOW",
        "header": "x-powered-by",
        "description": "Technology info leaked in X-Powered-By header",
        "expected_value": None,
        "remediation": "Remove X-Powered-By header in production",
    },
    {
        "id": "HDR-011",
        "name": "Weak HSTS max-age",
        "severity": "MEDIUM",
        "header": "strict-transport-security",
        "description": "HSTS max-age is less than the recommended 1 year (31536000s)",
        "expected_value": None,
        "remediation": "Set max-age to at least 31536000 (1 year)",
    },
    {
        "id": "HDR-012",
        "name": "Missing Cross-Origin-Embedder-Policy",
        "severity": "LOW",
        "header": "cross-origin-embedder-policy",
        "description": "COEP header not set; cross-origin isolation not enforced",
        "remediation": "Add Cross-Origin-Embedder-Policy: require-corp",
    },
    {
        "id": "HDR-013",
        "name": "Missing Cross-Origin-Opener-Policy",
        "severity": "LOW",
        "header": "cross-origin-opener-policy",
        "description": "COOP header not set; window opener attacks possible",
        "remediation": "Add Cross-Origin-Opener-Policy: same-origin-allow-popups",
    },
    {
        "id": "HDR-014",
        "name": "Missing Cross-Origin-Resource-Policy",
        "severity": "LOW",
        "header": "cross-origin-resource-policy",
        "description": "CORP header not set; cross-origin resource sharing may be unrestricted",
        "remediation": "Add Cross-Origin-Resource-Policy: same-origin or same-site",
    },
    {
        "id": "HDR-015",
        "name": "CSP Has 'unsafe-inline' or 'unsafe-eval'",
        "severity": "HIGH",
        "header": "content-security-policy",
        "description": "CSP allows 'unsafe-inline' or 'unsafe-eval' which weakens XSS protection",
        "expected_value": None,
        "remediation": "Use nonces or hashes instead of 'unsafe-inline'; avoid 'unsafe-eval'",
    },
]

RECOMMENDED_SET = {
    "strict-transport-security",
    "x-content-type-options",
    "x-frame-options",
    "content-security-policy",
    "referrer-policy",
    "permissions-policy",
}

VULNERABLE_CSP = re.compile(r"'unsafe-inline'|'unsafe-eval'", re.IGNORECASE)
HSTS_WEAK = re.compile(r"max-age\s*=\s*(\d+)", re.IGNORECASE)
SERVER_HEADER = re.compile(r"^(?:Apache|Nginx|IIS|Microsoft-IIS|Tomcat|Jetty|nginx|lighttpd)\b", re.IGNORECASE)


def scan_headers(
    response_headers: dict[str, str],
    url: str | None = None,
) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    headers_lower = {k.lower(): v for k, v in response_headers.items()}

    present = set(headers_lower.keys())

    for check in HEADER_CHECKS:
        header_name_lower = check["header"]
        header_present = header_name_lower in headers_lower
        header_value = headers_lower.get(header_name_lower, "")

        if check["id"] in ("HDR-001", "HDR-008"):
            if not header_present:
                findings.append({
                    "rule_id": check["id"],
                    "name": check["name"],
                    "severity": check["severity"],
                    "description": check["description"],
                    "remediation": check["remediation"],
                })
            continue

        if not header_present:
            findings.append({
                "rule_id": check["id"],
                "name": check["name"],
                "severity": check["severity"],
                "description": check["description"],
                "remediation": check["remediation"],
            })
        elif check["id"] == "HDR-009":
            if SERVER_HEADER.match(header_value):
                findings.append({
                    "rule_id": check["id"],
                    "name": check["name"],
                    "severity": check["severity"],
                    "description": check["description"],
                    "remediation": check["remediation"],
                    "detail": header_value.strip(),
                })
        elif check["id"] == "HDR-010":
            findings.append({
                "rule_id": check["id"],
                "name": check["name"],
                "severity": check["severity"],
                "description": check["description"],
                "remediation": check["remediation"],
                "detail": header_value.strip(),
            })
        elif check["id"] == "HDR-011":
            match = HSTS_WEAK.search(header_value)
            if match:
                max_age = int(match.group(1))
                if max_age < 31536000:
                    findings.append({
                        "rule_id": check["id"],
                        "name": check["name"],
                        "severity": check["severity"],
                        "description": check["description"],
                        "remediation": check["remediation"],
                        "detail": f"max-age={max_age}",
                    })
        elif check["id"] == "HDR-015":
            if VULNERABLE_CSP.search(header_value):
                findings.append({
                    "rule_id": check["id"],
                    "name": check["name"],
                    "severity": check["severity"],
                    "description": check["description"],
                    "remediation": check["remediation"],
                    "detail": header_value[:200],
                })

    missing = RECOMMENDED_SET - present
    status = "pass" if not findings else "fail"

    return {
        "url": url,
        "status": status,
        "missing": sorted(missing),
        "total_checks": len(HEADER_CHECKS),
        "checks_passed": len(HEADER_CHECKS) - len(findings),
        "findings": findings,
    }


def scan_headers_sync(url: str, timeout: float = 10) -> dict[str, Any]:
    import httpx
    try:
        with httpx.Client(verify=False, timeout=timeout) as client:
            resp = client.get(url, follow_redirects=True)
            return scan_headers(dict(resp.headers), url=url)
    except Exception as e:
        return {"url": url, "passed": False, "error": str(e), "findings": [], "missing": []}
