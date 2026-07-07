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

## MCP Tools (62 total)

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
| `fix_gitignore` | Add missing entries to prevent credential leaks |
| `generate_dockerfile` | Auto-generate Dockerfile from project |
| `generate_ci_workflow` | Generate GitHub Actions or GitLab CI config |
| `extract_migration` | Extract inline SQL schemas into migration files |
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
| `load_test` | Concurrent load/stress testing with latency percentiles |
| `integration_tests` | Discover and run integration tests |
| `smoke_tests` | Smoke test endpoints and commands |
| `mutation_test` | Mutation testing to evaluate test quality |

### Security
| Tool | Description |
|------|-------------|
| `security_scan` | Run all security scans (modes: all, sast, secrets, headers, tls, deps, dast, crawl) |
| `scan_sast` | Static analysis: SQLi, XSS, CSRF, SSRF, CMDI, path traversal, weak crypto, etc. |
| `scan_secrets` | Scan for hardcoded API keys, tokens, credentials, certs |
| `scan_headers` | Check HTTP security headers (HSTS, CSP, X-Frame-Options, etc.) |
| `scan_tls` | Validate TLS/SSL certificate |

### Browser Automation (Stealth)
| Tool | Description |
|------|-------------|
| `browser_new_session` | Create stealth browser session (anti-bot fingerprinting) |
| `browser_navigate` | Navigate to URL, auto-handle Cloudflare challenges |
| `browser_click` | Click element by CSS selector |
| `browser_fill` | Fill form fields |
| `browser_select_option` | Select dropdown option |
| `browser_get_text` | Get visible text from page/element |
| `browser_get_html` | Get full page or element HTML |
| `browser_evaluate` | Execute arbitrary JavaScript |
| `browser_screenshot` | Save screenshot to file or return base64 |
| `browser_get_cookies` | List session cookies |
| `browser_list_sessions` | Show all active browser sessions |
| `browser_set_active_session` | Switch active session |
| `browser_close_session` | Close and clean up session |

### Visual
| Tool | Description |
|------|-------------|
| `take_screenshot_tool` | Capture webpage screenshots |
| `visual_regression` | Compare screenshots, highlight differences |
| `create_diff_gif` | Animated GIF between baseline and current |
| `accessibility_scan` | WCAG accessibility scan using axe-core |
| `check_color_contrast_tool` | Check WCAG color contrast ratio |

### API & Protocol
| Tool | Description |
|------|-------------|
| `graphql_test` | Run GraphQL queries |
| `graphql_introspect` | Introspect GraphQL schema |
| `graphql_detect` | Detect GraphQL endpoint |
| `websocket_test` | Test WebSocket connections |
| `grpc_test` | Test gRPC endpoints |

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

### Profiling
| Tool | Description |
|------|-------------|
| `profile_memory` | Measure current memory usage |
| `profile_resources` | Measure startup time and resource usage |
| `profile_api` | Profile API memory and latency |
| `system_info` | CPU, memory, disk, network info |

## Security Scanning Details

### SAST (30 built-in rules)
Detects 15+ vulnerability classes:
- **SQL Injection** — string concatenation, f-string, raw queries
- **XSS** — innerHTML, dangerouslySetInnerHTML, unsafe template rendering
- **Command Injection** — os.system, subprocess(shell=True), exec/eval, popen
- **SSTI** — Template injection (Jinja2, Flask `render_template_string`)
- **Path Traversal** — open/Path with user-controlled paths, unsafe joins
- **SSRF** — User-controlled URLs in requests/httpx/fetch/urlopen
- **CSRF** — csrf_exempt decorators, disabled Django CSRF middleware
- **IDOR** — Insecure direct object references in params
- **LDAP Injection** — Unsanitized LDAP search filters
- **XXE** — XML parser with external entity expansion enabled
- **Deserialization** — pickle.loads, yaml.load, marshal.load
- **Hardcoded Secrets** — passwords, API keys, tokens in source code
- **Weak Crypto** — MD5, SHA1, DES, RC4, ECB mode
- **Weak CORS** — `Access-Control-Allow-Origin: *` with credentials
- **Prototype Pollution** — Unsafe object merge/assign
- **Mass Assignment** — `**kwargs` or `update()` with request data
- **Race Condition** — TOCTOU patterns in file operations
- **File Upload** — Unrestricted file upload without validation
- **ReDoS** — Unsafe regex patterns with user input
- **Info Disclosure** — Stack traces, debug endpoints exposed
- **Debug Mode** — Flask debug mode enabled in production

