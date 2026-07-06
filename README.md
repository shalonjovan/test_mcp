# Testing MCP

A universal AI-powered testing server built on the Model Context Protocol (MCP).

Allows AI agents to inspect, execute, test, monitor, debug, and report on software projects.

## Quick Start

```bash
pip install -e ".[dev]"
playwright install
testing-mcp serve
```

## Configuration

Create a `testing-mcp.toml` file in your project root:

```toml
[server]
host = "127.0.0.1"
port = 8080
```

## MCP Tools

| Tool | Description |
|------|-------------|
| `analyze_project_tool` | Detect language, framework, structure, dependencies |
| `run_tests` | Discover and execute existing tests |
| `console_test` | Test console apps (stdin, stdout, exit code) |
| `fuzz_test` | Fuzz test console apps with random input |
| `ui_test` | Playwright browser automation |
| `api_test` | API endpoint testing with schema validation |
| `discover_endpoints` | Auto-discover API endpoints |
| `database_validate` | Validate DB migrations, constraints, rollbacks |
| `performance_test` | Startup time, API latency, load testing |
| `security_scan` | Bandit, Semgrep, Trivy security scans |
| `generate_tests` | AI-generate unit tests (pytest, unittest, Jest) |
| `inspect_logs` | Log analysis with error pattern matching |
| `compare_runs` | Regression comparison between test runs |
| `suggest_fix` | AI root cause analysis and fix suggestions |
| `generate_report` | Generate Markdown, HTML, or JSON reports |
| `visual_regression` | Compare screenshots, highlight differences |
| `take_screenshot_tool` | Capture webpage screenshots |
| `create_diff_gif` | Animated GIF between baseline and current |
| `detect_mobile` | Detect Android, Flutter, React Native projects |
| `run_mobile_tests` | Run Android (Gradle) or Flutter tests |
| `detect_game` | Detect Godot, Unity, Unreal projects |
| `run_game_tests` | Run game engine tests |
| `infrastructure_info` | Docker, K8s, CI config detection |
| `check_docker` | Check Docker availability |
| `check_kubernetes` | Check Kubernetes availability |
| `ping` | Health check |

## Project Structure

```
testing_mcp/
├── analyzers/      # Project detection
├── api/            # API testing (httpx)
├── database/       # DB validation
├── generators/     # AI test generation
├── performance/    # Benchmarking (Locust)
├── plugins/        # Plugin framework
├── reporters/      # Report generation (Markdown/HTML/JSON)
├── runners/        # Test executors + analysis
├── security/       # Security scanning
├── server/         # MCP server + tool registration
├── ui/             # Playwright + visual regression
└── utils/          # Configuration, utilities
```

## License

LGPL v2.1
