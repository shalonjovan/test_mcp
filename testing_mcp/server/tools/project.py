from __future__ import annotations

from fastmcp import FastMCP

from testing_mcp.analyzers.project import analyze_project
from testing_mcp.generators.tests import generate_unit_tests, save_generated_tests
from testing_mcp.reporters.report import generate_html_report, generate_json_report, generate_markdown_report
from testing_mcp.runners.console import run_console_test, run_fuzz_test
from testing_mcp.runners.java_runner import discover_java_tests, run_gradle_tests, run_maven_tests
from testing_mcp.runners.mutation import run_mutation_test
from testing_mcp.runners.python_runner import discover_python_tests, run_pytest
from testing_mcp.server.tools._helpers import _resolve_path


def register_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    def analyze_project_tool(path: str = ".") -> dict:
        """Analyze a project and detect its language, framework, and structure."""
        root = _resolve_path(path)
        return analyze_project(root)

    @mcp.tool()
    def run_tests(
        path: str = ".",
        framework: str = "auto",
        test_names: list[str] | None = None,
    ) -> dict:
        """Discover and run tests in the project."""
        root = _resolve_path(path)
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
        root = _resolve_path(path)
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
        root = _resolve_path(path)
        results = run_fuzz_test(root, iterations=iterations, timeout=timeout)
        return {
            "project": str(root),
            "iterations": iterations,
            "crashes": sum(1 for r in results if r.get("exit_code", 0) != 0 or r.get("error")),
            "results": results,
        }

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
            out_path = _resolve_path(output)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(content)

        return {"format": format, "content": content, "output_file": output if output else None}

    @mcp.tool()
    def generate_tests(
        source_file: str,
        framework: str = "auto",
        functions: list[str] | None = None,
        dry_run: bool = True,
    ) -> dict:
        """Generate unit tests for a source file."""
        _resolve_path(source_file)
        test_data = generate_unit_tests(source_file, framework=framework, functions=functions)
        save_result = save_generated_tests(test_data, dry_run=dry_run)
        return {**test_data, **save_result}

    @mcp.tool()
    def mutation_test(
        source_file: str,
        test_command: str,
        mutation_types: list[str] | None = None,
    ) -> dict:
        """Run mutation tests to evaluate test quality."""
        return run_mutation_test(source_file, test_command, mutation_types=mutation_types)
