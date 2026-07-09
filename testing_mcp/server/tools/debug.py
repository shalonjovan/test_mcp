from __future__ import annotations

import re

from fastmcp import FastMCP

from testing_mcp.server.tools._helpers import _resolve_path


def register_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    def inspect_logs(
        log_content: str,
        log_file: str = "",
        error_patterns: list[str] | None = None,
    ) -> dict:
        """Analyze log content for errors and patterns."""
        if log_file:
            try:
                log_content = _resolve_path(log_file).read_text()
            except (OSError, FileNotFoundError) as e:
                return {"error": f"Could not read log file: {e}"}

        patterns = error_patterns or [
            r"(?i)(error|exception|traceback|failed|failure)",
            r"(?i)(timeout|timed?\s*out)",
            r"(?i)(crash|segfault|abort)",
            r"(?i)(permission denied|access denied)",
        ]

        lines = log_content.split("\n")
        matches: list[dict] = []
        for i, line in enumerate(lines, 1):
            for pattern in patterns:
                if re.search(pattern, line):
                    matches.append({"line": i, "content": line.strip(), "pattern": pattern})
                    break

        return {
            "total_lines": len(lines),
            "matches_found": len(matches),
            "matches": matches[:100],
        }
