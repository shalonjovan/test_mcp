from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "UNKNOWN": 4}


def _time() -> str:
    return datetime.now(timezone.utc).isoformat()


def _deduplicate(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple] = set()
    deduped: list[dict[str, Any]] = []
    for f in findings:
        key = (f.get("rule_id", "?"), f.get("file", "?"), f.get("line", 0), f.get("name", ""))
        if key not in seen:
            seen.add(key)
            deduped.append(f)
    return deduped


def _severity_score(severity: str) -> int:
    return SEVERITY_ORDER.get(severity.upper(), 99)


def build_report(
    *,
    target: str = ".",
    sast_result: dict[str, Any] | None = None,
    secret_result: dict[str, Any] | None = None,
    dependency_result: dict[str, Any] | None = None,
    config_result: dict[str, Any] | None = None,
    dast_result: dict[str, Any] | None = None,
    crawler_result: dict[str, Any] | None = None,
    header_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    all_findings: list[dict[str, Any]] = []
    module_summaries: dict[str, Any] = {}
    module_stats: dict[str, dict[str, int]] = {}
    overall_stats: dict[str, int] = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}

    modules = {
        "sast": sast_result,
        "secret-scanner": secret_result,
        "dependency-scanner": dependency_result,
        "config-scanner": config_result,
        "dast": dast_result,
        "web-crawler": crawler_result,
    }

    for mod_name, result in modules.items():
        if not result:
            continue

        if "error" in result:
            module_summaries[mod_name] = {"error": result["error"]}
            continue

        module_result = {}

        if mod_name == "sast":
            findings = result.get("findings", [])
            for f in findings:
                f["tool"] = "sast"
            summary = result.get("summary", {})
            module_result = {
                "scanned_files": result.get("scanned_files", 0),
                "total_findings": len(findings),
                "by_severity": {
                    "critical": summary.get("critical", 0),
                    "high": summary.get("high", 0),
                    "medium": summary.get("medium", 0),
                    "low": summary.get("low", 0),
                },
            }
        elif mod_name == "secret-scanner":
            findings = result.get("findings", [])
            for f in findings:
                f["tool"] = "secret-scanner"
            module_result = {
                "scanned_files": result.get("scanned_files", 0),
                "total_findings": result.get("total_findings", len(findings)),
                "by_severity": {
                    "critical": result.get("critical_count", 0),
                    "high": result.get("high_count", 0),
                    "medium": result.get("medium_count", 0),
                },
            }
        elif mod_name == "dependency-scanner":
            findings = result.get("vulnerabilities", [])
            for f in findings:
                f["tool"] = "dependency-scanner"
            summary = result.get("summary", {})
            module_result = {
                "total_packages": summary.get("total_packages", 0),
                "vulnerable_packages": summary.get("vulnerable", 0),
                "by_severity": {
                    "critical": summary.get("critical", 0),
                    "high": summary.get("high", 0),
                    "medium": summary.get("medium", 0),
                    "low": summary.get("low", 0),
                },
            }
        elif mod_name == "config-scanner":
            findings = result.get("findings", [])
            for f in findings:
                f["tool"] = "config-scanner"
            summary = result.get("summary", {})
            module_result = {
                "scanned_files": len(result.get("scanned_files", [])),
                "total_findings": summary.get("total", len(findings)),
                "by_severity": {
                    "critical": summary.get("critical", 0),
                    "high": summary.get("high", 0),
                    "medium": summary.get("medium", 0),
                    "low": summary.get("low", 0),
                },
            }
        elif mod_name == "dast":
            findings = result.get("findings", [])
            for f in findings:
                f["tool"] = "dast"
            module_result = {
                "base_url": result.get("base_url", ""),
                "technologies": result.get("technologies", []),
                "endpoints_checked": len(result.get("endpoints", [])),
                "total_findings": len(findings),
            }
            sqli = result.get("sqli_test")
            xss = result.get("xss_test")
            if sqli:
                module_result["sqli_test"] = sqli.get("vulnerable", False)
            if xss:
                module_result["xss_test"] = xss.get("vulnerable", False)
        elif mod_name == "web-crawler":
            findings = result.get("findings", [])
            for f in findings:
                f["tool"] = "web-crawler"
            module_result = {
                "base_url": result.get("base_url", ""),
                "pages_visited": result.get("pages_visited", 0),
                "endpoints_discovered": len(result.get("endpoints_discovered", [])),
                "total_findings": len(findings),
            }

        if "error" in result:
            module_result["error"] = result["error"]

        module_summaries[mod_name] = module_result

        # Count stats
        sev_map = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for f in findings:
            s = f.get("severity", "INFO").upper()
            if s in sev_map:
                sev_map[s] += 1
                overall_stats[s] += 1
            else:
                overall_stats["INFO"] += 1
        module_stats[mod_name] = sev_map

        all_findings.extend(findings)

    # Header results (special case)
    if header_result:
        hdr_findings = header_result.get("findings", [])
        for f in hdr_findings:
            f["tool"] = "header-scan"
        module_summaries["header-scan"] = {
            "url": header_result.get("url", ""),
            "status": header_result.get("status", ""),
            "checks_passed": header_result.get("checks_passed", 0),
            "total_checks": header_result.get("total_checks", 0),
            "missing_headers": list(header_result.get("missing", [])),
            "total_findings": len(hdr_findings),
        }
        for f in hdr_findings:
            s = f.get("severity", "INFO").upper()
            if s in overall_stats:
                overall_stats[s] += 1
            else:
                overall_stats["INFO"] += 1
        all_findings.extend(hdr_findings)

    deduped = _deduplicate(all_findings)
    deduped.sort(key=lambda x: _severity_score(x.get("severity", "UNKNOWN")))

    overall_stats = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
    for f in deduped:
        s = f.get("severity", "INFO").upper()
        if s in overall_stats:
            overall_stats[s] += 1
        else:
            overall_stats["INFO"] += 1

    total = sum(overall_stats.values())

    return {
        "report": {
            "generated_at": _time(),
            "target": target,
            "modules_ran": [k for k, v in modules.items() if v and "error" not in v] + (["header-scan"] if header_result else []),
            "modules_with_errors": [k for k, v in modules.items() if v and "error" in v],
        },
        "summary": {
            "total_findings": total,
            "by_severity": overall_stats,
            "risk_score": _calculate_risk(overall_stats),
        },
        "modules": module_summaries,
        "findings": deduped,
    }


