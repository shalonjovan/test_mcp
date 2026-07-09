from __future__ import annotations

from fastmcp import FastMCP

from testing_mcp.database.validation import detect_database, test_rollback, validate_constraints, validate_migrations
from testing_mcp.fix.migrations import extract_schema_migrations
from testing_mcp.server.tools._helpers import _resolve_path


def register_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    def database_validate(
        path: str = ".",
        check_type: str = "all",
    ) -> dict:
        """Validate database migrations, constraints, and rollbacks."""
        root = _resolve_path(path)
        db_types = detect_database(root)
        db_type = max(db_types, key=db_types.get) if db_types else "sqlite"

        result: dict = {"database_type": db_type, "detected_databases": db_types}

        if check_type in ("all", "migrations"):
            result["migrations"] = validate_migrations(root, db_type=db_type)

        if check_type in ("all", "constraints"):
            result["constraints"] = validate_constraints(root, db_type=db_type)

        if check_type in ("all", "rollback"):
            result["rollback"] = test_rollback(root)

        return result

    @mcp.tool()
    def extract_migration(
        path: str = ".",
        db_type: str = "sqlite",
        output_dir: str = "",
    ) -> dict:
        """Extract inline SQL schemas from source code into migration files."""
        return extract_schema_migrations(path=path, db_type=db_type, output_dir=output_dir)
