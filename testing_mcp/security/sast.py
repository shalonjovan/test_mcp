from __future__ import annotations

import re
from pathlib import Path
from typing import Any

SAST_RULES: list[dict[str, Any]] = [
    {
        "id": "SQLI-001",
        "name": "SQL Injection - string concatenation",
        "severity": "HIGH",
        "description": "SQL query built via string concatenation",
        "patterns": [
            r'(?i)(?:execute|query|raw|run)\s*\(\s*["\'].*\b(?:SELECT|INSERT|UPDATE|DELETE)\b.*["\']\s*\+',
            r'(?i)(?:cursor|db|conn|pool)\.(?:execute|exec|query)\(\s*f["\']',
            r'(?i)\+.*\b(?:WHERE|AND|OR|SET|VALUES)\b.*\+',
        ],
        "remediation": "Use parameterized queries / prepared statements instead of string concatenation",
    },
    {
        "id": "SQLI-002",
        "name": "SQL Injection - f-string query",
        "severity": "HIGH",
        "description": "SQL query built with f-string or format()",
        "patterns": [
            r'(?i)(?:execute|query|raw)\s*\(\s*f["\'].*\b(?:SELECT|INSERT|UPDATE|DELETE)\b',
            r'(?i)(?:execute|query|raw)\s*\(\s*["\'].*\{\}.*["\']\.format\(',
            r'(?i)(?:execute|query|raw)\s*\(\s*["\'].*%s.*["\']\s*%',
        ],
        "remediation": "Use parameterized queries with ? or %s placeholders",
    },
    {
        "id": "XSS-001",
        "name": "Cross-Site Scripting - unsafe HTML",
        "severity": "HIGH",
        "description": "Potentially unsafe HTML injection via innerHTML or similar",
        "patterns": [
            r'(?i)\.innerHTML\s*=\s*',
            r'(?i)\.outerHTML\s*=\s*',
            r'(?i)(?:document\.write|writeln)\s*\(',
            r'(?i)v-html\s*=',
            r'(?i)dangerouslySetInnerHTML',
            r'(?i)insertAdjacentHTML',
        ],
        "remediation": "Use textContent/innerText or sanitize input before inserting HTML",
    },
    {
        "id": "XSS-002",
        "name": "Cross-Site Scripting - unsafe template",
        "severity": "MEDIUM",
        "description": "Template variable rendered without escaping",
        "patterns": [
            r'(?i){{.*\|?\s*safe\s*}}',
            r'(?i)\{%\s*(?:autoescape|raw)\s+off\s*%\}',
            r'(?i)\.html\(\s*["\']',
        ],
        "remediation": "Ensure template variables are escaped by default; avoid |safe filter",
    },
    {
        "id": "CSRF-001",
        "name": "Missing CSRF Protection",
        "severity": "MEDIUM",
        "description": "Form or AJAX endpoint without CSRF token",
        "patterns": [
            r'(?i)@csrf_exempt',
            r'(?i)csrf_exempt\s*=\s*True',
            r'(?i)@method_decorator.*csrf_exempt',
            r'(?i)protect_from_forgery\s*(?::|=>)?\s*false',
        ],
        "remediation": "Enable CSRF protection; use CSRF tokens in forms",
    },
    {
        "id": "SSRF-001",
        "name": "Server-Side Request Forgery",
        "severity": "HIGH",
        "description": "URL constructed from user input without validation",
        "patterns": [
            r'(?i)requests?\.(?:get|post|put|delete)\(\s*[f"\'][^"\']*\{',
            r'(?i)urllib\.request\.urlopen\(\s*[f"\'][^"\']*\{',
            r'(?i)httpx\.(?:get|post|put|delete|request)\(\s*[f"\'][^"\']*\{',
            r'(?i)(?:fetch|axios)\(\s*[`\'][^`\']*\$\{',
        ],
        "remediation": "Validate and sanitize URLs; use an allowlist of permitted hosts",
    },
    {
        "id": "PT-001",
        "name": "Path Traversal",
        "severity": "HIGH",
        "description": "File path constructed from user input",
        "patterns": [
            r'(?i)open\(\s*[f"\'][^"\']*\{',
            r'(?i)Path\(\s*[f"\'][^"\']*\{',
            r'(?i)os\.path\.(?:join|exists|isfile)\(\s*[f"\'][^"\']*\{',
            r'(?i)__import__\(\s*["\'][^"\']*["\']\s*\)',
        ],
        "remediation": "Use allowlisted paths; sanitize user input to remove ../ patterns",
    },
    {
        "id": "CRYPTO-001",
        "name": "Weak Cryptography",
        "severity": "MEDIUM",
        "description": "Use of weak/outdated cryptographic algorithm",
        "patterns": [
            r'(?i)(?:md5|sha1)\s*\(',
            r'(?i)hashlib\.md5',
            r'(?i)hashlib\.sha1',
            r'(?i)Cipher\.(?:DES|RC2|RC4)',
            r'(?i)crypto\.create(?:Cipher|Decipher)iv.*des',
            r'(?i)\.p12\b',
        ],
        "remediation": "Use SHA-256 or stronger; use AES-256-GCM instead of DES/RC4",
    },
    {
        "id": "SECRET-001",
        "name": "Hardcoded Password",
        "severity": "HIGH",
        "description": "Potential hardcoded password or credential",
        "patterns": [
            r'(?i)password\s*[=:]\s*["\'][^"\'\s]{4,}["\']',
            r'(?i)passwd\s*[=:]\s*["\'][^"\'\s]{4,}["\']',
            r'(?i)pwd\s*[=:]\s*["\'][^"\'\s]{4,}["\']',
            r'(?i)secret\s*[=:]\s*["\'][^"\'\s]{8,}["\']',
            r'(?i)api_key\s*[=:]\s*["\'][^"\'\s]{8,}["\']',
            r'(?i)apikey\s*[=:]\s*["\'][^"\'\s]{8,}["\']',
            r'(?i)token\s*[=:]\s*["\'][^"\'\s]{16,}["\']',
        ],
        "remediation": "Use environment variables or a secrets manager; never hardcode credentials",
    },
    {
        "id": "AUTH-001",
        "name": "Weak Authentication - Basic Auth",
        "severity": "MEDIUM",
        "description": "Use of HTTP Basic Authentication without HTTPS",
        "patterns": [
            r'(?i)requests?\.(?:get|post)\(.*auth\s*=?\s*\(\s*["\']',
            r'(?i)HTTPBasicAuth',
            r'(?i)httpx\.BasicAuth',
        ],
        "remediation": "Use token-based auth (JWT, OAuth2) over HTTPS instead of Basic Auth",
    },
        {
            "id": "CMDI-001",
            "name": "Command Injection",
            "severity": "CRITICAL",
            "description": "Shell command built from user input",
            "patterns": [
                r'(?i)os\.system\(\s*(?:f|b)?["\'][^"\']*\{',
                r'(?i)subprocess\.(?:run|Popen|call|check_output)\(\s*(?:f|b)?["\'][^"\']*\{',
                r'(?i)subprocess\.(?:run|Popen|call|check_output)\(\s*["\'][^"\']*["\']\s*,\s*shell\s*=\s*True',
                r'(?i)exec\(\s*(?:f|b)?["\'][^"\']*\{',
                r'(?i)eval\(\s*(?:f|b)?["\'][^"\']*\{',
                r'(?i)`.*\{.*`',
            ],
        "remediation": "Avoid shell commands with user input; use subprocess with argument lists (shell=False)",
    },
]

