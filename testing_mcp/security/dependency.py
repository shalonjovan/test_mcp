from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

OSV_API = "https://api.osv.dev/v1"


PURL_TEMPLATES: dict[str, str] = {
    "pypi": "pkg:pypi/{name}@{version}",
    "npm": "pkg:npm/{name}@{version}",
    "gem": "pkg:gem/{name}@{version}",
    "maven": "pkg:maven/{name}@{version}",
    "nuget": "pkg:nuget/{name}@{version}",
    "go": "pkg:golang/{name}@{version}",
    "cargo": "pkg:cargo/{name}@{version}",
    "packagist": "pkg:packagist/{name}@{version}",
}


def parse_requirements_txt(path: Path) -> list[dict[str, str]]:
    deps: list[dict[str, str]] = []
    pattern = re.compile(r"^([a-zA-Z0-9_.-]+)\s*(?:[><=!~]+)\s*([a-zA-Z0-9_.*+-]+)")
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        m = pattern.match(line)
        if m:
            deps.append({"name": m.group(1), "version": m.group(2), "ecosystem": "pypi"})
    return deps


def parse_pipfile_lock(path: Path) -> list[dict[str, str]]:
    deps: list[dict[str, str]] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return deps
    for section in ("default", "develop"):
        for pkg_name, pkg_info in data.get(section, {}).items():
            version = pkg_info.get("version", "").lstrip("=")
            if version:
                deps.append({"name": pkg_name, "version": version, "ecosystem": "pypi"})
    return deps


def parse_poetry_lock(path: Path) -> list[dict[str, str]]:
    deps: list[dict[str, str]] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return deps
    for pkg in data.get("package", []):
        name = pkg.get("name", "")
        version = pkg.get("version", "")
        if name and version:
            deps.append({"name": name, "version": version, "ecosystem": "pypi"})
    return deps


def parse_package_json(path: Path) -> list[dict[str, str]]:
    deps: list[dict[str, str]] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return deps
    for deptype in ("dependencies", "devDependencies"):
        for name, version in data.get(deptype, {}).items():
            ver = version.lstrip("^~>=<!")
            if ver:
                deps.append({"name": name, "version": ver, "ecosystem": "npm"})
    return deps


def parse_cargo_lock(path: Path) -> list[dict[str, str]]:
    deps: list[dict[str, str]] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return deps
    for pkg in data.get("package", []):
        name = pkg.get("name", "")
        version = pkg.get("version", "")
        if name and version:
            deps.append({"name": name, "version": version, "ecosystem": "cargo"})
    return deps


def parse_gemfile_lock(path: Path) -> list[dict[str, str]]:
    deps: list[dict[str, str]] = []
    pattern = re.compile(r"^\s{4}(\S+)\s+\(([^)]+)\)")
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        m = pattern.match(line)
        if m:
            deps.append({"name": m.group(1), "version": m.group(2), "ecosystem": "gem"})
    return deps


def parse_go_sum(path: Path) -> list[dict[str, str]]:
    deps: list[dict[str, str]] = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        parts = line.strip().split()
        if len(parts) >= 2 and "/" in parts[0]:
            name = parts[0]
            version = parts[1].strip()
            deps.append({"name": name, "version": version, "ecosystem": "go"})
    return deps


PARSERS: dict[str, tuple[str, Any]] = {
    "requirements.txt": ("pypi", parse_requirements_txt),
    "Pipfile.lock": ("pypi", parse_pipfile_lock),
    "poetry.lock": ("pypi", parse_poetry_lock),
    "package-lock.json": ("npm", parse_package_json),
    "yarn.lock": ("npm", None),
    "pnpm-lock.yaml": ("npm", None),
    "Cargo.lock": ("cargo", parse_cargo_lock),
    "Gemfile.lock": ("gem", parse_gemfile_lock),
    "go.sum": ("go", parse_go_sum),
    "composer.lock": ("packagist", None),
    "packages.lock.json": ("nuget", None),
}


def resolve_purl(name: str, version: str, ecosystem: str) -> str:
    tmpl = PURL_TEMPLATES.get(ecosystem)
    if not tmpl:
        return f"pkg:{ecosystem}/{name}@{version}"
    return tmpl.format(name=name, version=version)


def query_osv(purl: str) -> dict[str, Any] | None:
    if not HAS_HTTPX:
        return {"error": "httpx required for OSV queries"}

    try:
        with httpx.Client(timeout=15) as client:
            resp = client.post(
                f"{OSV_API}/query",
                json={"package": {"purl": purl}},
            )
            if resp.status_code == 200:
                data = resp.json()
                return data if data.get("vulns") else None
            return None
    except (httpx.TimeoutException, httpx.RequestError):
        return None


def scan_dependencies(path: str | Path = ".") -> dict[str, Any]:
    root = Path(path).resolve()
    deps_found: list[dict[str, str]] = []
    results: dict[str, Any] = {
        "tool": "dependency-scanner",
        "scanned_files": [],
        "dependencies": [],
        "vulnerabilities": [],
        "summary": {"total_packages": 0, "vulnerable": 0, "critical": 0, "high": 0, "medium": 0, "low": 0},
    }

    for filename, (ecosystem, parser) in PARSERS.items():
        filepath = root / filename
        if filepath.is_file():
            results["scanned_files"].append(filename)
            if parser:
                deps = parser(filepath)
                for dep in deps:
                    if dep not in deps_found:
                        deps_found.append(dep)

    results["dependencies"] = deps_found
    results["summary"]["total_packages"] = len(deps_found)

    for dep in deps_found:
        purl = resolve_purl(dep["name"], dep["version"], dep["ecosystem"])
        vuln_data = query_osv(purl)
        if vuln_data and vuln_data.get("vulns"):
            for vuln in vuln_data["vulns"]:
                severity = _classify_severity(vuln)
                results["vulnerabilities"].append({
                    "id": vuln.get("id", "UNKNOWN"),
                    "package": dep["name"],
                    "version": dep["version"],
                    "ecosystem": dep["ecosystem"],
                    "severity": severity,
                    "summary": vuln.get("summary", ""),
                    "aliases": vuln.get("aliases", []),
                    "fixed_version": _find_fixed(vuln),
                    "url": f"https://osv.dev/vulnerability/{vuln.get('id', '')}",
                })
                results["summary"]["vulnerable"] += 1
                results["summary"][severity.lower()] = results["summary"].get(severity.lower(), 0) + 1

    return results


def _find_fixed(vuln: dict[str, Any]) -> str | None:
    for affected in vuln.get("affected", []):
        for rng in affected.get("ranges", []):
            for event in rng.get("events", []):
                if "fixed" in event:
                    return event["fixed"]
    return None


def _classify_severity(vuln: dict[str, Any]) -> str:
    for severity in vuln.get("severity", []):
        val = severity.get("score", "")
        if isinstance(val, str) and val:
            try:
                score = float(val)
                if score >= 9.0:
                    return "CRITICAL"
                elif score >= 7.0:
                    return "HIGH"
                elif score >= 4.0:
                    return "MEDIUM"
                else:
                    return "LOW"
            except ValueError:
                pass
    return "UNKNOWN"
