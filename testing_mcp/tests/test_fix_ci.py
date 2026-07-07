from __future__ import annotations

import tempfile
from pathlib import Path

from testing_mcp.fix.ci import generate_ci_workflow


def test_generate_github_actions():
    with tempfile.TemporaryDirectory() as d:
        Path(d, "pyproject.toml").write_text("[project]\nname = 'test'\n")
        result = generate_ci_workflow(d, ci_type="github-actions")
        assert result["ci_type"] == "github-actions"
        assert "name: CI" in result["content"]
        assert "actions/checkout" in result["content"]
        assert Path(result["path"]).exists()


def test_generate_gitlab_ci():
    with tempfile.TemporaryDirectory() as d:
        Path(d, "pyproject.toml").write_text("[project]\nname = 'test'\n")
        result = generate_ci_workflow(d, ci_type="gitlab-ci")
        assert result["ci_type"] == "gitlab-ci"
        assert "stages:" in result["content"]
        assert Path(result["path"]).exists()


def test_github_actions_includes_test():
    with tempfile.TemporaryDirectory() as d:
        Path(d, "pyproject.toml").write_text("[project]\nname = 'test'\n")
        result = generate_ci_workflow(d)
        assert "pytest" in result["content"]


def test_github_actions_includes_docker_when_dockerfile_exists():
    with tempfile.TemporaryDirectory() as d:
        Path(d, "pyproject.toml").write_text("[project]\nname = 'test'\n")
        Path(d, "Dockerfile").write_text("FROM python:3.12-slim\n")
        result = generate_ci_workflow(d)
        assert "docker build" in result["content"]
