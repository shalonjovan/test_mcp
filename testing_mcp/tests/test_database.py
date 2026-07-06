from pathlib import Path

from testing_mcp.database.validation import (
    _extract_constraints,
    detect_database,
    find_migration_files,
    validate_migrations,
)


def test_detect_database():
    dbs = detect_database(Path.cwd())
    assert isinstance(dbs, dict)


def test_find_migrations():
    migs = find_migration_files(Path.cwd())
    assert isinstance(migs, list)


def test_validate_migrations_noop():
    result = validate_migrations(Path.cwd())
    assert "validation_passed" in result
    assert "migrations_found" in result


def test_extract_constraints():
    sql = """
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    user_id INTEGER REFERENCES accounts(id),
    age INTEGER CHECK (age > 0)
);
"""
    constraints = _extract_constraints(sql)
    types = [c["type"] for c in constraints]
    assert "PRIMARY KEY" in types
    assert "FOREIGN KEY" in types
    assert "UNIQUE + NOT NULL" in types
    assert "CHECK" in types
