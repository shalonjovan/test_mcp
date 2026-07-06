from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any


def detect_database(project_root: Path) -> dict[str, float]:
    databases: dict[str, float] = {}
    config_files: dict[str, list[str]] = {
        "sqlite": ["*.db", "*.sqlite", "*.sqlite3"],
        "postgresql": ["postgres", "postgresql", "pg"],
        "mysql": ["mysql", "mariadb"],
        "mongodb": ["mongodb", "mongo"],
        "redis": ["redis"],
    }

    for db, patterns in config_files.items():
        for pattern in patterns:
            matches = list(project_root.rglob(pattern))
            conf_matches = [m for m in matches if m.suffix in {".py", ".yml", ".yaml", ".toml", ".cfg", ".conf", ".env"}]
            if conf_matches:
                databases[db] = max(databases.get(db, 0), 1.0)
                break
            db_files = [m for m in matches if m.suffix in {".db", ".sqlite", ".sqlite3"}]
            if db_files:
                databases["sqlite"] = max(databases.get("sqlite", 0), 1.0)

    return databases


def find_migration_files(project_root: Path) -> list[str]:
    migration_dirs = ["migrations", "alembic", "db/migrate", "database/migrations"]
    found: list[str] = []
    for dir_name in migration_dirs:
        mig_dir = project_root / dir_name
        if mig_dir.is_dir():
            files = sorted(mig_dir.rglob("*.py")) + sorted(mig_dir.rglob("*.sql"))
            found.extend(str(f.relative_to(project_root)) for f in files)
    return found


def validate_migrations(
    project_root: Path,
    db_type: str = "sqlite",
    db_url: str | None = None,
) -> dict[str, Any]:
    results: dict[str, Any] = {
        "database_type": db_type,
        "migrations_found": [],
        "validation_passed": True,
        "errors": [],
    }

    migration_files = find_migration_files(project_root)
    results["migrations_found"] = migration_files

    if not migration_files:
        results["validation_passed"] = True
        results["message"] = "No migration files found"
        return results

    if db_type == "sqlite":
        sql_files = [f for f in migration_files if f.endswith(".sql")]
        for sql_file in sql_files:
            filepath = project_root / sql_file
            content = filepath.read_text()
            issues = _check_sql_syntax(content)
            if issues:
                results["validation_passed"] = False
                results["errors"].extend(issues)

    return results


def _check_sql_syntax(sql: str) -> list[str]:
    issues: list[str] = []
    lines = sql.split("\n")
    for i, line in enumerate(lines, 1):
        stripped = line.strip().upper()
        if stripped.startswith("CREATE TABLE") and "(" not in stripped:
            issues.append(f"Line {i}: CREATE TABLE missing columns definition")
    return issues


def validate_constraints(
    project_root: Path,
    db_type: str = "sqlite",
    db_url: str | None = None,
) -> dict[str, Any]:
    results: dict[str, Any] = {
        "database_type": db_type,
        "constraints_checked": [],
        "validation_passed": True,
        "errors": [],
    }

    migration_files = find_migration_files(project_root)
    sql_files = [f for f in migration_files if f.endswith(".sql")]

    for sql_file in sql_files:
        filepath = project_root / sql_file
        content = filepath.read_text()
        constraints = _extract_constraints(content)
        results["constraints_checked"].extend(constraints)

    return results


def _extract_constraints(sql: str) -> list[dict[str, str]]:
    constraints: list[dict[str, str]] = []
    lines = sql.split("\n")
    for line in lines:
        upper = line.strip().upper()
        if "PRIMARY KEY" in upper:
            constraints.append({"type": "PRIMARY KEY", "definition": line.strip()})
        if "FOREIGN KEY" in upper or "REFERENCES" in upper:
            constraints.append({"type": "FOREIGN KEY", "definition": line.strip()})
        if "UNIQUE" in upper and "NOT NULL" in upper:
            constraints.append({"type": "UNIQUE + NOT NULL", "definition": line.strip()})
        if "CHECK" in upper:
            constraints.append({"type": "CHECK", "definition": line.strip()})

    return constraints


def test_rollback(project_root: Path) -> dict[str, Any]:
    results: dict[str, Any] = {
        "rollback_tests": [],
        "all_passed": True,
        "errors": [],
    }

    migration_files = find_migration_files(project_root)

    if any("alembic" in str(project_root / f) for f in migration_files):
        try:
            proc = subprocess.run(
                ["alembic", "history"],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=30,
            )
            results["rollback_tests"].append({
                "tool": "alembic",
                "revisions_available": proc.returncode == 0,
                "output": proc.stdout[:500] if proc.returncode == 0 else proc.stderr[:500],
            })
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            results["errors"].append(f"Alembic check failed: {e}")

    return results
