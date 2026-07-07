from __future__ import annotations

from pathlib import Path
from typing import Any

from testing_mcp.analyzers.project import analyze_project


def generate_ci_workflow(
    path: str = ".",
    ci_type: str = "github-actions",
) -> dict[str, Any]:
    root = Path(path).resolve()
    analysis = analyze_project(root)
    languages = analysis.get("languages", {})

    if ci_type == "gitlab-ci":
        return _generate_gitlab_ci(root, analysis, languages)

    return _generate_github_actions(root, analysis, languages)


def _generate_github_actions(root: Path, analysis: dict[str, Any], languages: dict[str, float]) -> dict[str, Any]:
    workflow_dir = root / ".github" / "workflows"
    workflow_dir.mkdir(parents=True, exist_ok=True)

    test_step: list[str] = []
    lint_step: list[str] = []
    setup_step: list[str] = []
    docker_step: list[str] = []

    if "python" in languages:
        setup_step = [
            "      - name: Set up Python",
            "        uses: actions/setup-python@v5",
            '        with:',
            '          python-version: "3.12"',
            "",
            "      - name: Install dependencies",
            "        run: |",
            "          python -m pip install --upgrade pip",
            "          pip install -e .",
            '          pip install pytest ruff',
        ]
        lint_step = [
            "      - name: Lint",
            "        run: |",
            "          ruff check .",
        ]
        test_step = [
            "      - name: Test",
            "        run: |",
            "          pytest -v --tb=short",
        ]
    elif "node" in languages or "javascript" in languages or "typescript" in languages:
        setup_step = [
            "      - name: Set up Node.js",
            "        uses: actions/setup-node@v4",
            '        with:',
            '          node-version: "20"',
            "",
            "      - name: Install dependencies",
            "        run: npm ci",
        ]
        lint_step = [
            "      - name: Lint",
            "        run: npm run lint",
        ]
        test_step = [
            "      - name: Test",
            "        run: npm test",
        ]
    elif "go" in languages:
        setup_step = [
            "      - name: Set up Go",
            "        uses: actions/setup-go@v5",
            '        with:',
            '          go-version: "1.22"',
            "",
            "      - name: Install dependencies",
            "        run: go mod download",
        ]
        lint_step = [
            "      - name: Lint",
            "        run: go vet ./...",
        ]
        test_step = [
            "      - name: Test",
            "        run: go test ./...",
        ]
    elif "rust" in languages:
        setup_step = [
            "      - name: Set up Rust",
            "        uses: actions-rs/toolchain@v1",
            '        with:',
            '          toolchain: stable',
            "",
            "      - name: Build",
            "        run: cargo build --verbose",
        ]
        test_step = [
            "      - name: Test",
            "        run: cargo test --verbose",
        ]

    docker_check: list[str] = []
    if root.joinpath("Dockerfile").exists():
        docker_check = [
            "      - name: Check Dockerfile",
            "        run: docker build . --tag test-build",
        ]

    lines = [
        "name: CI",
        "",
        "on:",
        "  push:",
        "    branches: [main]",
        "  pull_request:",
        "    branches: [main]",
        "",
        "jobs:",
        "  build-and-test:",
        "    runs-on: ubuntu-latest",
        "",
        "    steps:",
        "      - name: Checkout",
        "        uses: actions/checkout@v4",
        "",
    ]
    lines.extend(setup_step)
    if lint_step:
        lines.extend([""] + lint_step)
    if test_step:
        lines.extend([""] + test_step)
    if docker_check:
        lines.extend([""] + docker_check)

    workflow_path = workflow_dir / "ci.yml"
    content = "\n".join(lines) + "\n"
    workflow_path.write_text(content)

    return {
        "path": str(workflow_path),
        "ci_type": "github-actions",
        "lines": len(lines),
        "content": content,
    }


def _generate_gitlab_ci(root: Path, analysis: dict[str, Any], languages: dict[str, float]) -> dict[str, Any]:
    lines: list[str] = [
        "stages:",
        "  - test",
        "",
    ]

    if "python" in languages:
        lines.extend([
            "python-test:",
            "  image: python:3.12-slim",
            "  script:",
            "    - pip install -e .",
            "    - pytest -v --tb=short",
        ])
    elif "node" in languages:
        lines.extend([
            "node-test:",
            "  image: node:20-slim",
            "  script:",
            "    - npm ci",
            "    - npm test",
        ])
    elif "go" in languages:
        lines.extend([
            "go-test:",
            "  image: golang:1.22",
            "  script:",
            "    - go test ./...",
        ])
    else:
        lines.extend([
            "test:",
            "  script:",
            "    - echo 'No test configuration found'",
        ])

    ci_path = root / ".gitlab-ci.yml"
    content = "\n".join(lines) + "\n"
    ci_path.write_text(content)

    return {
        "path": str(ci_path),
        "ci_type": "gitlab-ci",
        "lines": len(lines),
        "content": content,
    }
