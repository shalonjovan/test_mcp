from __future__ import annotations

import subprocess
import time
from pathlib import Path
from typing import Any


def run_integration_tests(
    project_root: Path,
    test_patterns: list[str] | None = None,
    timeout: int = 600,
) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    patterns = test_patterns or [
        "**/test_integration*.py",
        "**/integration_test*.py",
        "**/tests/integration/**/*.py",
        "**/test_*.js",
        "**/*.test.js",
        "**/test_*.ts",
        "**/*.test.ts",
    ]

    found_tests: list[Path] = []
    for pattern in patterns:
        found_tests.extend(project_root.glob(pattern))

    if not found_tests:
        return {
            "passed": False,
            "message": "No integration tests found",
            "test_count": 0,
            "results": [],
        }

    for test_file in found_tests:
        result = _run_single_integration_test(test_file, project_root, timeout)
        results.append(result)

    passed = sum(1 for r in results if r.get("passed"))
    failed = len(results) - passed

    return {
        "passed": failed == 0,
        "test_count": len(results),
        "passed_count": passed,
        "failed_count": failed,
        "results": results,
    }


def _run_single_integration_test(
    test_file: Path,
    project_root: Path,
    timeout: int,
) -> dict[str, Any]:
    name = str(test_file.relative_to(project_root))
    start = time.time()

    if test_file.suffix == ".py":
        cmd = ["python", "-m", "pytest", str(test_file), "-v", "--tb=short"]
    elif test_file.suffix in (".js", ".ts"):
        cmd = ["npx", "jest", str(test_file)]
    else:
        return {"name": name, "passed": False, "error": "Unsupported file type"}

    try:
        proc = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True, timeout=timeout)
        passed = proc.returncode == 0
        return {
            "name": name,
            "passed": passed,
            "duration": round(time.time() - start, 3),
            "stdout": proc.stdout[-1000:],
            "stderr": proc.stderr[-1000:],
        }
    except subprocess.TimeoutExpired:
        return {"name": name, "passed": False, "error": f"Timeout ({timeout}s)"}
    except Exception as e:
        return {"name": name, "passed": False, "error": str(e)}


def run_smoke_tests(
    project_root: Path,
    endpoints: list[str] | None = None,
    commands: list[str] | None = None,
    timeout: int = 30,
) -> dict[str, Any]:
    import httpx
    import asyncio

    results: list[dict[str, Any]] = []

    if endpoints:
        async def _check_endpoints():
            async with httpx.AsyncClient(timeout=timeout) as client:
                for endpoint in endpoints:
                    try:
                        resp = await client.get(endpoint)
                        results.append({
                            "type": "endpoint",
                            "target": endpoint,
                            "passed": resp.status_code < 500,
                            "status": resp.status_code,
                        })
                    except Exception as e:
                        results.append({
                            "type": "endpoint",
                            "target": endpoint,
                            "passed": False,
                            "error": str(e),
                        })
        asyncio.run(_check_endpoints())

    if commands:
        for cmd in commands:
            try:
                proc = subprocess.run(
                    cmd.split(),
                    cwd=project_root,
                    capture_output=True,
                    timeout=timeout,
                )
                results.append({
                    "type": "command",
                    "target": cmd,
                    "passed": proc.returncode == 0,
                    "exit_code": proc.returncode,
                })
            except Exception as e:
                results.append({
                    "type": "command",
                    "target": cmd,
                    "passed": False,
                    "error": str(e),
                })

    if not results:
        return {"passed": False, "error": "No smoke test targets provided", "results": []}

    return {
        "passed": all(r["passed"] for r in results),
        "test_count": len(results),
        "results": results,
    }
