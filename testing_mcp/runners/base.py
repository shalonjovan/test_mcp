from __future__ import annotations

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


class TestRunner:
    def __init__(self, project_root: Path):
        self.project_root = project_root

    def run_command(
        self,
        cmd: list[str],
        timeout: int = 120,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess:
        final_env = {**dict(Path("/").glob("**/*")), **{}}  # placeholder
        final_env = None
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
