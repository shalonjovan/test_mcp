from __future__ import annotations

import subprocess
from pathlib import Path

from testing_mcp.runners.base import TestResult, handle_timeout, handle_not_found, run_subprocess


def discover_go_tests(project_root: Path) -> list[str]:
    test_files: list[str] = []
    for pattern in ["**/*_test.go"]:
        for f in project_root.glob(pattern):
            rel = str(f.relative_to(project_root))
            if rel not in test_files:
                test_files.append(rel)
    return sorted(test_files)


def run_go_test(
    project_root: Path,
    test_pattern: str = "./...",
    timeout: int = 120,
) -> list[TestResult]:
    try:
        proc = run_subprocess(["go", "test", test_pattern, "-v"], cwd=project_root, timeout=timeout)
    except subprocess.TimeoutExpired:
        return handle_timeout("go-test")
    except FileNotFoundError:
        return handle_not_found("go-test", "Go")

    results: list[TestResult] = []
    current_package = ""

    for line in proc.stdout.split("\n"):
        if line.startswith("ok "):
            parts = line.split()
            current_package = parts[1] if len(parts) > 1 else ""
            results.append(
                TestResult(passed=True, name=f"go-test:{current_package}", stdout=line)
            )
        elif line.startswith("FAIL"):
            parts = line.split()
            pkg = parts[1] if len(parts) > 1 else "unknown"
            results.append(
                TestResult(passed=False, name=f"go-test:{pkg}", stdout=line)
            )
        elif "--- PASS:" in line:
            name = line.split("--- PASS:")[1].strip().split()[0] if "--- PASS:" in line else line
            results.append(
                TestResult(passed=True, name=f"go:{name}", stdout=line)
            )
        elif "--- FAIL:" in line:
            name = line.split("--- FAIL:")[1].strip().split()[0] if "--- FAIL:" in line else line
            results.append(
                TestResult(passed=False, name=f"go:{name}", stdout=line)
            )

    if not results:
        passed = proc.returncode == 0
        results.append(
            TestResult(
                passed=passed,
                name="go-test",
                stdout=proc.stdout,
                stderr=proc.stderr,
            )
        )

    return results
