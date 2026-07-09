from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any


def extract_schema_migrations(
    path: str = ".",
    db_type: str = "sqlite",
    output_dir: str = "",
) -> dict[str, Any]:
    root = Path(path).resolve()
    migrations_dir = Path(output_dir).resolve() if output_dir else root / "migrations"
    migrations_dir.mkdir(parents=True, exist_ok=True)

    sql_patterns: list[re.Pattern] = [
        re.compile(r'(CREATE\s+TABLE|CREATE\s+INDEX|CREATE\s+TRIGGER|CREATE\s+VIEW)\s', re.IGNORECASE),
    ]

    found_schemas: list[dict[str, Any]] = []

    for py_file in sorted(root.rglob("*.py")):
        if ".venv" in str(py_file) or "__pycache__" in str(py_file):
            continue
        try:
            content = py_file.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        for pattern in sql_patterns:
            for match in pattern.finditer(content):
                start = max(0, match.start() - 5)
                snippet = content[start:match.end() + 200]
                found_schemas.append({
                    "file": str(py_file.relative_to(root)),
                    "type": match.group(1).split()[1] if len(match.group(1).split()) > 1 else "SQL",
                    "snippet": snippet[:200],
                })

    if not found_schemas:
        return {
            "migrations_dir": str(migrations_dir),
            "migrations_created": [],
            "schemas_found": [],
            "count": 0,
            "message": "No inline SQL schemas found",
        }

    existing = sorted(migrations_dir.glob("[0-9]*.sql"))
    next_num = 1
    if existing:
        last = existing[-1].stem.split("_")[0]
        try:
            next_num = int(last) + 1
        except ValueError:
            next_num = len(existing) + 1

    created: list[str] = []
    for i, schema in enumerate(found_schemas):
        filename = f"{next_num + i:04d}_extracted_{schema['type'].lower()}.sql"
        filepath = migrations_dir / filename

        stmt = schema["snippet"].split(";")[0] + ";" if ";" in schema["snippet"] else schema["snippet"]
        comment = f"-- Extracted from {schema['file']}\n-- Generated at {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        filepath.write_text(comment + stmt + "\n")
        created.append(str(filepath.relative_to(root)))

    return {
        "migrations_dir": str(migrations_dir),
        "migrations_created": created,
        "schemas_found": [
            {"file": s["file"], "type": s["type"]} for s in found_schemas
        ],
        "count": len(created),
    }
