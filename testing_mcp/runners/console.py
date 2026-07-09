from __future__ import annotations

import subprocess
import time
from pathlib import Path
from typing import Any



def _get_build_command(project_root: Path) -> list[str] | None:
    if (project_root / "Cargo.toml").exists():
        return ["cargo", "build", "--release"]
    if (project_root / "go.mod").exists():
        return ["go", "build", "-o", "app"]
    if (project_root / "Makefile").exists():
        return ["make"]
    return None


def _get_run_command(project_root: Path) -> list[str] | None:
    if (project_root / "Cargo.toml").exists():
        return ["cargo", "run", "--release"]
    if (project_root / "go.mod").exists():
        binary = project_root / "app"
        if binary.exists():
            return [str(binary)]
        return ["go", "run", "."]
    py_files = list(project_root.glob("*.py"))
    if py_files and (project_root / "main.py").exists():
        return ["python", str(project_root / "main.py")]
    if (project_root / "Makefile").exists():
        return ["make", "run"]
    return None


def run_console_test(
    project_root: Path,
    input_data: str = "",
    expected_output: str | None = None,
    expected_exit_code: int = 0,
    timeout: int = 30,
) -> dict[str, Any]:
    cmd = _get_run_command(project_root)
    if cmd is None:
        return {
            "passed": False,
            "error": "No run command determined for project",
            "name": "console-test",
        }

    start = time.time()
    try:
        proc = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            input=input_data if input_data else None,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return {
            "passed": False,
            "error": f"Timeout after {timeout}s",
            "name": "console-test",
            "duration": round(time.time() - start, 3),
        }

    duration = round(time.time() - start, 3)
    exit_ok = proc.returncode == expected_exit_code
    output_match = True
    if expected_output is not None:
        output_match = expected_output in proc.stdout or expected_output in proc.stderr

    passed = exit_ok and output_match

    return {
        "passed": passed,
        "name": "console-test",
        "duration": duration,
        "exit_code": proc.returncode,
        "expected_exit_code": expected_exit_code,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "output_match": output_match,
    }


def run_fuzz_test(
    project_root: Path,
    iterations: int = 10,
    timeout: int = 60,
) -> list[dict[str, Any]]:
    import random
    import string

    results: list[dict[str, Any]] = []
    for i in range(iterations):
        input_len = random.randint(0, 100)
        fuzz_input = "".join(random.choices(string.printable, k=input_len))
        result = run_console_test(
            project_root,
            input_data=fuzz_input,
            timeout=max(1, timeout // iterations),
        )
        result["name"] = f"fuzz-{i}"
        result["input_length"] = input_len
        results.append(result)
    return results
