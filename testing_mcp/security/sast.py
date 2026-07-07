from __future__ import annotations

import re
from pathlib import Path
from typing import Any

SAST_RULES: list[dict[str, Any]] = [
    # ── SQL Injection ──
    {
        "id": "SQLI-001",
        "name": "SQL Injection - string concatenation",
        "severity": "HIGH",
        "description": "SQL query built via string concatenation",
        "patterns": [
            r'(?i)(?:execute|query|raw|run)\s*\(\s*["\'].*\b(?:SELECT|INSERT|UPDATE|DELETE)\b.*["\']\s*\+',
            r'(?i)(?:cursor|db|conn|pool)\.(?:execute|exec|query)\(\s*f["\']',
            r'(?i)\+.*\b(?:WHERE|AND|OR|SET|VALUES)\b.*\+',
        ],
        "remediation": "Use parameterized queries / prepared statements instead of string concatenation",
    },
    {
        "id": "SQLI-002",
        "name": "SQL Injection - f-string query",
        "severity": "HIGH",
        "description": "SQL query built with f-string or format()",
        "patterns": [
            r'(?i)(?:execute|query|raw)\s*\(\s*f["\'].*\b(?:SELECT|INSERT|UPDATE|DELETE)\b',
            r'(?i)(?:execute|query|raw)\s*\(\s*["\'].*\{\}.*["\']\.format\(',
            r'(?i)(?:execute|query|raw)\s*\(\s*["\'].*%s.*["\']\s*%',
        ],
        "remediation": "Use parameterized queries with ? or %s placeholders",
    },
    {
        "id": "NOSQLI-001",
        "name": "NoSQL Injection",
        "severity": "HIGH",
        "description": "NoSQL query built from user input without sanitization",
        "patterns": [
            r'(?i)\$\s*(?:where|gt|gte|lt|lte|ne|regex|exists|nin)\b',
            r'(?i)(?:find|findOne|findAndModify)\(\s*\{.*\$\w+',
        ],
        "remediation": "Validate and sanitize user input; avoid $where operator; use parameterized queries",
    },
    # ── Cross-Site Scripting ──
    {
        "id": "XSS-001",
        "name": "Cross-Site Scripting - unsafe HTML",
        "severity": "HIGH",
        "description": "Potentially unsafe HTML injection via innerHTML or similar",
        "patterns": [
            r'(?i)\.innerHTML\s*=\s*',
            r'(?i)\.outerHTML\s*=\s*',
            r'(?i)(?:document\.write|writeln)\s*\(',
            r'(?i)v-html\s*=',
            r'(?i)dangerouslySetInnerHTML',
            r'(?i)insertAdjacentHTML',
        ],
        "remediation": "Use textContent/innerText or sanitize input before inserting HTML",
    },
    {
        "id": "XSS-002",
        "name": "Cross-Site Scripting - unsafe template",
        "severity": "MEDIUM",
        "description": "Template variable rendered without escaping",
        "patterns": [
            r'(?i){{.*\|?\s*safe\s*}}',
            r'(?i)\{%\s*(?:autoescape|raw)\s+off\s*%\}',
            r'(?i)\.html\(\s*["\']',
        ],
        "remediation": "Ensure template variables are escaped by default; avoid |safe filter",
    },
    # ── CSRF ──
    {
        "id": "CSRF-001",
        "name": "Missing CSRF Protection",
        "severity": "MEDIUM",
        "description": "Form or AJAX endpoint without CSRF token",
        "patterns": [
            r'(?i)@csrf_exempt',
            r'(?i)csrf_exempt\s*=\s*True',
            r'(?i)@method_decorator.*csrf_exempt',
            r'(?i)protect_from_forgery\s*(?::|=>)?\s*false',
        ],
        "remediation": "Enable CSRF protection; use CSRF tokens in forms",
    },
    # ── SSRF ──
    {
        "id": "SSRF-001",
        "name": "Server-Side Request Forgery",
        "severity": "HIGH",
        "description": "URL constructed from user input without validation",
        "patterns": [
            r'(?i)requests?\.(?:get|post|put|delete)\(\s*f?["\'][^"\']*\{',
            r'(?i)urllib\.request\.urlopen\(\s*f?["\'][^"\']*\{',
            r'(?i)httpx\.(?:get|post|put|delete|request)\(\s*f?["\'][^"\']*\{',
            r'(?i)(?:fetch|axios)\(\s*[`\'][^`\']*\$\{',
        ],
        "remediation": "Validate and sanitize URLs; use an allowlist of permitted hosts",
    },
    # ── Path Traversal ──
    {
        "id": "PT-001",
        "name": "Path Traversal",
        "severity": "HIGH",
        "description": "File path constructed from user input",
        "patterns": [
            r'(?i)open\(\s*f?["\'][^"\']*\{',
            r'(?i)Path\(\s*f?["\'][^"\']*\{',
            r'(?i)os\.path\.(?:join|exists|isfile)\(\s*f?["\'][^"\']*\{',
            r'(?i)__import__\(\s*f?["\'][^"\']*["\']\s*\)',
        ],
        "remediation": "Use allowlisted paths; sanitize user input to remove ../ patterns",
    },
    # ── Cryptography ──
    {
        "id": "CRYPTO-001",
        "name": "Weak Cryptography",
        "severity": "MEDIUM",
        "description": "Use of weak/outdated cryptographic algorithm",
        "patterns": [
            r'(?i)(?:md5|sha1)\s*\(',
            r'(?i)hashlib\.md5',
            r'(?i)hashlib\.sha1',
            r'(?i)Cipher\.(?:DES|RC2|RC4)',
            r'(?i)crypto\.create(?:Cipher|Decipher)iv.*des',
            r'(?i)\.p12\b',
        ],
        "remediation": "Use SHA-256 or stronger; use AES-256-GCM instead of DES/RC4",
    },
    # ── Hardcoded Secrets ──
    {
        "id": "SECRET-001",
        "name": "Hardcoded Password",
        "severity": "HIGH",
        "description": "Potential hardcoded password or credential",
        "patterns": [
            r'(?i)password\s*[=:]\s*["\'][^"\'\s]{4,}["\']',
            r'(?i)passwd\s*[=:]\s*["\'][^"\'\s]{4,}["\']',
            r'(?i)pwd\s*[=:]\s*["\'][^"\'\s]{4,}["\']',
            r'(?i)secret\s*[=:]\s*["\'][^"\'\s]{8,}["\']',
            r'(?i)api_key\s*[=:]\s*["\'][^"\'\s]{8,}["\']',
            r'(?i)apikey\s*[=:]\s*["\'][^"\'\s]{8,}["\']',
            r'(?i)token\s*[=:]\s*["\'][^"\'\s]{16,}["\']',
        ],
        "remediation": "Use environment variables or a secrets manager; never hardcode credentials",
    },
    # ── Command Injection ──
    {
        "id": "CMDI-001",
        "name": "Command Injection",
        "severity": "CRITICAL",
        "description": "Shell command built from user input",
        "patterns": [
            r'(?i)os\.system\(\s*(?:f|b)?["\'][^"\']*\{',
            r'(?i)subprocess\.(?:run|Popen|call|check_output)\(\s*(?:f|b)?["\'][^"\']*\{',
            r'(?i)subprocess\.(?:run|Popen|call|check_output)\(\s*["\'][^"\']*["\']\s*,\s*shell\s*=\s*True',
            r'(?i)exec\(\s*(?:f|b)?["\'][^"\']*\{',
            r'(?i)eval\(\s*(?:f|b)?["\'][^"\']*\{',
            r'(?i)`.*\{.*`',
        ],
        "remediation": "Avoid shell commands with user input; use subprocess with argument lists (shell=False)",
    },
    # ── Open Redirect ──
    {
        "id": "OPEN-REDIRECT-001",
        "name": "Open Redirect",
        "severity": "MEDIUM",
        "description": "URL redirect parameter accepts user-controlled input",
        "patterns": [
            r'(?i)(?:redirect|next|return|goto|url)\s*=\s*request\.(?:GET|POST|args|form)\.get',
            r'(?i)redirect\(\s*(?:request\.(?:GET|POST|args|form)\.get|request\.url\.args)',
            r'(?i)(?:HttpResponseRedirect|redirect)\(\s*[^)]*\b(request\.)',
            r'(?i)(?:Location|redirect_uri)\s*[:=]\s*\$_(?:GET|POST|REQUEST)',
        ],
        "remediation": "Validate redirect targets against an allowlist; avoid open redirects",
    },
    # ── XXE ──
    {
        "id": "XXE-001",
        "name": "XML External Entity (XXE)",
        "severity": "HIGH",
        "description": "XML parser configured without disabling external entities",
        "patterns": [
            r'(?i)(?:xml\.dom|xml\.sax|xml\.etree|lxml)\.(?:parse|fromstring|iterparse)',
            r'(?i)from\s+xml\.(?:dom|sax|etree)\s+import',
            r'(?i)SAXParser\s*\(',
            r'(?i)DocumentBuilderFactory\.newInstance',
            r'(?i)javax\.xml\.parsers\.DocumentBuilder',
            r'(?i)XMLReader\s*=\s*xml\.parsers\.expat',
            r'(?i)(?:SimpleXMLElement|DOMDocument)\s*\(',
        ],
        "remediation": "Disable external entity processing: set resolve_entities=False, use defusedxml",
    },
    # ── Insecure Deserialization ──
    {
        "id": "DESER-001",
        "name": "Insecure Deserialization",
        "severity": "CRITICAL",
        "description": "Unsafe deserialization of untrusted data",
        "patterns": [
            r'(?i)pickle\.loads?\s*\(',
            r'(?i)yaml\.load\s*\(',
            r'(?i)Yaml\.load\s*\(',
            r'(?i)marshal\.loads?\s*\(',
            r'(?i)base64\.b64decode.*pickle',
        ],
        "remediation": "Avoid pickle/yaml.load on untrusted data; use safe alternatives (yaml.safe_load, JSON)",
    },
    # ── SSTI ──
    {
        "id": "SSTI-001",
        "name": "Server-Side Template Injection",
        "severity": "CRITICAL",
        "description": "Template rendered with user input without sanitization",
        "patterns": [
            r'(?i)render_template_string\(\s*f?["\'][^"\']*\{',
            r'(?i)Template\(\s*f?["\'][^"\']*\{',
            r'(?i)Jinja2?\.(?:from_string|compile)\(\s*f?["\'][^"\']*\{',
            r'(?i)nunjucks\.renderString\(\s*f?["\'][^"\']*\{',
        ],
        "remediation": "Never pass user input directly to template engines; use sandboxed rendering",
    },
    # ── Insecure Direct Object Reference ──
    {
        "id": "IDOR-001",
        "name": "Insecure Direct Object Reference",
        "severity": "MEDIUM",
        "description": "Object reference from user input without authorization check",
        "patterns": [
            r'(?i)(?:get_object_or_404|get_list_or_404)\(.*request',
            r'(?i)queryset\.get\(\s*(?:pk|id)\s*=',
            r'(?i)find_by_id\(\s*params\[',
            r'(?i)\.objects\.get\(.*request\.',
        ],
        "remediation": "Verify user authorization for every object access; use ownership checks",
    },
    # ── Weak Authentication ──
    {
        "id": "AUTH-001",
        "name": "Weak Authentication - Basic Auth",
        "severity": "MEDIUM",
        "description": "Use of HTTP Basic Authentication without HTTPS",
        "patterns": [
            r'(?i)requests?\.(?:get|post)\(.*auth\s*=?\s*\(\s*["\']',
            r'(?i)HTTPBasicAuth',
            r'(?i)httpx\.BasicAuth',
        ],
        "remediation": "Use token-based auth (JWT, OAuth2) over HTTPS instead of Basic Auth",
    },
    # ── Debug / Info Leak ──
    {
        "id": "DEBUG-001",
        "name": "Debug Mode Enabled",
        "severity": "MEDIUM",
        "description": "Debug or verbose mode left enabled in production",
        "patterns": [
            r'(?i)(?:DEBUG|VERBOSE|DEV_MODE)\s*=\s*(?:True|1|yes)',
            r'(?i)app\.run\(.*debug\s*=\s*True',
            r'(?i)setDebug\s*\(\s*True',
            r'(?i)werkzeug\.DebuggedApplication',
        ],
        "remediation": "Disable debug mode in production; set DEBUG=False and remove debug middleware",
    },
    # ── CORS Misconfiguration ──
    {
        "id": "CORS-001",
        "name": "CORS Misconfiguration - Wildcard Origin",
        "severity": "MEDIUM",
        "description": "CORS configured with wildcard origin allowing any domain",
        "patterns": [
            r'(?i)Access-Control-Allow-Origin\s*[:=]\s*["\']\*["\']',
            r'(?i)CORS\(.*origins?\s*=?\s*["\']?\*["\']?',
            r'(?i)allow_origins?\s*=\s*["\']\*["\']',
            r'(?i)cors\.allow_any_origin\s*\(\)',
        ],
        "remediation": "Restrict Access-Control-Allow-Origin to specific trusted origins",
    },
    # ── Hardcoded JWT Secret ──
    {
        "id": "HARDCODED-JWT-001",
        "name": "Hardcoded JWT Secret",
        "severity": "CRITICAL",
        "description": "JWT signing secret hardcoded in source code",
        "patterns": [
            r'(?i)(?:JWT_SECRET|jwt_secret|jwt_key|JWT_KEY)\s*[=:]\s*["\'][A-Za-z0-9_\-\.]{8,}["\']',
            r'(?i)(?:HS256|HS384|HS512).*["\'][A-Za-z0-9_\-\.]{8,}["\']',
            r'(?i)jwt\.encode\(.*["\'][A-Za-z0-9_\-\.]{8,}["\']',
        ],
        "remediation": "Store JWT secrets in environment variables or a secrets manager",
    },
    # ── Race Condition ──
    {
        "id": "RACE-001",
        "name": "Potential Race Condition (TOCTOU)",
        "severity": "MEDIUM",
        "description": "Time-of-check to time-of-use pattern detected",
        "patterns": [
            r'(?i)(?:os\.path\.exists|os\.path\.isfile|Path\.exists)\(.*\)\s*(?:and|or)\s*(?:open|os\.remove|Path\.unlink|Path\.rename)',
            r'(?i)if\s+(?:os\.path\.exists)',
        ],
        "remediation": "Use atomic file operations; open files directly and handle errors instead of checking first",
    },
    # ── Insecure Randomness ──
    {
        "id": "INSECURE-RNG-001",
        "name": "Insecure Random Number Generator",
        "severity": "LOW",
        "description": "Use of random module for security-sensitive operations",
        "patterns": [
            r'(?i)random\.(?:randint|choice|shuffle|sample|random)\(',
            r'(?i)Math\.random\(\)',
        ],
        "remediation": "Use secrets module (Python) or crypto.getRandomValues (JS) for security-sensitive randomness",
    },
    # ── LDAP Injection ──
    {
        "id": "LDAPI-001",
        "name": "LDAP Injection",
        "severity": "HIGH",
        "description": "LDAP query built from user input without sanitization",
        "patterns": [
            r'(?i)\.search\(.*["\'+].*\{',
            r'(?i)ldap\.(?:search|search_s|search_st)\(.*["\'+].*\{',
            r'(?i)(?:LDAPConnection|ldap_connect).*search.*\+',
        ],
        "remediation": "Escape LDAP search filters; use parameterized LDAP queries",
    },
    # ── Sensitive File Exposure ──
    {
        "id": "SENSITIVE-FILE-001",
        "name": "Sensitive File Exposure",
        "severity": "HIGH",
        "description": "Sensitive file served from web-accessible directory",
        "patterns": [
            r'(?i)\.env\b',
            r'(?i)credentials\.json',
            r'(?i)service_account\.json',
            r'(?i)config\.php',
            r'(?i)wp-config\.php',
        ],
        "remediation": "Move sensitive files outside the web root; add .htaccess or nginx deny rules",
    },
    # ── Prototype Pollution ──
    {
        "id": "PROTO-POLLUTION-001",
        "name": "Prototype Pollution",
        "severity": "HIGH",
        "description": "Object merge/assign operation vulnerable to prototype pollution",
        "patterns": [
            r'(?i)Object\.assign\(\s*\[\]',
            r'(?i)object\[__proto__\]',
            r'(?i)_.merge\(\s*\[\]',
            r'(?i).extend\(\s*true\s*,',
        ],
        "remediation": "Use Object.create(null) or Object.freeze for merge targets; validate object keys",
    },
]

