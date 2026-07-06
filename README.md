# Testing MCP

A universal AI-powered testing server built on the Model Context Protocol (MCP).

Allows AI agents to inspect, execute, test, monitor, debug, and report on software projects.

## Quick Start

```bash
# Install
pip install -e ".[dev]"

# Install Playwright browsers (for UI testing)
playwright install chromium

# Optional security tools
pip install bandit semgrep trivy

# Start server (SSE mode)
testing-mcp serve

# Or stdio mode (for Claude Desktop, Cursor, etc.)
testing-mcp stdio
```

## MCP Client Configuration

Add to your MCP client config (`claude_desktop_config.json`, `~/.config/opencode/opencode.json`, etc.):

```json
{
  "mcpServers": {
    "testing-mcp": {
      "command": "testing-mcp",
      "args": ["stdio"]
    }
  }
}
```

Or copy `testing-mcp.json` to your project root for auto-discovery.

## Configuration

Create a `testing-mcp.toml` file in your project root:

```toml
[server]
host = "127.0.0.1"
port = 8080
```

## MCP Tools (31 total)

### Core
| Tool | Description |
|------|-------------|
| `analyze_project_tool` | Detect language, framework, structure, dependencies |
| `run_tests` | Discover and execute existing tests |
| `generate_tests` | AI-generate unit tests (pytest, unittest, Jest) |
| `generate_report` | Generate Markdown, HTML, or JSON reports |
| `compare_runs` | Regression comparison between test runs |
| `suggest_fix` | Root cause analysis and fix suggestions |
| `inspect_logs` | Log analysis with error pattern matching |
| `ping` | Health check |

### Testing
| Tool | Description |
|------|-------------|
| `console_test` | Test console apps (stdin, stdout, exit code) |
| `fuzz_test` | Fuzz test console apps with random input |
| `ui_test` | Playwright browser automation |
| `api_test` | API endpoint testing with schema validation |
| `discover_endpoints` | Auto-discover API endpoints |
| `database_validate` | Validate DB migrations, constraints, rollbacks |
| `performance_test` | Startup time, API latency, load testing |

### Security
| Tool | Description |
|------|-------------|
| `security_scan` | Run all security scans (modes: all, sast, secrets, headers, tls, deps) |
| `scan_sast` | Static analysis: SQLi, XSS, CSRF, SSRF, command injection, path traversal, weak crypto |
| `scan_secrets` | Scan for hardcoded API keys, tokens, credentials, certs |
| `scan_headers` | Check HTTP security headers (HSTS, CSP, X-Frame-Options, etc.) |
| `scan_tls` | Validate TLS/SSL certificate |

### Visual
| Tool | Description |
|------|-------------|
| `take_screenshot_tool` | Capture webpage screenshots |
| `visual_regression` | Compare screenshots, highlight differences |
| `create_diff_gif` | Animated GIF between baseline and current |

### Platform
| Tool | Description |
|------|-------------|
| `detect_mobile` | Detect Android, Flutter, React Native projects |
| `run_mobile_tests` | Run Android (Gradle) or Flutter tests |
| `detect_game` | Detect Godot, Unity, Unreal projects |
| `run_game_tests` | Run game engine tests |
| `infrastructure_info` | Docker, K8s, CI config detection |
| `check_docker` | Check Docker availability |
| `check_kubernetes` | Check Kubernetes availability |

## Security Scanning Details

### SAST (no external tools required)
12 built-in rules detect:
- **SQL Injection** — string concatenation, f-string queries
- **XSS** — innerHTML, dangerouslySetInnerHTML, unsafe templates
- **CSRF** — csrf_exempt decorators, disabled forgery protection
- **SSRF** — user-controlled URLs in requests/httpx/fetch
- **Command Injection** — os.system, subprocess with shell=True, exec/eval
- **Path Traversal** — open/Path with user-controlled paths
- **Weak Crypto** — MD5, SHA1, DES, RC4
- **Hardcoded Secrets** — passwords, API keys, tokens in source

### Secret Scanner
20 patterns including: AWS keys, GitHub/GitLab tokens, SSH keys, JWT, Stripe keys, Google API keys, Discord/Slack tokens, database connection strings, PGP keys, npm tokens, Azure connection strings

### HTTP Header Scanner
Checks for: Strict-Transport-Security, Content-Security-Policy, X-Content-Type-Options, X-Frame-Options, Referrer-Policy, Permissions-Policy, X-XSS-Protection, Cache-Control, CORS

### TLS/SSL Checker
Validates certificates, expiry dates, SAN entries, protocol versions

## Project Structure

```
testing_mcp/
├── analyzers/      # Project detection (language, framework, deps)
├── api/            # API testing (httpx, OpenAPI)
├── database/       # DB validation (migrations, constraints)
├── generators/     # AI test generation
├── performance/    # Benchmarking (Locust)
├── plugins/        # Plugin framework (Language, Framework, Reporter)
├── reporters/      # Report generation (Markdown/HTML/JSON)
├── runners/        # Test executors + analysis (Python, Java, JS, Go, Rust)
├── security/       # SAST, secrets, headers, TLS scanning
├── server/         # MCP server + tool registration
├── ui/             # Playwright UI automation + visual regression
└── utils/          # Configuration, utilities
```

## Running Tests

```bash
pip install -e ".[dev]"
pytest testing_mcp/tests/ -v
```

## Docker

```bash
docker compose up
```

## License

LGPL v2.1
