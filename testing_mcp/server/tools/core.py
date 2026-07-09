from __future__ import annotations

import time

from fastmcp import FastMCP

from testing_mcp import __version__
from testing_mcp.performance.profiler import get_cpu_info, get_disk_io, get_network_io, measure_memory_usage
from testing_mcp.server.state import get_start_time


def register_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    def ping() -> dict:
        """Health check. Returns server status, version, and uptime."""
        uptime = time.time() - get_start_time()
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
    def system_info() -> dict:
        """Get system resource info (CPU, memory, disk, network)."""
        return {
            "cpu": get_cpu_info(),
            "memory": measure_memory_usage(),
            "disk": get_disk_io(),
            "network": get_network_io(),
        }
