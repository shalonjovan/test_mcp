from __future__ import annotations

import time
from pathlib import Path

from fastmcp import FastMCP

from testing_mcp import __version__
from testing_mcp.analyzers.project import analyze_project
from testing_mcp.server.state import get_start_time
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
from testing_mcp.generators.tests import generate_unit_tests, save_generated_tests
from testing_mcp.runners.analysis import analyze_failure, suggest_fix
from testing_mcp.security.scanner import run_security_scan
from testing_mcp.runners.distributed import check_docker_available, check_kubernetes_available, detect_ci_config, get_infrastructure_info
from testing_mcp.runners.game_testing import detect_game_project, run_godot_tests, run_unity_tests, run_unreal_tests
from testing_mcp.runners.mobile import detect_mobile_project, run_android_tests, run_flutter_tests
from testing_mcp.api.graphql import detect_graphql_endpoint, introspect_schema, run_graphql_query
from testing_mcp.api.grpc_test import run_grpc_test
from testing_mcp.api.websocket_test import run_websocket_test
from testing_mcp.performance.profiler import (
    get_cpu_info,
    get_disk_io,
    get_network_io,
    measure_memory_usage,
    measure_startup_resources,
    profile_api_memory,
)
from testing_mcp.runners.integration import run_integration_tests, run_smoke_tests
from testing_mcp.runners.mutation import run_mutation_test
from testing_mcp.ui.accessibility import check_color_contrast, check_keyboard_navigation, run_accessibility_scan
from testing_mcp.ui.playwright import run_ui_test_sync
from testing_mcp.ui.visual_regression import compare_screenshots, generate_diff_gif, take_screenshot
from testing_mcp.browser import new_session, get_session, set_active_session, close_session, list_sessions


