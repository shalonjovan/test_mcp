from __future__ import annotations

from pathlib import Path

from testing_mcp.browser import get_session
from testing_mcp.utils.validators import validate_command, validate_project_path, validate_url


def _resolve_path(path: str) -> Path:
    return validate_project_path(path)


def _resolve_url(url: str, allow_internal: bool = False) -> str:
    return validate_url(url, allow_internal=allow_internal)


def _resolve_command(command: str) -> list[str]:
    return validate_command(command)


def _browser_sess(session_id: str) -> tuple:
    sess = get_session(session_id)
    if not sess:
        return None, {
            "success": False,
            "error": "No active session. Call browser_new_session first.",
        }
    return sess, None