### Secret Scanner (25+ patterns)
Scans for: AWS keys, GitHub tokens, GitLab tokens, Slack tokens, Discord tokens, JWT tokens, Stripe keys, SSH private keys, PGP private keys, Google API keys, Azure keys, GCP keys, Telegram tokens, Twilio credentials, Heroku API keys, npm tokens, npmrc auth tokens, database connection strings (MySQL, PostgreSQL, MongoDB, Redis), and generic bearer/token patterns

### HTTP Header Scanner (15 checks)
Validates: Strict-Transport-Security (incl. weak `max-age`), Content-Security-Policy (incl. unsafe `script-src 'unsafe-inline'`), X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy, Cross-Origin-Embedder-Policy, Cross-Origin-Opener-Policy, Cross-Origin-Resource-Policy, Server disclosure, X-Powered-By disclosure

### TLS/SSL Checker
Validates certificates, expiry dates, SAN entries, protocol versions

### DAST (Dynamic Analysis)
- Technology fingerprinting (server headers, cookies, framework patterns)
- Endpoint discovery (JS source mapping, common API paths)
- SQL injection detection (error-based, time-based)
- XSS detection (reflected payloads)
- Authentication-aware scanning

### Dependency Scanner
Scans lockfiles via OSV.dev API:
- `requirements.txt`, `Pipfile.lock`, `poetry.lock`
- `package-lock.json`, `Cargo.lock`, `Gemfile.lock`, `go.sum`

### Configuration Scanner
**Docker Checks (10)**: Running as root, latest tag used, ADD vs COPY, secrets in build args, exposed ports, HEALTHCHECK missing, no .dockerignore, vulnerable base images, shell in ENTRYPOINT, multi-stage build missing
**K8s Checks (10)**: Privileged containers, hostNetwork, runAsNonRoot, readOnlyRootFilesystem, allowPrivilegeEscalation, resource limits, seccomp, securityContext, hostPID/IPC, ServiceAccount token mount
**CI/CD Checks (5)**: Hardcoded secrets, unpinned actions, script injection, missing code checkout, missing artifact upload

### Web Crawler
Discovers endpoints and files via:
- HTML source patterns (forms, links, scripts, API endpoints)
- JS source scanning (XHR/fetch URLs, route patterns)
- Common files (robots.txt, sitemap.xml, security.txt, .well-known/)

### Reporter
Unified report builder that aggregates all scan results with:
- Deduplication of findings across scanners
- Risk scoring (NONE → INFO → LOW → MEDIUM → HIGH → CRITICAL)
- Text and JSON output formats

## Project Structure

```
testing_mcp/
├── analyzers/      # Project detection (language, framework, deps)
├── api/            # API testing (httpx, OpenAPI, GraphQL, WebSocket, gRPC)
├── browser/        # Stealth browser automation (anti-bot fingerprinting, Cloudflare bypass)
├── database/       # DB validation (migrations, constraints)
├── fix/            # Remediation tools (gitignore, Docker, CI, migrations)
├── generators/     # AI test generation
├── performance/    # Benchmarking (Locust, load/stress testing, profiling)
├── plugins/        # Plugin framework (Language, Framework, Reporter)
├── reporters/      # Report generation (Markdown/HTML/JSON)
├── runners/        # Test executors + analysis (Python, Java, JS, Go, Rust, mobile, game)
├── security/       # SAST (30 rules), secrets (25+ patterns), headers, TLS, DAST,
│                   # dependency scanning (OSV.dev), config (Docker/K8s/CI),
│                   # web crawling, reporter
├── server/         # MCP server + tool registration
├── tests/          # Test suite (179+ tests covering all modules)
├── ui/             # Playwright UI automation + accessibility + visual regression
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
