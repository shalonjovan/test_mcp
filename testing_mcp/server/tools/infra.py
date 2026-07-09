from __future__ import annotations

from fastmcp import FastMCP

from testing_mcp.runners.distributed import (
    check_docker_available,
    check_kubernetes_available,
    detect_ci_config,
    get_infrastructure_info,
)
from testing_mcp.runners.integration import run_integration_tests, run_smoke_tests
from testing_mcp.server.tools._helpers import _resolve_path


def register_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    def infrastructure_info(path: str = ".") -> dict:
        """Get infrastructure info (Docker, K8s, CI config)."""
        root = _resolve_path(path)
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
    def integration_tests(
        path: str = ".",
        test_patterns: list[str] | None = None,
    ) -> dict:
        """Discover and run integration tests."""
        root = _resolve_path(path)
        return run_integration_tests(root, test_patterns=test_patterns)

    @mcp.tool()
    def smoke_tests(
        endpoints: list[str] | None = None,
        commands: list[str] | None = None,
        path: str = ".",
    ) -> dict:
        """Run smoke tests (check endpoints or commands respond)."""
        root = _resolve_path(path)
        return run_smoke_tests(root, endpoints=endpoints, commands=commands)
