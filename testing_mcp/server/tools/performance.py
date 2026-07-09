from __future__ import annotations

import asyncio
from pathlib import Path

from fastmcp import FastMCP

from testing_mcp.performance.benchmark import measure_api_latency, measure_startup_time, run_locust_benchmark
from testing_mcp.performance.load_test import run_load_test
from testing_mcp.performance.profiler import measure_memory_usage, measure_startup_resources, profile_api_memory
from testing_mcp.server.tools._helpers import _resolve_command


def register_tools(mcp: FastMCP) -> None:
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
            cmd_parts = _resolve_command(command)
            return measure_startup_time(cmd_parts, iterations=iterations)

        if type == "latency" and url:
            return asyncio.run(measure_api_latency(url, method=method, iterations=iterations))

        if type == "load":
            return run_locust_benchmark(
                host=url or "http://localhost:8080",
                users=users,
                run_time=run_time,
            )

        return {"error": "Invalid performance test type or missing parameters"}

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
        """Run a load/stress test against a URL with configurable concurrency."""
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
    def profile_memory(path: str = ".") -> dict:
        """Measure current process memory usage."""
        return measure_memory_usage()

    @mcp.tool()
    def profile_resources(command: str, iterations: int = 3) -> dict:
        """Measure startup time and resource usage of a command."""
        cmd_parts = _resolve_command(command)
        return measure_startup_resources(cmd_parts, cwd=Path.cwd(), iterations=iterations)

    @mcp.tool()
    def profile_api(url: str, iterations: int = 10) -> dict:
        """Profile API memory and latency."""
        return asyncio.run(profile_api_memory(url, iterations=iterations))
