from __future__ import annotations

import json
from datetime import datetime
from typing import Any


def generate_markdown_report(results: list[dict], title: str = "Test Report") -> str:
    lines: list[str] = [
        f"# {title}",
        "",
        f"**Generated:** {datetime.now().isoformat()}",
        "",
        "## Summary",
        "",
    ]

    total = len(results)
    passed = sum(1 for r in results if r.get("passed"))
    failed = total - passed

    lines.append(f"- **Total:** {total}")
    lines.append(f"- **Passed:** {passed}")
    lines.append(f"- **Failed:** {failed}")
    lines.append("")

    if results:
        lines.append("## Results")
        lines.append("")
        lines.append("| Test | Status | Duration | Message |")
        lines.append("|------|--------|----------|---------|")
        for r in results:
            status = "✅ PASS" if r.get("passed") else "❌ FAIL"
            name = r.get("name", "unknown")
            duration = f"{r.get('duration', 0)}s"
            message = (r.get("message", "") or "")[:80]
            lines.append(f"| {name} | {status} | {duration} | {message} |")

        lines.append("")

        failed_results = [r for r in results if not r.get("passed")]
        if failed_results:
            lines.append("## Failures")
            lines.append("")
            for r in failed_results:
                lines.append(f"### {r.get('name', 'unknown')}")
                lines.append("")
                if r.get("stdout"):
                    lines.append("```")
                    lines.append(r["stdout"])
                    lines.append("```")
                if r.get("stderr"):
                    lines.append("```")
                    lines.append(r["stderr"])
                    lines.append("```")
                lines.append("")

    return "\n".join(lines)


def generate_html_report(results: list[dict], title: str = "Test Report") -> str:
    total = len(results)
    passed = sum(1 for r in results if r.get("passed"))
    failed = total - passed
    pass_pct = round((passed / total * 100) if total else 0, 1)

    rows = ""
    for r in results:
        status = "pass" if r.get("passed") else "fail"
        name = r.get("name", "unknown")
        duration = r.get("duration", 0)
        message = (r.get("message", "") or "")
        rows += f"<tr class='{status}'><td>{name}</td><td>{status.upper()}</td><td>{duration}s</td><td>{message}</td></tr>\n"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{title}</title>
<style>
body {{ font-family: sans-serif; margin: 2rem; }}
.pass {{ background: #d4edda; }}
.fail {{ background: #f8d7da; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border: 1px solid #ccc; padding: 0.5rem; text-align: left; }}
.summary {{ font-size: 1.2rem; margin: 1rem 0; }}
</style>
</head>
<body>
<h1>{title}</h1>
<p>Generated: {datetime.now().isoformat()}</p>
<div class="summary">
  <strong>Total:</strong> {total} |
  <strong>Passed:</strong> {passed} |
  <strong>Failed:</strong> {failed} |
  <strong>Pass Rate:</strong> {pass_pct}%
</div>
<h2>Results</h2>
<table>
<thead><tr><th>Test</th><th>Status</th><th>Duration</th><th>Message</th></tr></thead>
<tbody>
{rows}
</tbody>
</table>
</body>
</html>"""


def generate_json_report(results: list[dict], title: str = "Test Report") -> str:
    total = len(results)
    passed = sum(1 for r in results if r.get("passed"))

    report = {
        "title": title,
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "total": total,
            "passed": passed,
            "failed": total - passed,
        },
        "results": results,
    }
    return json.dumps(report, indent=2)
