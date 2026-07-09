from __future__ import annotations

import json
import subprocess
from pathlib import Path

from testing_mcp.runners.base import TestResult, handle_timeout, run_subprocess


def discover_python_tests(project_root: Path) -> list[str]:
    test_files: list[str] = []
    for pattern in ["test_*.py", "*_test.py", "**/test_*.py", "**/*_test.py"]:
        for f in project_root.glob(pattern):
            rel = str(f.relative_to(project_root))
            if rel not in test_files:
                test_files.append(rel)
    return sorted(test_files)


def run_pytest(
    project_root: Path,
    test_paths: list[str] | None = None,
    timeout: int = 300,
    extra_args: list[str] | None = None,
) -> list[TestResult]:
    cmd = ["python", "-m", "pytest", "--json-report", "--tb=short"]
    if extra_args:
        cmd.extend(extra_args)
    if test_paths:
        cmd.extend(test_paths)

    try:
        proc = run_subprocess(cmd, cwd=project_root, timeout=timeout)
    except subprocess.TimeoutExpired:
        return handle_timeout("pytest")

    report_file = project_root / ".report.json"
    results: list[TestResult] = []

    if report_file.exists():
        try:
            report = json.loads(report_file.read_text())
            for test in report.get("tests", []):
                results.append(
                    TestResult(
                        passed=test.get("outcome") == "passed",
                        name=test.get("nodeid", "unknown"),
                        duration=test.get("duration", 0),
                        message=test.get("call", {}).get("longrepr", ""),
                    )
                )
            report_file.unlink(missing_ok=True)
            return results
        except (json.JSONDecodeError, KeyError):
            pass

    passed = proc.returncode == 0
    results.append(
        TestResult(
            passed=passed,
            name="pytest",
            stdout=proc.stdout,
            stderr=proc.stderr,
        )
    )
    return results
