from __future__ import annotations

import re
from typing import Any


def analyze_failure(
    test_name: str,
    stdout: str = "",
    stderr: str = "",
    test_file: str = "",
    source_files: list[str] | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "test_name": test_name,
        "probable_cause": "",
        "affected_modules": [],
        "confidence": 0.0,
        "suggested_fix": "",
    }

    combined = stdout + "\n" + stderr

    if "AssertionError" in stderr or "AssertionError" in stdout:
        result["probable_cause"] = "Assertion failure"
        result["confidence"] = 0.9

        assertion_match = re.search(
            r"assert\s+(.+?)\n",
            combined,
            re.DOTALL,
        )
        if assertion_match:
            result["suggested_fix"] = (
                f"Check the assertion: {assertion_match.group(1).strip()[:100]}. "
                "Verify the expected value matches actual output."
            )

    elif "Timeout" in combined or "timeout" in combined.lower():
        result["probable_cause"] = "Timeout"
        result["confidence"] = 0.8
        result["suggested_fix"] = (
            "Increase timeout or optimize slow operation. "
            "Consider adding timeouts to network calls or database queries."
        )

    elif "ImportError" in stderr or "ModuleNotFoundError" in stderr:
        result["probable_cause"] = "Missing dependency"
        result["confidence"] = 0.95

        module_match = re.search(
            r"(?:ImportError|ModuleNotFoundError):\s*(?:No module named\s+)?['\"]?(\w+)['\"]?",
            combined,
        )
        if module_match:
            result["suggested_fix"] = (
                f"Install missing module: pip install {module_match.group(1)}"
            )

    elif "SyntaxError" in stderr:
        result["probable_cause"] = "Syntax error"
        result["confidence"] = 0.95

        syntax_match = re.search(
            r"SyntaxError:\s*(.+?)\n",
            combined,
        )
        if syntax_match:
            result["suggested_fix"] = (
                f"Fix syntax: {syntax_match.group(1).strip()[:100]}"
            )

    elif "TypeError" in stderr:
        result["probable_cause"] = "Type mismatch"
        result["confidence"] = 0.85

        type_match = re.search(
            r"TypeError:\s*(.+?)\n",
            combined,
        )
        if type_match:
            result["suggested_fix"] = (
                f"Fix type: {type_match.group(1).strip()[:100]}"
            )

    elif "KeyError" in stderr or "IndexError" in stderr:
        result["probable_cause"] = "Missing key or index"
        result["confidence"] = 0.85
        result["suggested_fix"] = (
            "Check that the expected key/index exists before accessing it. "
            "Use .get() for dicts or check bounds for lists."
        )

    elif "ConnectionError" in combined or "ConnectionRefused" in combined:
        result["probable_cause"] = "Connection refused"
        result["confidence"] = 0.9
        result["suggested_fix"] = (
            "Ensure the service is running and accessible at the expected address/port."
        )

    elif "Permission" in combined:
        result["probable_cause"] = "Permission denied"
        result["confidence"] = 0.8
        result["suggested_fix"] = (
            "Check file/directory permissions or run with appropriate privileges."
        )

    elif "MemoryError" in combined:
        result["probable_cause"] = "Out of memory"
        result["confidence"] = 0.7
        result["suggested_fix"] = (
            "Reduce memory usage by processing data in chunks or increasing available memory."
        )

    else:
        if proc := re.search(r"(.+?Error):\s*(.+)", combined):
            result["probable_cause"] = proc.group(1)
            result["suggested_fix"] = f"Investigate error: {proc.group(2).strip()[:100]}"
            result["confidence"] = 0.5
        else:
            result["probable_cause"] = "Unknown failure"
            result["suggested_fix"] = "Review test output for details."
            result["confidence"] = 0.3

    if test_file:
        result["affected_modules"] = _find_affected_modules(test_file, source_files)

    return result


def _find_affected_modules(test_file: str, source_files: list[str] | None = None) -> list[str]:
    modules: list[str] = [test_file]
    if source_files:
        modules.extend(source_files)
    return modules


def suggest_fix(
    test_results: list[dict],
    source_files: list[str] | None = None,
) -> list[dict[str, Any]]:
    analyses: list[dict[str, Any]] = []

    for result in test_results:
        if not result.get("passed", True):
            analysis = analyze_failure(
                test_name=result.get("name", "unknown"),
                stdout=result.get("stdout", ""),
                stderr=result.get("stderr", ""),
                test_file=result.get("test_file", ""),
                source_files=source_files,
            )
            analyses.append(analysis)

    return analyses
