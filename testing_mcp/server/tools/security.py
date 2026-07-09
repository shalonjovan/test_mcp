from __future__ import annotations

from fastmcp import FastMCP

from testing_mcp.security.headers import scan_headers_sync
from testing_mcp.security.sast import run_sast_scan
from testing_mcp.security.scanner import run_security_scan
from testing_mcp.security.secrets import scan_for_secrets
from testing_mcp.security.tls import check_tls
from testing_mcp.server.tools._helpers import _resolve_path, _resolve_url


def register_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    def security_scan(
        path: str = ".",
        scan_type: str = "all",
        url: str = "",
        hostname: str = "",
        port: int = 443,
    ) -> dict:
        """Run security scans on the project.

        Scan types: all, sast, secrets, headers, tls, deps, bandit, semgrep
        """
        root = _resolve_path(path)
        return run_security_scan(
            path=root,
            scan_type=scan_type,
            url=url,
            hostname=hostname,
            port=port,
        )

    @mcp.tool()
    def scan_sast(path: str = ".") -> dict:
        """Static analysis: detect SQLi, XSS, CSRF, SSRF, path traversal, weak crypto."""
        return run_sast_scan(path)

    @mcp.tool()
    def scan_secrets(path: str = ".") -> dict:
        """Scan for hardcoded secrets, API keys, tokens, and credentials."""
        return scan_for_secrets(path)

    @mcp.tool()
    def scan_headers(url: str) -> dict:
        """Check HTTP security headers (HSTS, CSP, X-Frame-Options, etc.)."""
        _resolve_url(url)
        return scan_headers_sync(url)

    @mcp.tool()
    def scan_tls(hostname: str, port: int = 443) -> dict:
        """Check TLS/SSL certificate validity and expiration."""
        return check_tls(hostname, port=port)
