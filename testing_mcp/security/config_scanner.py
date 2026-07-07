from __future__ import annotations

import re
from pathlib import Path
from typing import Any

DOCKER_CHECKS: list[dict[str, Any]] = [
    {
        "id": "DOCKER-001",
        "name": "Container runs as root",
        "severity": "HIGH",
        "description": "User directive not set; container may run as root",
        "pattern": r"^FROM\s",
        "negative_pattern": r"^USER\s+\d+",
        "remediation": "Add USER <non-root-user> directive after FROM",
    },
    {
        "id": "DOCKER-002",
        "name": "Sensitive port exposed without restriction",
        "severity": "MEDIUM",
        "description": "Port 22 (SSH) exposed in container",
        "pattern": r"EXPOSE\s+22\b",
        "remediation": "Avoid exposing SSH port; use alternative access methods",
    },
    {
        "id": "DOCKER-003",
        "name": "APT without --no-install-recommends",
        "severity": "LOW",
        "description": "apt-get install used without --no-install-recommends",
        "pattern": r"apt-get\s+install\s",
        "negative_pattern": r"--no-install-recommends",
        "remediation": "Add --no-install-recommends to reduce attack surface",
    },
    {
        "id": "DOCKER-004",
        "name": "ADD instruction used instead of COPY",
        "severity": "LOW",
        "description": "ADD has extra features (URL extraction, tar auto-extraction); use COPY for local files",
        "pattern": r"^ADD\s",
        "remediation": "Use COPY instead of ADD unless URL/tar extraction is needed",
    },
    {
        "id": "DOCKER-005",
        "name": "apt-get update without cache cleanup",
        "severity": "LOW",
        "description": "apt-get update not followed by rm -rf /var/lib/apt/lists/*",
        "pattern": r"apt-get\s+update",
        "negative_pattern": r"rm\s+.*/var/lib/apt/lists/",
        "remediation": "Chain apt-get update with clean up: rm -rf /var/lib/apt/lists/*",
    },
    {
        "id": "DOCKER-006",
        "name": "Wget/curl fetching from HTTP",
        "severity": "MEDIUM",
        "description": "Files downloaded over unencrypted HTTP",
        "pattern": r"(?:wget|curl)\s+http://",
        "remediation": "Use HTTPS for all downloads to prevent MITM attacks",
    },
    {
        "id": "DOCKER-007",
        "name": "ENV with secret value",
        "severity": "HIGH",
        "description": "Sensitive values set as ENV in Dockerfile",
        "pattern": r"ENV\s+.*(?:password|secret|token|key|credential)\s*=",
        "remediation": "Use Docker secrets or build args instead of ENV for secrets",
    },
    {
        "id": "DOCKER-008",
        "name": "COPY --chmod with world-writable",
        "severity": "MEDIUM",
        "description": "Copy with world-writable permissions",
        "pattern": r"COPY\s+--chmod=0?777\b",
        "remediation": "Avoid world-writable permissions; use more restrictive chmod",
    },
    {
        "id": "DOCKER-009",
        "name": "Latest tag used",
        "severity": "MEDIUM",
        "description": "Using :latest tag; non-reproducible builds",
        "pattern": r"FROM\s+\S+:\s*latest\s*$",
        "remediation": "Pin to a specific version tag for reproducible builds",
    },
    {
        "id": "DOCKER-010",
        "name": "No HEALTHCHECK directive",
        "severity": "LOW",
        "description": "HEALTHCHECK not defined for the container",
        "pattern": r"^FROM\s",
        "negative_pattern": r"^HEALTHCHECK\s",
        "remediation": "Add HEALTHCHECK to improve container lifecycle management",
    },
]

