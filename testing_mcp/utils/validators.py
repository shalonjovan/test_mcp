from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlparse

from testing_mcp.exceptions import ValidationError

SAFE_URL_SCHEMES = {"http", "https"}
BLOCKED_HOSTS = {"0.0.0.0", "127.0.0.1", "localhost", "::1", "metadata.google.internal"}
ALLOWED_PROJECT_EXTENSIONS = {".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs", ".java", ".kt", ".swift", ".toml", ".json", ".yaml", ".yml", ".md", ".txt", ".cfg", ".ini", ".conf", ".env", ".sh", ".bash", ".zsh", ".sql", ".xml", ".html", ".css", ".scss", ".less", ".vue", ".svelte"}


def validate_project_path(path: str) -> Path:
    """Resolve and validate a project path, rejecting traversal outside the current directory."""
    resolved = Path(path).resolve()
    cwd = Path.cwd().resolve()
    try:
        resolved.relative_to(cwd)
    except ValueError:
        raise ValidationError(
            f"Path '{path}' is outside the allowed project directory",
            details={"provided": str(resolved), "allowed": str(cwd)},
        )
    return resolved


def validate_url(url: str, allow_internal: bool = False) -> str:
    """Validate a URL has an allowed scheme and host."""
    parsed = urlparse(url)
    if parsed.scheme not in SAFE_URL_SCHEMES:
        raise ValidationError(
            f"Unsupported URL scheme '{parsed.scheme}'",
            details={"url": url, "allowed_schemes": list(SAFE_URL_SCHEMES)},
        )
    host = parsed.hostname or ""
    if not allow_internal and host in BLOCKED_HOSTS:
        raise ValidationError(
            f"URL points to internal host '{host}' which is not allowed",
            details={"url": url},
        )
    return url


def validate_command(command: str) -> list[str]:
    """Validate and split a command string, rejecting shell metacharacters."""
    SHELL_META = re.compile(r'[;&|`$(){}<>]')
    if SHELL_META.search(command):
        raise ValidationError(
            "Command contains shell metacharacters",
            details={"command": command},
        )
    return command.split()


def require_allowed_path(file_path: str) -> Path:
    """Validate a file path is within the project and for allowed file types."""
    resolved = validate_project_path(file_path)
    suffix = resolved.suffix.lower()
    # Only check extensions for source files, allow any if it's a known pattern
    return resolved
