from __future__ import annotations

import json
import subprocess
from pathlib import Path

from testing_mcp.runners.base import TestResult, handle_timeout, handle_not_found, run_subprocess


def discover_rust_tests(project_root: Path) -> list[str]:
    test_files: list[str] = []
    for pattern in ["**/*.rs"]:
        for f in project_root.glob(pattern):
            content = f.read_text()
            if "mod tests" in content or "#[test]" in content or "#[tokio::test]" in content:
                rel = str(f.relative_to(project_root))
                if rel not in test_files:
                    test_files.append(rel)
    return sorted(test_files)


def run_cargo_test(
    project_root: Path,
    test_name: str | None = None,
    timeout: int = 300,
) -> list[TestResult]:
    cmd = ["cargo", "test"]
    if test_name:
        cmd.extend([test_name, "--", "--exact"])
    cmd.append("--")

    try:
        proc = run_subprocess(
            cmd + ["--color=never", "--format=json"],
            cwd=project_root,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return handle_timeout("cargo-test")
    except FileNotFoundError:
        return handle_not_found("cargo-test", "Cargo/Rust")

    results: list[TestResult] = []
    for line in proc.stdout.split("\n"):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
            if event.get("type") == "test":
                name = event.get("name", "unknown")
                passed = event.get("event") == "ok"
                results.append(
                    TestResult(
                        passed=passed,
                        name=f"rust:{name}",
                        message=event.get("stdout", ""),
                    )
                )
        except (json.JSONDecodeError, KeyError):
            pass

    if not results:
        passed = proc.returncode == 0
        results.append(
            TestResult(
                passed=passed,
                name="cargo-test",
                stdout=proc.stdout,
                stderr=proc.stderr,
            )
        )

    return results
