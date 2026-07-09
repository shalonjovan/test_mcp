from __future__ import annotations

from fastmcp import FastMCP

from testing_mcp.fix.ci import generate_ci_workflow as _gen_ci
from testing_mcp.fix.docker import generate_dockerfile as _gen_docker
from testing_mcp.fix.gitignore import add_to_gitignore
from testing_mcp.runners.analysis import suggest_fix as _suggest_fix


def register_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    def suggest_fix(
        test_results: list[dict],
        source_files: list[str] | None = None,
    ) -> list[dict]:
        """Analyze test failures and suggest fixes."""
        return _suggest_fix(test_results, source_files=source_files)

    @mcp.tool()
    def fix_gitignore(
        path: str = ".",
        patterns: list[str] | None = None,
    ) -> dict:
        """Add missing entries to .gitignore to prevent credential exposure."""
        return add_to_gitignore(path=path, patterns=patterns)

    @mcp.tool()
    def generate_dockerfile(
        path: str = ".",
    ) -> dict:
        """Generate a Dockerfile based on project language detection."""
        return _gen_docker(path=path)

    @mcp.tool()
    def generate_ci_workflow(
        path: str = ".",
        ci_type: str = "github-actions",
    ) -> dict:
        """Generate CI workflow config (GitHub Actions or GitLab CI)."""
        return _gen_ci(path=path, ci_type=ci_type)
