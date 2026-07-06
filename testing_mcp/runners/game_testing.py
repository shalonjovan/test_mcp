from __future__ import annotations

from pathlib import Path
from typing import Any


def detect_game_project(project_root: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "is_game": False,
        "engines": [],
    }

    if (project_root / "project.godot").exists() or list(project_root.rglob("*.godot")):
        result["is_game"] = True
        result["engines"].append("godot")

    if (project_root / "Assembly-CSharp.csproj").exists() or (project_root / "Assets").is_dir():
        result["is_game"] = True
        result["engines"].append("unity")

    if list(project_root.rglob("*.uproject")):
        result["is_game"] = True
        result["engines"].append("unreal")

    return result


def run_godot_tests(project_root: Path) -> dict[str, Any]:
    import subprocess

    result: dict[str, Any] = {
        "engine": "godot",
        "passed": False,
        "output": "",
    }

    for godot_binary in ["godot", "godot4", "godot3"]:
        try:
            proc = subprocess.run(
                [godot_binary, "--headless", "--path", str(project_root), "--script", "res://test_runner.gd"],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if proc.returncode == 0 or proc.stderr:
                result["passed"] = proc.returncode == 0
                result["output"] = proc.stdout[-2000:] or proc.stderr[-2000:]
                result["binary"] = godot_binary
                return result
        except (subprocess.TimeoutExpired, FileNotFoundError):
            continue

    result["error"] = "Godot not found or no tests found"
    return result


def run_unity_tests(project_root: Path) -> dict[str, Any]:
    import subprocess

    result: dict[str, Any] = {
        "engine": "unity",
        "passed": False,
        "output": "",
    }

    for unity_binary in [
        "/Applications/Unity/Unity.app/Contents/MacOS/Unity",
        "C:\\Program Files\\Unity\\Editor\\Unity.exe",
        "unity",
        "unity-editor",
    ]:
        try:
            proc = subprocess.run(
                [
                    unity_binary,
                    "-projectPath", str(project_root),
                    "-runTests",
                    "-testPlatform", "EditMode",
                    "-batchmode",
                    "-nographics",
                    "-logFile", "-",
                ],
                capture_output=True,
                text=True,
                timeout=300,
            )
            result["passed"] = "PASSED" in proc.stdout or proc.returncode == 0
            result["output"] = proc.stdout[-2000:] or proc.stderr[-2000:]
            result["binary"] = unity_binary
            return result
        except (subprocess.TimeoutExpired, FileNotFoundError):
            continue

    result["error"] = "Unity not found"
    return result


def run_unreal_tests(project_root: Path) -> dict[str, Any]:
    import subprocess

    result: dict[str, Any] = {
        "engine": "unreal",
        "passed": False,
        "output": "",
    }

    uproject_files = list(project_root.rglob("*.uproject"))
    if not uproject_files:
        result["error"] = "No .uproject file found"
        return result

    uproject = str(uproject_files[0])

    editor_binaries = [
        "UE5Editor",
        "UE4Editor",
        "UnrealEditor",
    ]

    for editor in editor_binaries:
        try:
            proc = subprocess.run(
                [editor, uproject, "-ExecCmds=", "Automation RunTests Now", "-nullRHI", "- unattended"],
                capture_output=True,
                text=True,
                timeout=300,
            )
            result["passed"] = proc.returncode == 0
            result["output"] = proc.stdout[-2000:] or proc.stderr[-2000:]
            result["binary"] = editor
            return result
        except (subprocess.TimeoutExpired, FileNotFoundError):
            continue

    result["error"] = "Unreal Editor not found"
    return result
