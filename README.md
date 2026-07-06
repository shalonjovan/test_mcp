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

## Tools

| Tool | Description |
|------|-------------|
| `analyze_project` | Detect language, framework, structure |
| `run_tests` | Execute existing tests |
| `generate_tests` | AI-generate missing tests |
| `ui_test` | Playwright browser automation |
| `api_test` | API endpoint testing |
| `performance_test` | Benchmarking |
| `security_scan` | Security checks |
| `inspect_logs` | Log analysis |
| `compare_runs` | Regression comparison |
| `generate_report` | Report generation |
| `suggest_fix` | AI debugging |

## License

LGPL v2.1