def register_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    def ping() -> dict:
        """Health check. Returns server status, version, and uptime."""
        uptime = time.time() - get_start_time()
        # Count tools from provider components
        tool_count = 0
        for p in mcp.providers:
            try:
                components = getattr(p, "_components", {})
                tool_count += sum(1 for k in components if k.startswith("tool:"))
            except Exception:
                pass
        return {
            "status": "ok",
            "version": __version__,
            "uptime_seconds": round(uptime, 2),
            "tools_registered": tool_count,
        }

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

    @mcp.tool()
    def security_scan(
        path: str = ".",
        scan_type: str = "all",
        url: str = "",
        hostname: str = "",
        port: int = 443,
    ) -> dict:
        """Run security scans on the project.

        Scan types: all, sast, secrets, headers, tls, deps, bandit, semgrep
        """
        root = Path(path).resolve()
        return run_security_scan(
            path=root,
            scan_type=scan_type,
            url=url,
            hostname=hostname,
            port=port,
        )

    @mcp.tool()
    def scan_sast(path: str = ".") -> dict:
        """Static analysis: detect SQLi, XSS, CSRF, SSRF, path traversal, weak crypto."""
        from testing_mcp.security.sast import run_sast_scan
        return run_sast_scan(path)

    @mcp.tool()
    def scan_secrets(path: str = ".") -> dict:
        """Scan for hardcoded secrets, API keys, tokens, and credentials."""
        from testing_mcp.security.secrets import scan_for_secrets
        return scan_for_secrets(path)

    @mcp.tool()
    def scan_headers(url: str) -> dict:
        """Check HTTP security headers (HSTS, CSP, X-Frame-Options, etc.)."""
        from testing_mcp.security.headers import scan_headers_sync
        return scan_headers_sync(url)

    @mcp.tool()
    def scan_tls(hostname: str, port: int = 443) -> dict:
        """Check TLS/SSL certificate validity and expiration."""
        from testing_mcp.security.tls import check_tls
        return check_tls(hostname, port=port)

    @mcp.tool()
    def generate_tests(
        source_file: str,
        framework: str = "auto",
        functions: list[str] | None = None,
        dry_run: bool = True,
    ) -> dict:
        """Generate unit tests for a source file."""
        test_data = generate_unit_tests(source_file, framework=framework, functions=functions)
        save_result = save_generated_tests(test_data, dry_run=dry_run)
        return {**test_data, **save_result}

    @mcp.tool()
    def inspect_logs(
        log_content: str,
        log_file: str = "",
        error_patterns: list[str] | None = None,
    ) -> dict:
        """Analyze log content for errors and patterns."""
        if log_file:
            try:
                log_content = Path(log_file).read_text()
            except (OSError, FileNotFoundError) as e:
                return {"error": f"Could not read log file: {e}"}

        import re
        patterns = error_patterns or [
            r"(?i)(error|exception|traceback|failed|failure)",
            r"(?i)(timeout|timed?\s*out)",
            r"(?i)(crash|segfault|abort)",
            r"(?i)(permission denied|access denied)",
        ]

        lines = log_content.split("\n")
        matches: list[dict] = []
        for i, line in enumerate(lines, 1):
            for pattern in patterns:
                if re.search(pattern, line):
                    matches.append({"line": i, "content": line.strip(), "pattern": pattern})
                    break

        return {
            "total_lines": len(lines),
            "matches_found": len(matches),
            "matches": matches[:100],
        }

    @mcp.tool()
    def compare_runs(
        baseline: list[dict],
        current: list[dict],
    ) -> dict:
        """Compare two test runs and identify regressions."""
        baseline_map = {r.get("name", ""): r for r in baseline}
        current_map = {r.get("name", ""): r for r in current}

        regressions: list[dict] = []
        improvements: list[dict] = []
        new: list[dict] = []
        fixed: list[dict] = []

        all_names = set(list(baseline_map.keys()) + list(current_map.keys()))

        for name in all_names:
            b = baseline_map.get(name)
            c = current_map.get(name)

            if b and c:
                if b.get("passed") and not c.get("passed"):
                    regressions.append({"name": name, "was": "pass", "now": "fail"})
                elif not b.get("passed") and c.get("passed"):
                    improvements.append({"name": name, "was": "fail", "now": "pass"})
            elif b and not c:
                fixed.append({"name": name, "status": "missing"})
            elif c and not b:
                new.append({"name": name, "status": "new"})

        return {
            "baseline_total": len(baseline),
            "current_total": len(current),
            "regressions": regressions,
            "improvements": improvements,
            "new_tests": new,
            "removed_tests": fixed,
        }

    @mcp.tool()
    def suggest_fix(
        test_results: list[dict],
        source_files: list[str] | None = None,
    ) -> list[dict]:
        """Analyze test failures and suggest fixes."""
        return suggest_fix(test_results, source_files=source_files)

    @mcp.tool()
    def visual_regression(
        baseline: str,
        current: str,
        output_diff: str = "",
        threshold: float = 0.0,
    ) -> dict:
        """Compare two screenshots and highlight visual differences."""
        return compare_screenshots(baseline, current, output_path=output_diff, threshold=threshold)

    @mcp.tool()
    def take_screenshot_tool(
        url: str,
        output_path: str = "",
        viewport: dict[str, int] | None = None,
        full_page: bool = True,
    ) -> dict:
        """Take a screenshot of a webpage."""
        return take_screenshot(url, output_path=output_path, viewport=viewport, full_page=full_page)

    @mcp.tool()
    def create_diff_gif(
        baseline: str,
        current: str,
        output_path: str = "diff.gif",
        duration: int = 500,
    ) -> dict:
        """Create an animated GIF showing the transition between two screenshots."""
        return generate_diff_gif(baseline, current, output_path=output_path, duration=duration)

    @mcp.tool()
    def detect_mobile(path: str = ".") -> dict:
        """Detect if the project is a mobile app (Android, Flutter, React Native)."""
        root = Path(path).resolve()
        return detect_mobile_project(root)

    @mcp.tool()
    def run_mobile_tests(
        path: str = ".",
        platform: str = "android",
        test_type: str = "unit",
    ) -> dict:
        """Run mobile app tests (Android or Flutter)."""
        root = Path(path).resolve()
        if platform == "flutter":
            return run_flutter_tests(root)
        return run_android_tests(root, test_type=test_type)

    @mcp.tool()
    def detect_game(path: str = ".") -> dict:
        """Detect if the project is a game (Godot, Unity, Unreal)."""
        root = Path(path).resolve()
        return detect_game_project(root)

    @mcp.tool()
    def run_game_tests(
        path: str = ".",
        engine: str = "auto",
    ) -> dict:
        """Run game engine tests."""
        root = Path(path).resolve()
        if engine == "auto":
            detected = detect_game_project(root)
            engines = detected.get("engines", [])
            if not engines:
                return {"error": "No game engine detected"}
            engine = engines[0]

        if engine == "godot":
            return run_godot_tests(root)
        elif engine == "unity":
            return run_unity_tests(root)
        elif engine == "unreal":
            return run_unreal_tests(root)
        return {"error": f"Unknown engine: {engine}"}

    @mcp.tool()
    def infrastructure_info(path: str = ".") -> dict:
        """Get infrastructure info (Docker, K8s, CI config)."""
        root = Path(path).resolve()
        return {
            "infrastructure": get_infrastructure_info(),
            "ci_config": detect_ci_config(root),
        }

    @mcp.tool()
    def check_docker() -> dict:
        """Check if Docker is available and get info."""
        return check_docker_available()

    @mcp.tool()
    def check_kubernetes() -> dict:
        """Check if Kubernetes is available."""
        return check_kubernetes_available()

    @mcp.tool()
    def accessibility_scan(
        url: str,
        standard: str = "wcag2aa",
        include_iframe: bool = True,
        timeout: int = 30000,
    ) -> dict:
        """Run WCAG accessibility scan using axe-core."""
        import asyncio
        return asyncio.run(run_accessibility_scan(url, standard=standard, include_iframe=include_iframe, timeout=timeout))

    @mcp.tool()
    def check_color_contrast_tool(foreground: str, background: str) -> dict:
        """Check WCAG color contrast ratio between two colors."""
        return check_color_contrast(foreground, background)

    @mcp.tool()
    def graphql_test(
        url: str,
        query: str,
        variables: dict | None = None,
        timeout: float = 30.0,
    ) -> dict:
        """Run a GraphQL query against an endpoint."""
        import asyncio
        return asyncio.run(run_graphql_query(url, query, variables=variables, timeout=timeout))

    @mcp.tool()
    def graphql_introspect(url: str) -> dict:
        """Introspect a GraphQL schema."""
        import asyncio
        return asyncio.run(introspect_schema(url))

    @mcp.tool()
    def graphql_detect(base_url: str) -> dict:
        """Detect a GraphQL endpoint at common paths."""
        import asyncio
        path = asyncio.run(detect_graphql_endpoint(base_url))
        return {"found": path is not None, "endpoint": f"{base_url}{path}" if path else None}

    @mcp.tool()
    def websocket_test(
        url: str,
        message: str = "",
        timeout: float = 10.0,
    ) -> dict:
        """Test a WebSocket connection."""
        import asyncio
        return asyncio.run(test_websocket(url, message=message or None, timeout=timeout))

    @mcp.tool()
    def grpc_test(
        url: str,
        service: str,
        method: str,
        request_body: str = "",
        timeout: float = 30.0,
    ) -> dict:
        """Test a gRPC endpoint."""
        import asyncio
        return asyncio.run(test_grpc(url, service=service, method=method, request_body=request_body, timeout=timeout))

    @mcp.tool()
    def profile_memory(path: str = ".") -> dict:
        """Measure current process memory usage."""
        return measure_memory_usage()

    @mcp.tool()
    def profile_resources(command: str, iterations: int = 3) -> dict:
        """Measure startup time and resource usage of a command."""
        from pathlib import Path
        return measure_startup_resources(command.split(), cwd=Path.cwd(), iterations=iterations)

    @mcp.tool()
    def profile_api(url: str, iterations: int = 10) -> dict:
        """Profile API memory and latency."""
        import asyncio
        return asyncio.run(profile_api_memory(url, iterations=iterations))

    @mcp.tool()
    def system_info() -> dict:
        """Get system resource info (CPU, memory, disk, network)."""
        return {
            "cpu": get_cpu_info(),
            "memory": measure_memory_usage(),
            "disk": get_disk_io(),
            "network": get_network_io(),
        }

    @mcp.tool()
    def load_test(
        url: str = "",
        method: str = "GET",
        concurrent_users: int = 10,
        duration: int = 30,
        ramp_up: int = 5,
        think_time: float = 0.0,
        headers: str = "{}",
        body: str = "",
        timeout: int = 30,
    ) -> dict:
        """Run a load/stress test against a URL with configurable concurrency.

        Simulates multiple concurrent users making requests with optional
        ramp-up period and think time. Reports latency percentiles (p50/p95/p99),
        throughput, error rate, and status code distribution.
        """
        from testing_mcp.performance.load_test import run_load_test
        return run_load_test(
            url=url,
            method=method,
            concurrent_users=concurrent_users,
            duration=duration,
            ramp_up=ramp_up,
            think_time=think_time,
            headers=headers,
            body=body,
            timeout=timeout,
        )

    @mcp.tool()
    def integration_tests(
        path: str = ".",
        test_patterns: list[str] | None = None,
    ) -> dict:
        """Discover and run integration tests."""
        root = Path(path).resolve()
        return run_integration_tests(root, test_patterns=test_patterns)

    @mcp.tool()
    def smoke_tests(
        endpoints: list[str] | None = None,
        commands: list[str] | None = None,
        path: str = ".",
    ) -> dict:
        """Run smoke tests (check endpoints or commands respond)."""
        root = Path(path).resolve()
        return run_smoke_tests(root, endpoints=endpoints, commands=commands)

    @mcp.tool()
    def mutation_test(
        source_file: str,
        test_command: str,
        mutation_types: list[str] | None = None,
    ) -> dict:
        """Run mutation tests to evaluate test quality."""
        return run_mutation_test(source_file, test_command, mutation_types=mutation_types)

    @mcp.tool()
    def fix_gitignore(
        path: str = ".",
        patterns: list[str] | None = None,
    ) -> dict:
        """Add missing entries to .gitignore to prevent credential exposure."""
        from testing_mcp.fix.gitignore import add_to_gitignore
        return add_to_gitignore(path=path, patterns=patterns)

    @mcp.tool()
    def generate_dockerfile(
        path: str = ".",
    ) -> dict:
        """Generate a Dockerfile based on project language detection."""
        from testing_mcp.fix.docker import generate_dockerfile
        return generate_dockerfile(path=path)

    @mcp.tool()
    def generate_ci_workflow(
        path: str = ".",
        ci_type: str = "github-actions",
    ) -> dict:
        """Generate CI workflow config (GitHub Actions or GitLab CI)."""
        from testing_mcp.fix.ci import generate_ci_workflow
        return generate_ci_workflow(path=path, ci_type=ci_type)

    @mcp.tool()
    def extract_migration(
        path: str = ".",
        db_type: str = "sqlite",
        output_dir: str = "",
    ) -> dict:
        """Extract inline SQL schemas from source code into migration files."""
        from testing_mcp.fix.migrations import extract_schema_migrations
        return extract_schema_migrations(path=path, db_type=db_type, output_dir=output_dir)

    @mcp.tool()
    def browser_new_session(
        session_id: str = "",
        viewport_width: int = 1920,
        viewport_height: int = 1080,
        user_agent: str = "",
        locale: str = "en-US",
        timezone_id: str = "America/New_York",
        headless: bool = True,
    ) -> dict:
        """Create a new stealth browser session with anti-bot fingerprinting.
        Uses realistic viewport, user agent, timezone, and stealth JS overrides
        to bypass Cloudflare and other bot detection systems."""
        import asyncio
        return asyncio.run(new_session(
            session_id=session_id,
            viewport={"width": viewport_width, "height": viewport_height},
            user_agent=user_agent,
            locale=locale,
            timezone_id=timezone_id,
            headless=headless,
        ))

    @mcp.tool()
    def browser_list_sessions() -> dict:
        """List all active browser sessions with their status."""
        return list_sessions()

    @mcp.tool()
    def browser_set_active_session(session_id: str) -> dict:
        """Switch the active browser session by ID."""
        return set_active_session(session_id)

    @mcp.tool()
    def browser_close_session(session_id: str = "") -> dict:
        """Close a browser session (defaults to active session)."""
        import asyncio
        return asyncio.run(close_session(session_id))

    @mcp.tool()
    def browser_navigate(
        url: str,
        session_id: str = "",
        wait_until: str = "domcontentloaded",
        timeout: int = 30000,
        screenshot: bool = False,
    ) -> dict:
        """Navigate to a URL using the stealth browser session.
        Automatically handles Cloudflare challenges with retry logic.
        Returns page title, status code, and optional base64 screenshot."""
        import asyncio
        sess = get_session(session_id)
        if not sess:
            return {"success": False, "error": "No active session. Call browser_new_session first."}
        return asyncio.run(sess.navigate(
            url=url,
            wait_until=wait_until,
            timeout=timeout,
            screenshot=screenshot,
        ))

    @mcp.tool()
    def browser_click(
        selector: str,
        session_id: str = "",
        wait_after: int = 2000,
        timeout: int = 10000,
    ) -> dict:
        """Click an element identified by CSS selector."""
        import asyncio
        sess = get_session(session_id)
        if not sess:
            return {"success": False, "error": "No active session"}
        return asyncio.run(sess.click(selector, wait_after=wait_after, timeout=timeout))

    @mcp.tool()
    def browser_fill(
        selector: str,
        value: str,
        session_id: str = "",
        timeout: int = 10000,
    ) -> dict:
        """Fill a form field identified by CSS selector."""
        import asyncio
        sess = get_session(session_id)
        if not sess:
            return {"success": False, "error": "No active session"}
        return asyncio.run(sess.fill(selector, value, timeout=timeout))

    @mcp.tool()
    def browser_select_option(
        selector: str,
        value: str,
        session_id: str = "",
        timeout: int = 10000,
    ) -> dict:
        """Select an option from a dropdown/select element."""
        import asyncio
        sess = get_session(session_id)
        if not sess:
            return {"success": False, "error": "No active session"}
        return asyncio.run(sess.select_option(selector, value, timeout=timeout))

    @mcp.tool()
    def browser_get_text(
        selector: str = "body",
        session_id: str = "",
        timeout: int = 5000,
    ) -> dict:
        """Get visible text content from a page element."""
        import asyncio
        sess = get_session(session_id)
        if not sess:
            return {"success": False, "error": "No active session"}
        return asyncio.run(sess.get_text(selector, timeout=timeout))

    @mcp.tool()
    def browser_get_html(
        selector: str = "body",
        session_id: str = "",
    ) -> dict:
        """Get the full page HTML or inner HTML of a specific element."""
        import asyncio
        sess = get_session(session_id)
        if not sess:
            return {"success": False, "error": "No active session"}
        return asyncio.run(sess.get_html(selector))

    @mcp.tool()
    def browser_evaluate(
        js: str,
        session_id: str = "",
    ) -> dict:
        """Execute JavaScript in the browser page and return the result."""
        import asyncio
        sess = get_session(session_id)
        if not sess:
            return {"success": False, "error": "No active session"}
        return asyncio.run(sess.evaluate(js))

    @mcp.tool()
    def browser_screenshot(
        path: str = "",
        full_page: bool = True,
        session_id: str = "",
    ) -> dict:
        """Take a screenshot of the current page.
        If path is empty, returns base64-encoded PNG."""
        import asyncio
        sess = get_session(session_id)
        if not sess:
            return {"success": False, "error": "No active session"}
        return asyncio.run(sess.screenshot(path=path, full_page=full_page))

    @mcp.tool()
    def browser_get_cookies(session_id: str = "") -> dict:
        """Get all cookies from the current browser session."""
        import asyncio
        sess = get_session(session_id)
        if not sess:
            return {"success": False, "error": "No active session"}
        return asyncio.run(sess.get_cookies())