def _calculate_risk(stats: dict[str, int]) -> str:
    score = stats.get("CRITICAL", 0) * 10 + stats.get("HIGH", 0) * 5 + stats.get("MEDIUM", 0) * 2 + stats.get("LOW", 0) * 0.5
    if score >= 50:
        return "CRITICAL"
    elif score >= 20:
        return "HIGH"
    elif score >= 5:
        return "MEDIUM"
    elif score > 0:
        return "LOW"
    return "NONE"


def report_to_text(report: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("=" * 70)
    lines.append("SECURITY SCAN REPORT")
    lines.append("=" * 70)
    r = report.get("report", {})
    lines.append(f"Target:       {r.get('target', 'N/A')}")
    lines.append(f"Generated:    {r.get('generated_at', 'N/A')}")
    lines.append(f"Modules Run:  {', '.join(r.get('modules_ran', []))}")
    if r.get("modules_with_errors"):
        lines.append(f"Errors:       {', '.join(r['modules_with_errors'])}")
    lines.append("")

    summary = report.get("summary", {})
    lines.append("-" * 70)
    lines.append("SUMMARY")
    lines.append("-" * 70)
    lines.append(f"Total Findings: {summary.get('total_findings', 0)}")
    lines.append(f"Risk Score:     {summary.get('risk_score', 'NONE')}")
    for sev, count in summary.get("by_severity", {}).items():
        if count:
            lines.append(f"  {sev.capitalize():10s}: {count}")
    lines.append("")

    modules = report.get("modules", {})
    if modules:
        lines.append("-" * 70)
        lines.append("MODULE RESULTS")
        lines.append("-" * 70)
        for mod_name, mod_result in modules.items():
            if "error" in mod_result:
                lines.append(f"  {mod_name}: ERROR - {mod_result['error']}")
                continue
            lines.append(f"\n  [{mod_name.upper()}]")
            for key, val in mod_result.items():
                if key == "by_severity":
                    parts = [f"{sev}: {cnt}" for sev, cnt in val.items() if cnt]
                    if parts:
                        lines.append(f"    Severity: {', '.join(parts)}")
                elif key not in ("total_findings", "error"):
                    lines.append(f"    {key.replace('_', ' ').title()}: {val}")
            if mod_result.get("total_findings", 0) > 0:
                lines.append(f"    Findings: {mod_result['total_findings']}")

    findings = report.get("findings", [])
    if findings:
        lines.append("")
        lines.append("-" * 70)
        lines.append("FINDINGS (sorted by severity)")
        lines.append("-" * 70)

        limit = min(len(findings), 100)
        for i, f in enumerate(findings[:limit], 1):
            severity = f.get("severity", "INFO")
            sev_tag = f"[{severity}]"
            lines.append(f"\n  {i:3d}. {sev_tag} {f.get('name', 'Unknown Issue')}")
            lines.append(f"       File: {f.get('file', 'N/A')}:{f.get('line', '?')}")
            if f.get("match"):
                lines.append(f"       Match: {f['match']}")
            if f.get("remediation"):
                lines.append(f"       Fix:   {f['remediation']}")
            if f.get("url"):
                lines.append(f"       URL:   {f['url']}")
            if f.get("detail"):
                lines.append(f"       Detail: {f['detail']}")

        if len(findings) > limit:
            lines.append(f"\n  ... and {len(findings) - limit} more findings")

    lines.append("")
    lines.append("=" * 70)
    lines.append("END OF REPORT")
    lines.append("=" * 70)

    return "\n".join(lines)


def report_to_json(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, default=str)
