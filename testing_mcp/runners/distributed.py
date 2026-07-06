from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


def detect_ci_config(project_root: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "ci_systems": [],
        "docker": False,
    }

    if (project_root / ".github/workflows").is_dir():
        result["ci_systems"].append("github-actions")

    if (project_root / ".gitlab-ci.yml").exists():
        result["ci_systems"].append("gitlab-ci")

    if (project_root / "Jenkinsfile").exists():
        result["ci_systems"].append("jenkins")

    if (project_root / ".circleci/config.yml").exists():
        result["ci_systems"].append("circleci")

    if (project_root / "Dockerfile").exists() or (project_root / "docker-compose.yml").exists():
        result["docker"] = True

    return result


def check_docker_available() -> dict[str, Any]:
    try:
        proc = subprocess.run(
            ["docker", "info", "--format", "{{json .}}"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if proc.returncode == 0:
            info = json.loads(proc.stdout)
            return {
                "available": True,
                "version": info.get("ServerVersion", "unknown"),
                "containers": info.get("Containers", 0),
                "images": info.get("Images", 0),
            }
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
        pass

    return {"available": False}


def check_kubernetes_available() -> dict[str, Any]:
    try:
        proc = subprocess.run(
            ["kubectl", "version", "--short"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if proc.returncode == 0:
            return {"available": True, "version": proc.stdout.strip()}
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return {"available": False}


def get_infrastructure_info() -> dict[str, Any]:
    import platform

    return {
        "platform": platform.system(),
        "architecture": platform.machine(),
        "cpu_count": str(Path("/proc/cpuinfo").read_text().count("processor\t:") if Path("/proc/cpuinfo").exists() else "N/A"),
        "docker": check_docker_available(),
        "kubernetes": check_kubernetes_available(),
        "ci_config": detect_ci_config(Path.cwd()),
    }
