from __future__ import annotations

import json
import subprocess
from pathlib import Path

from testing_mcp.runners.base import TestResult


def detect_js_project(project_root: Path) -> dict[str, float]:
    frameworks: dict[str, float] = {}
    pkg_file = project_root / "package.json"
    if not pkg_file.exists():
        return frameworks

    try:
        data = json.loads(pkg_file.read_text())
        deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
    except (json.JSONDecodeError, KeyError):
        return frameworks

    if "jest" in deps or "jest-cli" in deps:
        frameworks["jest"] = 1.0
    if "vitest" in deps:
        frameworks["vitest"] = 1.0
    if "playwright" in deps or "@playwright/test" in deps:
        frameworks["playwright"] = 1.0
    if "cypress" in deps:
        frameworks["cypress"] = 1.0

    return frameworks


def discover_js_tests(project_root: Path, framework: str = "jest") -> list[str]:
    if framework == "jest":
        patterns = ["**/*.test.js", "**/*.test.ts", "**/*.spec.js", "**/*.spec.ts", "**/__tests__/**"]
    elif framework == "vitest":
        patterns = ["**/*.test.js", "**/*.test.ts", "**/*.spec.js", "**/*.spec.ts"]
    else:
        patterns = ["**/*.test.js", "**/*.test.ts"]

    found: list[str] = []
    for pattern in patterns:
        for f in project_root.glob(pattern):
            rel = str(f.relative_to(project_root))
            if rel not in found and "node_modules" not in rel:
                found.append(rel)
    return sorted(found)


def run_jest(
    project_root: Path,
    test_paths: list[str] | None = None,
    timeout: int = 120,
) -> list[TestResult]:
    npx = "npx.cmd" if Path("npx.cmd").exists() else "npx"
    cmd = [npx, "jest", "--json"]
    if test_paths:
        cmd.extend(test_paths)

    try:
        proc = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return [TestResult(passed=False, name="jest", message="Timeout exceeded")]

    try:
        report = json.loads(proc.stdout)
        results: list[TestResult] = []
        for test_result in report.get("testResults", []):
            for assertion in test_result.get("assertionResults", []):
                results.append(
                    TestResult(
                        passed=assertion.get("status") == "passed",
                        name=assertion.get("fullName", "unknown"),
                        duration=assertion.get("duration", 0) / 1000,
                        message=assertion.get("failureMessages", [""])[0],
                    )
                )
        if results:
            return results
    except (json.JSONDecodeError, KeyError, TypeError):
        pass

    passed = proc.returncode == 0
    return [
        TestResult(
            passed=passed,
            name="jest",
            stdout=proc.stdout,
            stderr=proc.stderr,
        )
    ]


def run_vitest(
    project_root: Path,
    test_paths: list[str] | None = None,
    timeout: int = 120,
) -> list[TestResult]:
    npx = "npx.cmd" if Path("npx.cmd").exists() else "npx"
    cmd = [npx, "vitest", "run", "--reporter=json"]
    if test_paths:
        cmd.extend(test_paths)

    try:
        proc = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return [TestResult(passed=False, name="vitest", message="Timeout exceeded")]

    try:
        report = json.loads(proc.stdout)
        results: list[TestResult] = []
        for test_file in report:
            for test in test_file.get("tasks", []):
                results.append(
                    TestResult(
                        passed=test.get("type") == "passed",
                        name=test.get("name", "unknown"),
                        duration=test.get("duration", 0) / 1000,
                    )
                )
        if results:
            return results
    except (json.JSONDecodeError, KeyError, TypeError):
        pass

    passed = proc.returncode == 0
    return [
        TestResult(
            passed=passed,
            name="vitest",
            stdout=proc.stdout,
            stderr=proc.stderr,
        )
    ]
