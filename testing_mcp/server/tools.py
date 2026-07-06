from __future__ import annotations

from pathlib import Path

from fastmcp import FastMCP

from testing_mcp.analyzers.project import analyze_project
from testing_mcp.reporters.report import generate_html_report, generate_json_report, generate_markdown_report
from testing_mcp.runners.console import run_console_test, run_fuzz_test
from testing_mcp.runners.java_runner import (
    discover_java_tests,
    run_gradle_tests,
    run_maven_tests,
)
from testing_mcp.runners.python_runner import discover_python_tests, run_pytest
from testing_mcp.api.testing import discover_api_endpoints, run_api_test_sync
from testing_mcp.database.validation import (
    detect_database,
    test_rollback,
    validate_constraints,
    validate_migrations,
)
from testing_mcp.performance.benchmark import (
    measure_api_latency,
    measure_startup_time,
    run_locust_benchmark,
)
from testing_mcp.ui.playwright import run_ui_test_sync


def register_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    def ping() -> str:
        return "pong"

    @mcp.tool()
    def analyze_project_tool(path: str = ".") -> dict:
        """Analyze a project and detect its language, framework, and structure."""
        root = Path(path).resolve()
        return analyze_project(root)

    @mcp.tool()
    def run_tests(
        path: str = ".",
        framework: str = "auto",
        test_names: list[str] | None = None,
    ) -> dict:
        """Discover and run tests in the project."""
        root = Path(path).resolve()
        analysis = analyze_project(root)
        results: list[dict] = []

        languages = analysis.get("languages", {})

        if "python" in languages and framework in ("auto", "pytest"):
            discovered = discover_python_tests(root)
            if discovered:
                test_results = run_pytest(root, test_paths=test_names or discovered)
                results.extend(r.to_dict() for r in test_results)

        if "java" in languages and framework in ("auto", "junit"):
            discovered = discover_java_tests(root)
            if discovered:
                if analysis.get("build_tools", {}).get("gradle"):
                    test_results = run_gradle_tests(root, test_classes=test_names)
                else:
                    test_results = run_maven_tests(root, test_classes=test_names)
                results.extend(r.to_dict() for r in test_results)

        return {
            "project": str(root),
            "test_frameworks": analysis.get("test_frameworks", {}),
            "total": len(results),
            "passed": sum(1 for r in results if r.get("passed")),
            "failed": sum(1 for r in results if not r.get("passed")),
            "results": results,
        }

    @mcp.tool()
    def console_test(
        path: str = ".",
        input_data: str = "",
        expected_output: str | None = None,
        expected_exit_code: int = 0,
        timeout: int = 30,
    ) -> dict:
        """Test a console application with stdin/stdout/exit code checks."""
        root = Path(path).resolve()
        return run_console_test(
            root,
            input_data=input_data,
            expected_output=expected_output,
            expected_exit_code=expected_exit_code,
            timeout=timeout,
        )

    @mcp.tool()
    def fuzz_test(
        path: str = ".",
        iterations: int = 10,
        timeout: int = 60,
    ) -> dict:
        """Fuzz test a console application with random inputs."""
        root = Path(path).resolve()
        results = run_fuzz_test(root, iterations=iterations, timeout=timeout)
        return {
            "project": str(root),
            "iterations": iterations,
            "crashes": sum(1 for r in results if r.get("exit_code", 0) != 0 or r.get("error")),
            "results": results,
        }

    @mcp.tool()
    def ui_test(
        url: str,
        actions: list[dict] | None = None,
        viewport: dict[str, int] | None = None,
        screenshot: bool = True,
        timeout: int = 30000,
    ) -> dict:
        """Run browser-based UI tests using Playwright."""
        return run_ui_test_sync(
            url=url,
            actions=actions,
            viewport=viewport,
            screenshot=screenshot,
            timeout=timeout,
        )

    @mcp.tool()
    def generate_report(
        results: list[dict],
        format: str = "markdown",
        title: str = "Test Report",
        output: str = "",
    ) -> dict:
        """Generate a test report in markdown, HTML, or JSON format."""
        if format == "html":
            content = generate_html_report(results, title)
        elif format == "json":
            content = generate_json_report(results, title)
        else:
            content = generate_markdown_report(results, title)

        if output:
            out_path = Path(output)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(content)

        return {"format": format, "content": content, "output_file": output if output else None}

    @mcp.tool()
    def api_test(
        base_url: str,
        method: str = "GET",
        path: str = "/",
        headers: dict[str, str] | None = None,
        body: dict | None = None,
        expected_status: int = 200,
        expected_schema: dict | None = None,
        timeout: float = 30.0,
    ) -> dict:
        """Test an API endpoint with request/response validation."""
        return run_api_test_sync(
            base_url=base_url,
            method=method,
            path=path,
            headers=headers,
            body=body,
            expected_status=expected_status,
            expected_schema=expected_schema,
            timeout=timeout,
        )

    @mcp.tool()
    def discover_endpoints(
        base_url: str,
        paths: list[str] | None = None,
    ) -> list[dict]:
        """Discover API endpoints from a base URL."""
        import asyncio
        return asyncio.run(discover_api_endpoints(base_url, paths))

    @mcp.tool()
    def database_validate(
        path: str = ".",
        check_type: str = "all",
    ) -> dict:
        """Validate database migrations, constraints, and rollbacks."""
        root = Path(path).resolve()
        db_types = detect_database(root)
        db_type = max(db_types, key=db_types.get) if db_types else "sqlite"

        result: dict = {"database_type": db_type, "detected_databases": db_types}

        if check_type in ("all", "migrations"):
            result["migrations"] = validate_migrations(root, db_type=db_type)

        if check_type in ("all", "constraints"):
            result["constraints"] = validate_constraints(root, db_type=db_type)

        if check_type in ("all", "rollback"):
            result["rollback"] = test_rollback(root)

        return result

    @mcp.tool()
    def performance_test(
        type: str = "startup",
        command: str = "",
        url: str = "",
        method: str = "GET",
        iterations: int = 5,
        users: int = 10,
        run_time: str = "30s",
    ) -> dict:
        """Run performance benchmarks (startup time, API latency, or load test)."""
        if type == "startup" and command:
            cmd_parts = command.split()
            return measure_startup_time(cmd_parts, iterations=iterations)

        if type == "latency" and url:
            import asyncio
            return asyncio.run(measure_api_latency(url, method=method, iterations=iterations))

        if type == "load":
            return run_locust_benchmark(
                host=url or "http://localhost:8080",
                users=users,
                run_time=run_time,
            )

        return {"error": "Invalid performance test type or missing parameters"}
