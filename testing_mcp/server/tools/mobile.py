from __future__ import annotations

from fastmcp import FastMCP

from testing_mcp.runners.mobile import detect_mobile_project, run_android_tests, run_flutter_tests
from testing_mcp.server.tools._helpers import _resolve_path


def register_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    def detect_mobile(path: str = ".") -> dict:
        """Detect if the project is a mobile app (Android, Flutter, React Native)."""
        root = _resolve_path(path)
        return detect_mobile_project(root)

    @mcp.tool()
    def run_mobile_tests(
        path: str = ".",
        platform: str = "android",
        test_type: str = "unit",
    ) -> dict:
        """Run mobile app tests (Android or Flutter)."""
        root = _resolve_path(path)
        if platform == "flutter":
            return run_flutter_tests(root)
        return run_android_tests(root, test_type=test_type)
