from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any


class TestResult:
    def __init__(
        self,
        passed: bool,
        name: str,
        duration: float = 0.0,
        message: str = "",
        stdout: str = "",
        stderr: str = "",
    ):
        self.passed = passed
        self.name = name
        self.duration = duration
        self.message = message
        self.stdout = stdout
        self.stderr = stderr

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "name": self.name,
            "duration": round(self.duration, 3),
            "message": self.message,
            "stdout": self.stdout,
            "stderr": self.stderr,
        }


def run_subprocess(
    cmd: list[str],
    *,
    cwd: Path | None = None,
    timeout: int = 120,
    env_add: dict[str, str] | None = None,
) -> subprocess.CompletedProcess:
    """Run a subprocess with proper error handling and env merging."""
    env = os.environ.copy()
    if env_add:
        env.update(env_add)
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
    )


def handle_timeout(name: str) -> list[TestResult]:
    """Standardized timeout error result for runner functions."""
    return [TestResult(passed=False, name=name, message="Timeout exceeded")]


def handle_not_found(name: str, tool: str = "") -> list[TestResult]:
    """Standardized 'tool not installed' error result."""
    msg = f"{tool} not installed" if tool else "Command not found"
    return [TestResult(passed=False, name=name, message=msg)]


class TestRunner:
    def __init__(self, project_root: Path):
        self.project_root = project_root

    def run_command(
        self,
        cmd: list[str],
        timeout: int = 120,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess:
        final_env = os.environ.copy()
        if env:
            final_env.update(env)
        return subprocess.run(
            cmd,
            cwd=self.project_root,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=final_env,
        )

    def discover_tests(self) -> list[str]:
        raise NotImplementedError

    def run_tests(self, test_names: list[str] | None = None) -> list[TestResult]:
        raise NotImplementedError
