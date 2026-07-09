from __future__ import annotations

from fastmcp import FastMCP

from testing_mcp.runners.game_testing import detect_game_project, run_godot_tests, run_unity_tests, run_unreal_tests
from testing_mcp.server.tools._helpers import _resolve_path


def register_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    def detect_game(path: str = ".") -> dict:
        """Detect if the project is a game (Godot, Unity, Unreal)."""
        root = _resolve_path(path)
        return detect_game_project(root)

    @mcp.tool()
    def run_game_tests(
        path: str = ".",
        engine: str = "auto",
    ) -> dict:
        """Run game engine tests."""
        root = _resolve_path(path)
        if engine == "auto":
            detected = detect_game_project(root)
            engines = detected.get("engines", [])
            if not engines:
                return {"error": "No game engine detected"}
            engine = engines[0]

        if engine == "godot":
            return run_godot_tests(root)
        elif engine == "unity":
            return run_unity_tests(root)
        elif engine == "unreal":
            return run_unreal_tests(root)
        return {"error": f"Unknown engine: {engine}"}
