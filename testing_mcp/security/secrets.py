from __future__ import annotations

import re
from pathlib import Path
from typing import Any

SECRET_PATTERNS: list[dict[str, Any]] = [
    {"id": "AWS-KEY", "name": "AWS Access Key", "pattern": r"(?i)(?:AKIA[0-9A-Z]{16}|A3T[A-Z0-9]|AKIA[0-9A-Z]{16})", "severity": "CRITICAL"},
    {"id": "AWS-SECRET", "name": "AWS Secret Key", "pattern": r"(?i)(?<![A-Za-z0-9+/=])[A-Za-z0-9+/]{40}(?![A-Za-z0-9+/=])", "severity": "CRITICAL"},
    {"id": "GITHUB-TOKEN", "name": "GitHub PAT", "pattern": r"(?i)(?:ghp_|gho_|ghu_|ghs_|ghr_|github_pat_)[A-Za-z0-9_]{36,}", "severity": "CRITICAL"},
    {"id": "GITLAB-TOKEN", "name": "GitLab PAT", "pattern": r"(?i)glpat-[A-Za-z0-9\-_]{20,}", "severity": "CRITICAL"},
    {"id": "SLACK-TOKEN", "name": "Slack Token", "pattern": r"(?i)xox[baprs]-[0-9a-zA-Z\-]{10,}", "severity": "HIGH"},
    {"id": "DISCORD-TOKEN", "name": "Discord Bot Token", "pattern": r"(?i)[MN][A-Za-z0-9_-]{23,28}\.[A-Za-z0-9_-]{6,10}\.[A-Za-z0-9_-]{27,40}", "severity": "HIGH"},
    {"id": "JWT-TOKEN", "name": "JWT Token", "pattern": r"(?i)eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}", "severity": "HIGH"},
    {"id": "GOOGLE-API", "name": "Google API Key", "pattern": r"(?i)AIza[0-9A-Za-z\-_]{35}", "severity": "HIGH"},
    {"id": "STRIPE-KEY", "name": "Stripe Secret Key", "pattern": r"(?i)sk_live_[0-9a-zA-Z]{24,}", "severity": "CRITICAL"},
    {"id": "STRIPE-PUB", "name": "Stripe Publishable Key", "pattern": r"(?i)pk_live_[0-9a-zA-Z]{24,}", "severity": "MEDIUM"},
    {"id": "SSH-KEY", "name": "SSH Private Key", "pattern": r"-----BEGIN\s*(?:RSA|DSA|EC|OPENSSH)\s*PRIVATE\s*KEY-----", "severity": "CRITICAL"},
    {"id": "PGP-KEY", "name": "PGP Private Key", "pattern": r"-----BEGIN PGP PRIVATE KEY BLOCK-----", "severity": "CRITICAL"},
    {"id": "HEROKU-API", "name": "Heroku API Key", "pattern": r"(?i)[hH][eE][rR][oO][kK][uU].*[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}", "severity": "HIGH"},
    {"id": "GENERIC-TOKEN", "name": "Generic API Token", "pattern": r"(?i)(?:api[_-]?key|api[_-]?secret|app[_-]?secret)[\s:=]+['\"]([A-Za-z0-9_\-\.]{16,})['\"]", "severity": "HIGH"},
    {"id": "CONNECTION-STRING", "name": "Database Connection String", "pattern": r"(?i)(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis|rediss)://[^\s]{10,}", "severity": "HIGH"},
    {"id": "PEM-KEY", "name": "PEM Encoded Key", "pattern": r"-----BEGIN\s*(?:CERTIFICATE|EC|RSA|DSA)\s*KEY-----", "severity": "HIGH"},
    {"id": "NPM-TOKEN", "name": "npm Token", "pattern": r"(?i)npm_[A-Za-z0-9]{36}", "severity": "HIGH"},
    {"id": "TWILIO-SID", "name": "Twilio SID", "pattern": r"(?i)AC[a-z0-9]{32}", "severity": "HIGH"},
    {"id": "TWILIO-AUTH", "name": "Twilio Auth Token", "pattern": r"(?i)(?:TWILIO_AUTH_TOKEN|twilio_auth_token)\s*[=:]\s*['\"][a-z0-9]{32}['\"]", "severity": "CRITICAL"},
    {"id": "AZURE-CONNECTION", "name": "Azure Connection String", "pattern": r"(?i)DefaultEndpointsProtocol=https;AccountName=", "severity": "HIGH"},
    {"id": "AZURE-KEY", "name": "Azure Subscription Key", "pattern": r"(?i)(?:azure|AZURE).*(?:key|KEY)\s*[=:]\s*['\"][A-Za-z0-9_\-]{20,}['\"]", "severity": "HIGH"},
    {"id": "GCP-SERVICE-ACCT", "name": "GCP Service Account JSON", "pattern": r"\"type\":\s*\"service_account\"", "severity": "CRITICAL"},
    {"id": "PRIVATE-KEY-FILE", "name": "Private Key File", "pattern": r".*\.(?:pem|key|p12|pfx|asc)$", "severity": "MEDIUM"},
    {"id": "DOCKER-HUB", "name": "Docker Hub Credential", "pattern": r"(?i)(?:DOCKER_HUB|docker_hub).*(?:password|token|PAT)\s*[=:]\s*['\"][^'\"]{8,}['\"]", "severity": "HIGH"},
    {"id": "TELEGRAM-TOKEN", "name": "Telegram Bot Token", "pattern": r"(?i)[0-9]{8,10}:[A-Za-z0-9_-]{35}", "severity": "HIGH"},
    {"id": "FACEBOOK-TOKEN", "name": "Facebook Access Token", "pattern": r"(?i)EAACEdEose0cBA[0-9A-Za-z]{30,}", "severity": "HIGH"},
]