FILE_EXTENSIONS = {".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs", ".rb", ".php", ".cs", ".kt", ".swift"}

IGNORE_DIRS = {"node_modules", ".git", "__pycache__", "venv", ".venv", "dist", "build", ".tox", ".eggs", "vendor"}


def scan_file(filepath: Path, rules: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    if rules is None:
        rules = SAST_RULES

    findings: list[dict[str, Any]] = []
    try:
        content = filepath.read_text(encoding="utf-8", errors="replace")
    except (OSError, UnicodeDecodeError):
        return findings

    for rule in rules:
        for pattern in rule["patterns"]:
            for match in re.finditer(pattern, content):
                line_num = content[: match.start()].count("\n") + 1
                findings.append({
                    "rule_id": rule["id"],
                    "name": rule["name"],
                    "severity": rule["severity"],
                    "description": rule["description"],
                    "file": str(filepath),
                    "line": line_num,
                    "match": match.group()[:120],
                    "remediation": rule["remediation"],
                })
                break

    return findings


def run_sast_scan(path: str | Path = ".") -> dict[str, Any]:
    root = Path(path).resolve()
    all_findings: list[dict[str, Any]] = []

    for ext in FILE_EXTENSIONS:
        for filepath in root.rglob(f"*{ext}"):
            rel_parts = filepath.relative_to(root).parts
            if any(part in IGNORE_DIRS for part in rel_parts):
                continue
            findings = scan_file(filepath)
            all_findings.extend(findings)

    high = sum(1 for f in all_findings if f["severity"] == "CRITICAL" or f["severity"] == "HIGH")
    medium = sum(1 for f in all_findings if f["severity"] == "MEDIUM")
    low = sum(1 for f in all_findings if f["severity"] == "LOW")

    return {
        "tool": "sast",
        "rules_evaluated": len(SAST_RULES),
        "findings": all_findings,
        "summary": {
            "total": len(all_findings),
            "critical": sum(1 for f in all_findings if f["severity"] == "CRITICAL"),
            "high": high,
            "medium": medium,
            "low": low,
        },
    }
