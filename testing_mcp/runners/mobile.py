from __future__ import annotations

from pathlib import Path
from typing import Any


def detect_mobile_project(project_root: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "is_mobile": False,
        "platforms": [],
        "frameworks": [],
    }

    if (project_root / "android").is_dir() or (project_root / "app").is_dir():
        gradle_files = list(project_root.rglob("build.gradle*"))
        if gradle_files:
            result["is_mobile"] = True
            result["platforms"].append("android")

    if (project_root / "pubspec.yaml").exists():
        result["is_mobile"] = True
        result["platforms"].append("android")
        result["frameworks"].append("flutter")

    if (project_root / "ios").is_dir() or list(project_root.rglob("*.xcworkspace")):
        result["is_mobile"] = True
        result["platforms"].append("ios")

    if (project_root / "package.json").exists():
        import json
        try:
            pkg = json.loads((project_root / "package.json").read_text())
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
            if "react-native" in deps:
                result["is_mobile"] = True
                result["platforms"].extend(["android", "ios"])
                result["frameworks"].append("react-native")
        except (json.JSONDecodeError, KeyError):
            pass

    result["platforms"] = list(set(result["platforms"]))
    result["frameworks"] = list(set(result["frameworks"]))

    return result


def run_android_tests(project_root: Path, test_type: str = "unit") -> dict[str, Any]:
    import subprocess

    result: dict[str, Any] = {
        "platform": "android",
        "test_type": test_type,
        "passed": False,
        "output": "",
    }

    if test_type == "unit":
        gradlew = project_root / "gradlew"
        cmd = [str(gradlew) if gradlew.exists() else "gradlew", "test"]
    elif test_type == "instrumented":
        gradlew = project_root / "gradlew"
        cmd = [str(gradlew) if gradlew.exists() else "gradlew", "connectedAndroidTest"]
    else:
        result["error"] = f"Unknown test type: {test_type}"
        return result

    try:
        proc = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True, timeout=600)
        result["passed"] = proc.returncode == 0
        result["output"] = proc.stdout[-2000:] if proc.stdout else proc.stderr[-2000:]
    except subprocess.TimeoutExpired:
        result["error"] = "Android test timed out after 600s"
    except FileNotFoundError:
        result["error"] = "Gradle not found"
    except Exception as e:
        result["error"] = str(e)

    return result


def run_flutter_tests(project_root: Path) -> dict[str, Any]:
    import subprocess

    result: dict[str, Any] = {
        "platform": "flutter",
        "passed": False,
        "output": "",
    }

    try:
        proc = subprocess.run(
            ["flutter", "test"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=600,
        )
        result["passed"] = proc.returncode == 0
        result["output"] = proc.stdout[-2000:] if proc.stdout else proc.stderr[-2000:]
    except subprocess.TimeoutExpired:
        result["error"] = "Flutter test timed out after 600s"
    except FileNotFoundError:
        result["error"] = "Flutter not found. Install from https://flutter.dev"
    except Exception as e:
        result["error"] = str(e)

    return result