IGNORE_DIRS = {"node_modules", ".git", "__pycache__", "venv", ".venv", "dist", "build", ".tox", ".eggs", "vendor", ".terraform", ".serverless"}

SENSITIVE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".env", ".env.local", ".env.production",
    ".json", ".yml", ".yaml", ".toml", ".cfg", ".conf", ".ini", ".txt",
    ".sh", ".bash", ".zsh", ".ps1", ".bat", ".cmd",
    ".php", ".rb", ".go", ".rs", ".java", ".cs", ".kt",
    ".xml", ".html", ".vue", ".svelte", ".md",
    ".pem", ".key", ".p12", ".pfx", ".asc", ".der", ".cert",
}


def scan_for_secrets(
    path: str | Path = ".",
    max_file_size: int = 1_000_000,
) -> dict[str, Any]:
    root = Path(path).resolve()
    all_findings: list[dict[str, Any]] = []
    scanned_files = 0
    skipped_files = 0

    for ext in SENSITIVE_EXTENSIONS:
        for filepath in root.rglob(f"*{ext}"):
            rel_parts = filepath.relative_to(root).parts
            if any(part in IGNORE_DIRS for part in rel_parts):
                continue

            try:
                if filepath.stat().st_size > max_file_size:
                    skipped_files += 1
                    continue
                content = filepath.read_text(encoding="utf-8", errors="replace")
                scanned_files += 1
            except (OSError, UnicodeDecodeError):
                skipped_files += 1
                continue

            for rule in SECRET_PATTERNS:
                if rule["id"] == "PRIVATE-KEY-FILE":
                    if filepath.suffix in {".pem", ".key", ".p12", ".pfx", ".asc", ".der", ".cert"}:
                        all_findings.append({
                            "rule_id": rule["id"],
                            "name": rule["name"],
                            "severity": rule["severity"],
                            "file": str(filepath.relative_to(root)),
                            "line": 1,
                            "match": filepath.name,
                        })
                    continue

                for match in re.finditer(rule["pattern"], content):
                    line_num = content[: match.start()].count("\n") + 1
                    all_findings.append({
                        "rule_id": rule["id"],
                        "name": rule["name"],
                        "severity": rule["severity"],
                        "file": str(filepath.relative_to(root)),
                        "line": line_num,
                        "match": match.group()[:80],
                    })

    critical = sum(1 for f in all_findings if f["severity"] == "CRITICAL")
    high = sum(1 for f in all_findings if f["severity"] == "HIGH")
    medium = sum(1 for f in all_findings if f["severity"] == "MEDIUM")

    return {
        "tool": "secret-scanner",
        "scanned_files": scanned_files,
        "skipped_files": skipped_files,
        "findings": all_findings,
        "critical_count": critical,
        "high_count": high,
        "medium_count": medium,
        "total_findings": len(all_findings),
    }
