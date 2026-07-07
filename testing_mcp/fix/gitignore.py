from __future__ import annotations

from pathlib import Path
from typing import Any


def add_to_gitignore(
    path: str = ".",
    patterns: list[str] | None = None,
) -> dict[str, Any]:
    gitignore_path = Path(path).resolve() / ".gitignore"
    requested = patterns or []

    existing_lines: list[str] = []
    if gitignore_path.exists():
        existing_lines = [line.rstrip("\n") for line in gitignore_path.read_text().splitlines()]

    existing_set = set(existing_lines) - {""}
    added: list[str] = []
    already_present: list[str] = []

    for p in requested:
        if p in existing_set:
            already_present.append(p)
        else:
            added.append(p)
            existing_lines.append(p)

    if added:
        content = "\n".join(existing_lines)
        if not content.endswith("\n"):
            content += "\n"
        gitignore_path.parent.mkdir(parents=True, exist_ok=True)
        gitignore_path.write_text(content)

    return {
        "path": str(gitignore_path),
        "exists": gitignore_path.exists(),
        "total_patterns": len(existing_lines),
        "added": added,
        "already_present": already_present,
        "modified": len(added) > 0,
    }