K8S_CHECKS: list[dict[str, Any]] = [
    {
        "id": "K8S-001",
        "name": "Privileged container",
        "severity": "CRITICAL",
        "description": "Container runs in privileged mode",
        "pattern": r"privileged:\s*true",
        "remediation": "Avoid privileged mode; use securityContext with specific capabilities",
    },
    {
        "id": "K8S-002",
        "name": "Container runs as root",
        "severity": "HIGH",
        "description": "runAsNonRoot not set or set to false",
        "pattern": r"(?:containers|initContainers):",
        "negative_pattern": r"runAsNonRoot:\s*true",
        "remediation": "Set securityContext.runAsNonRoot: true and runAsUser: >1000",
    },
    {
        "id": "K8S-003",
        "name": "Host network access",
        "severity": "HIGH",
        "description": "Pod has hostNetwork access",
        "pattern": r"hostNetwork:\s*true",
        "remediation": "Avoid hostNetwork unless absolutely necessary",
    },
    {
        "id": "K8S-004",
        "name": "Host PID/IPC access",
        "severity": "HIGH",
        "description": "Pod has hostPID or hostIPC access",
        "pattern": r"host(?:PID|IPC):\s*true",
        "remediation": "Avoid hostPID and hostIPC unless essential",
    },
    {
        "id": "K8S-005",
        "name": "Empty securityContext",
        "severity": "MEDIUM",
        "description": "Pod or container has no securityContext defined",
        "pattern": r"(?:containers|initContainers):",
        "negative_pattern": r"securityContext:",
        "remediation": "Define securityContext with least-privilege settings",
    },
    {
        "id": "K8S-006",
        "name": "Container has readOnlyRootFilesystem not set",
        "severity": "MEDIUM",
        "description": "readOnlyRootFilesystem not set to true",
        "pattern": r"containers:",
        "negative_pattern": r"readOnlyRootFilesystem:\s*true",
        "remediation": "Set securityContext.readOnlyRootFilesystem: true",
    },
    {
        "id": "K8S-007",
        "name": "Secrets via env vars",
        "severity": "MEDIUM",
        "description": "environment variables used for sensitive data instead of volumes",
        "pattern": r"env:\s*\n.*(?:SECRET|PASSWORD|TOKEN|KEY)",
        "remediation": "Mount secrets as volumes instead of environment variables",
    },
    {
        "id": "K8S-008",
        "name": "Image tag :latest or missing",
        "severity": "MEDIUM",
        "description": "Container image uses :latest tag or no tag",
        "pattern": r"image:\s+\S+:\s*(?:latest)?\s*$",
        "remediation": "Pin image to a specific version tag",
    },
    {
        "id": "K8S-009",
        "name": "AllowPrivilegeEscalation not set",
        "severity": "MEDIUM",
        "description": "allowPrivilegeEscalation not explicitly set to false",
        "pattern": r"containers:",
        "negative_pattern": r"allowPrivilegeEscalation:\s*false",
        "remediation": "Set securityContext.allowPrivilegeEscalation: false",
    },
    {
        "id": "K8S-010",
        "name": "CAP_SYS_ADMIN capability added",
        "severity": "HIGH",
        "description": "SYS_ADMIN capability granted to container",
        "pattern": r"(?:add|capAdd):\s*\[.*SYS_ADMIN",
        "remediation": "Remove SYS_ADMIN capability; it grants near-root privileges",
    },
]

CI_CHECKS: list[dict[str, Any]] = [
    {
        "id": "CI-001",
        "name": "Hardcoded secret in CI config",
        "severity": "CRITICAL",
        "description": "Sensitive value hardcoded in CI/CD config",
        "pattern": r"(?:password|secret|token|key|credential)\s*[=:]\s*[^A-Za-z0-9\s]{1,3}[^\s]{4,}[^A-Za-z0-9\s]{1,3}",
        "remediation": "Use CI/CD secrets manager (e.g. GitHub Secrets, GitLab CI Variables)",
    },
    {
        "id": "CI-002",
        "name": "Wide permissions on checkout step",
        "severity": "LOW",
        "description": "Checkout may persist credentials for subsequent steps",
        "pattern": r"actions/checkout",
        "remediation": "Set persist-credentials: false for checkout action if not needed",
    },
    {
        "id": "CI-003",
        "name": "Unpinned third-party action",
        "severity": "MEDIUM",
        "description": "Third-party action used without commit SHA pinning",
        "pattern": r"uses:\s+\S+@\w+",
        "negative_pattern": r"uses:\s+\S+@[0-9a-f]{40}",
        "remediation": "Pin actions to full commit SHA instead of version tags",
    },
    {
        "id": "CI-004",
        "name": "Write-all permission token",
        "severity": "HIGH",
        "description": "GITHUB_TOKEN has push/write permissions without restriction",
        "pattern": r"permissions:\s*write-all",
        "remediation": "Restrict permissions to the minimum required scope",
    },
    {
        "id": "CI-005",
        "name": "Dangerous script injection",
        "severity": "HIGH",
        "description": "Event payload data used in script without sanitization",
        "pattern": r"run:\s*.*\${{.*github\.event",
        "remediation": "Use intermediate environment variables to sanitize event payload injection",
    },
]

