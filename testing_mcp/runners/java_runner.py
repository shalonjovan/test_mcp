from __future__ import annotations

import subprocess
from pathlib import Path

from testing_mcp.runners.base import TestResult


def discover_java_tests(project_root: Path) -> list[str]:
    test_files: list[str] = []
    for pattern in ["**/*Test.java", "**/Test*.java"]:
        for f in project_root.glob(pattern):
            rel = str(f.relative_to(project_root))
            if rel not in test_files:
                test_files.append(rel)
    return sorted(test_files)


def run_maven_tests(
    project_root: Path,
    test_classes: list[str] | None = None,
    timeout: int = 600,
) -> list[TestResult]:
    cmd = ["./mvnw" if (project_root / "mvnw").exists() else "mvn", "test"]
    if test_classes:
        test_filter = ",".join(test_classes)
        cmd.extend(["-Dtest=" + test_filter])

    try:
        proc = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return [TestResult(passed=False, name="maven", message="Timeout exceeded")]

    passed = proc.returncode == 0
    return [
        TestResult(
            passed=passed,
            name="maven-tests",
            stdout=proc.stdout,
            stderr=proc.stderr,
        )
    ]


def run_gradle_tests(
    project_root: Path,
    test_classes: list[str] | None = None,
    timeout: int = 600,
) -> list[TestResult]:
    cmd = ["./gradlew" if (project_root / "gradlew").exists() else "gradle", "test"]
    if test_classes:
        cmd.extend(["--tests", ",".join(test_classes)])

    try:
        proc = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return [TestResult(passed=False, name="gradle", message="Timeout exceeded")]

    passed = proc.returncode == 0
    return [
        TestResult(
            passed=passed,
            name="gradle-tests",
            stdout=proc.stdout,
            stderr=proc.stderr,
        )
    ]