FILE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs", ".rb",
    ".php", ".cs", ".kt", ".swift", ".scala", ".vue", ".svelte", ".c", ".cpp", ".h",
}

IGNORE_DIRS = {"node_modules", ".git", "__pycache__", "venv", ".venv", "dist", "build", ".tox", ".eggs", "vendor", ".terraform", ".serverless"}


def scan_file(filepath: Path, rules: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    if rules is None:
        rules = SAST_RULES

    findings: list[dict[str, Any]] = []
    try:
        content = filepath.read_text(encoding="utf-8", errors="replace")
    except (OSError, UnicodeDecodeError):
        return findings

    for rule in rules:
        for pattern in rule["patterns"]:
            for match in re.finditer(pattern, content):
                line_num = content[: match.start()].count("\n") + 1
                findings.append({
                    "rule_id": rule["id"],
                    "name": rule["name"],
                    "severity": rule["severity"],
                    "description": rule["description"],
                    "file": str(filepath),
                    "line": line_num,
                    "match": match.group()[:120],
                    "remediation": rule["remediation"],
                })
                break

    return findings


def run_sast_scan(path: str | Path = ".") -> dict[str, Any]:
    root = Path(path).resolve()
    all_findings: list[dict[str, Any]] = []

    for ext in FILE_EXTENSIONS:
        for filepath in root.rglob(f"*{ext}"):
            rel_parts = filepath.relative_to(root).parts
            if any(part in IGNORE_DIRS for part in rel_parts):
                continue
            findings = scan_file(filepath)
            all_findings.extend(findings)

    return {
        "tool": "sast",
        "rules_evaluated": len(SAST_RULES),
        "findings": all_findings,
        "summary": {
            "total": len(all_findings),
            "critical": sum(1 for f in all_findings if f["severity"] == "CRITICAL"),
            "high": sum(1 for f in all_findings if f["severity"] in ("CRITICAL", "HIGH")),
            "medium": sum(1 for f in all_findings if f["severity"] == "MEDIUM"),
            "low": sum(1 for f in all_findings if f["severity"] == "LOW"),
        },
    }