IGNORE_DIRS = {"node_modules", ".git", "__pycache__", "venv", ".venv"}


def scan_file(filepath: Path, checks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    try:
        content = filepath.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return findings

    for check in checks:
        has_pattern = bool(re.search(check["pattern"], content, re.MULTILINE))
        has_negative = False
        if check.get("negative_pattern"):
            has_negative = bool(re.search(check["negative_pattern"], content, re.MULTILINE))

        if "negative_pattern" in check:
            if has_pattern and not has_negative:
                if check["id"] in ("DOCKER-001", "DOCKER-010", "DOCKER-003", "DOCKER-005"):
                    findings.append({
                        "rule_id": check["id"],
                        "name": check["name"],
                        "severity": check["severity"],
                        "description": check["description"],
                        "file": str(filepath),
                        "remediation": check["remediation"],
                    })
                else:
                    findings.append({
                        "rule_id": check["id"],
                        "name": check["name"],
                        "severity": check["severity"],
                        "description": check["description"],
                        "file": str(filepath),
                        "remediation": check["remediation"],
                    })
            continue

        if has_pattern:
            for line_no, line in enumerate(content.splitlines(), 1):
                m = re.search(check["pattern"], line, re.IGNORECASE)
                if m:
                    findings.append({
                        "rule_id": check["id"],
                        "name": check["name"],
                        "severity": check["severity"],
                        "description": check["description"],
                        "file": str(filepath),
                        "line": line_no,
                        "match": m.group()[:120],
                        "remediation": check["remediation"],
                    })
                    break

    return findings


def scan_directory(path: str | Path = ".") -> dict[str, Any]:
    root = Path(path).resolve()
    results: dict[str, Any] = {
        "tool": "config-scanner",
        "scanned_files": [],
        "findings": [],
        "summary": {"critical": 0, "high": 0, "medium": 0, "low": 0},
    }

    dockerfile_patterns = ["Dockerfile", "Dockerfile.*", "*.dockerfile"]
    k8s_patterns = ["*.yaml", "*.yml"]

    docker_files: list[Path] = []
    k8s_files: list[Path] = []
    ci_files: list[Path] = []

    for f in root.rglob("*"):
        rel_parts = f.relative_to(root).parts
        if any(part in IGNORE_DIRS for part in rel_parts):
            continue
        name_lower = f.name.lower()

        if f.is_file():
            if name_lower == "dockerfile" or name_lower.startswith("dockerfile.") or name_lower.endswith(".dockerfile"):
                docker_files.append(f)
            elif f.suffix in (".yaml", ".yml"):
                k8s_files.append(f)
            if f.suffix in (".yaml", ".yml", ".json") and "ci" in name_lower:
                ci_files.append(f)
            if f.name in (".github/workflows", "gitlab-ci.yml", ".cirrus.yml", "Jenkinsfile"):
                ci_files.append(f)

    for filepath in docker_files:
        findings = scan_file(filepath, DOCKER_CHECKS)
        if findings:
            results["findings"].extend(findings)
        results["scanned_files"].append(str(filepath))

    for filepath in k8s_files:
        if not any(p in str(filepath) for p in ["/ci/", "/cicd/", "/.github/"]):
            try:
                content = filepath.read_text(encoding="utf-8", errors="ignore")
                if re.search(r"(?:kind:|apiVersion:)|\b(?:Pod|Deployment|Service|StatefulSet|DaemonSet|ConfigMap|Secret)\b", content):
                    findings = scan_file(filepath, K8S_CHECKS)
                    if findings:
                        results["findings"].extend(findings)
                    results["scanned_files"].append(str(filepath))
            except OSError:
                continue

    for filepath in ci_files:
        findings = scan_file(filepath, CI_CHECKS)
        if findings:
            results["findings"].extend(findings)
        results["scanned_files"].append(str(filepath))

    for f in results["findings"]:
        sev = f["severity"].lower()
        if sev in results["summary"]:
            results["summary"][sev] += 1

    results["summary"]["total"] = len(results["findings"])
    return results
