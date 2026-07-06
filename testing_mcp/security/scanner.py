from __future__ import annotations

from pathlib import Path
from typing import Any

from testing_mcp.security.headers import scan_headers_sync
from testing_mcp.security.sast import run_sast_scan
from testing_mcp.security.secrets import scan_for_secrets
from testing_mcp.security.tls import check_tls


def scan_dependency_files(path: str | Path = ".") -> dict[str, Any]:
    root = Path(path).resolve()
    result: dict[str, Any] = {
        "dependencies": [],
        "issues": [],
    }
    dep_files: dict[str, str] = {
        "requirements.txt": "pip",
        "Pipfile": "pipenv",
        "pyproject.toml": "poetry",
        "package.json": "npm",
        "Cargo.toml": "cargo",
        "go.mod": "go",
    }
    for filename, manager in dep_files.items():
        filepath = root / filename
        if filepath.exists():
            content = filepath.read_text()
            result["dependencies"].append({
                "file": filename,
                "manager": manager,
                "content_preview": content[:500],
            })
    return result


def run_bandit_scan(path: str | Path = ".") -> dict[str, Any]:
    import json
    import subprocess

    root = Path(path).resolve()
    result: dict[str, Any] = {"tool": "bandit", "issues": [], "summary": {}}
    try:
        proc = subprocess.run(
            ["python", "-m", "bandit", "-r", str(root), "-f", "json"],
            capture_output=True, text=True, timeout=120,
        )
    except subprocess.TimeoutExpired:
        result["error"] = "Bandit scan timed out"
        return result
    except FileNotFoundError:
        return result
    try:
        data = json.loads(proc.stdout)
        for issue in data.get("results", []):
            result["issues"].append({
                "filename": issue.get("filename", ""),
                "line": issue.get("line_number", 0),
                "severity": issue.get("issue_severity", "UNKNOWN"),
                "confidence": issue.get("issue_confidence", "UNKNOWN"),
                "cwe": issue.get("cwe", {}).get("id", ""),
                "test_id": issue.get("test_id", ""),
                "text": issue.get("issue_text", ""),
            })
        result["summary"] = {
            "total": len(result["issues"]),
            "high": sum(1 for i in result["issues"] if i["severity"] == "HIGH"),
            "medium": sum(1 for i in result["issues"] if i["severity"] == "MEDIUM"),
            "low": sum(1 for i in result["issues"] if i["severity"] == "LOW"),
        }
    except (json.JSONDecodeError, KeyError) as e:
        result["error"] = f"Failed to parse Bandit output: {e}"
    return result


def run_semgrep_scan(path: str | Path = ".") -> dict[str, Any]:
    import json
    import subprocess

    root = Path(path).resolve()
    result: dict[str, Any] = {"tool": "semgrep", "issues": [], "summary": {}}
    try:
        proc = subprocess.run(
            ["semgrep", "--json", "--quiet", str(root)],
            capture_output=True, text=True, timeout=120,
        )
    except subprocess.TimeoutExpired:
        result["error"] = "Semgrep scan timed out"
        return result
    except FileNotFoundError:
        return result
    try:
        data = json.loads(proc.stdout)
        for issue in data.get("results", []):
            result["issues"].append({
                "filename": issue.get("path", ""),
                "line": issue.get("start", {}).get("line", 0),
                "severity": issue.get("extra", {}).get("severity", "UNKNOWN"),
                "check_id": issue.get("check_id", ""),
                "message": issue.get("extra", {}).get("message", ""),
            })
        result["summary"] = {
            "total": len(result["issues"]),
            "error": sum(1 for i in result["issues"] if i["severity"] == "ERROR"),
            "warning": sum(1 for i in result["issues"] if i["severity"] == "WARNING"),
            "info": sum(1 for i in result["issues"] if i["severity"] == "INFO"),
        }
    except (json.JSONDecodeError, KeyError) as e:
        result["error"] = f"Failed to parse Semgrep output: {e}"
    return result


def run_trivy_scan(path: str | Path = ".") -> dict[str, Any]:
    import json
    import subprocess

    root = Path(path).resolve()
    result: dict[str, Any] = {"tool": "trivy", "issues": [], "summary": {}}
    try:
        proc = subprocess.run(
            ["trivy", "fs", "--format", "json", "--quiet", str(root)],
            capture_output=True, text=True, timeout=300,
        )
    except subprocess.TimeoutExpired:
        result["error"] = "Trivy scan timed out after 300s"
        return result
    except FileNotFoundError:
        return result
    try:
        data = json.loads(proc.stdout)
        for vuln in data.get("Results", []):
            target = vuln.get("Target", "")
            for issue in vuln.get("Vulnerabilities", []):
                result["issues"].append({
                    "target": target,
                    "pkg": issue.get("PkgName", ""),
                    "severity": issue.get("Severity", "UNKNOWN"),
                    "cve": issue.get("VulnerabilityID", ""),
                    "installed": issue.get("InstalledVersion", ""),
                    "fixed": issue.get("FixedVersion", ""),
                    "title": issue.get("Title", ""),
                })
        result["summary"] = {
            "total": len(result["issues"]),
            "critical": sum(1 for i in result["issues"] if i["severity"] == "CRITICAL"),
            "high": sum(1 for i in result["issues"] if i["severity"] == "HIGH"),
            "medium": sum(1 for i in result["issues"] if i["severity"] == "MEDIUM"),
            "low": sum(1 for i in result["issues"] if i["severity"] == "LOW"),
        }
    except (json.JSONDecodeError, KeyError) as e:
        result["error"] = f"Failed to parse Trivy output: {e}"
    return result


def run_security_scan(
    path: str | Path = ".",
    scan_type: str = "all",
    url: str = "",
    hostname: str = "",
    port: int = 443,
) -> dict[str, Any]:
    root = Path(path).resolve()
    result: dict[str, Any] = {"project": str(root), "scan_type": scan_type}

    if scan_type in ("all", "static", "sast"):
        result["sast"] = run_sast_scan(root)

    if scan_type in ("all", "secrets"):
        result["secrets"] = scan_for_secrets(root)

    if scan_type in ("all", "deps", "dependencies"):
        result["dependencies"] = scan_dependency_files(root)
        result["trivy"] = run_trivy_scan(root)

    if scan_type in ("all", "headers"):
        if url:
            result["headers"] = scan_headers_sync(url)
        else:
            result["headers"] = {"error": "URL required for header scan", "passed": False}

    if scan_type in ("all", "tls"):
        if hostname:
            result["tls"] = check_tls(hostname, port=port)
        elif url:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            result["tls"] = check_tls(parsed.hostname or hostname, port=port)
        else:
            result["tls"] = {"error": "URL or hostname required for TLS check", "passed": False}

    if scan_type in ("all", "bandit"):
        result["bandit"] = run_bandit_scan(root)

    if scan_type in ("all", "semgrep"):
        result["semgrep"] = run_semgrep_scan(root)

    return result
