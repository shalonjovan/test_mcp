import tempfile
from pathlib import Path

from testing_mcp.security.dependency import (
    PARSERS,
    parse_requirements_txt,
    parse_package_json,
    parse_cargo_lock,
    resolve_purl,
)


def test_parsers_defined():
    assert "requirements.txt" in PARSERS
    assert "package-lock.json" in PARSERS
    assert "Cargo.lock" in PARSERS


def test_parse_requirements_txt():
    content = "flask==2.0.1\nrequests>=2.25.0\nnumpy>=1.19.0,<2.0.0\n# comment\n-e .\n"
    path = Path("/tmp/test_req.txt")
    path.write_text(content)
    deps = parse_requirements_txt(path)
    assert len(deps) >= 3
    names = {d["name"] for d in deps}
    assert "flask" in names
    assert "requests" in names
    assert "numpy" in names
    path.unlink()


def test_parse_package_json():
    content = '{"dependencies": {"express": "^4.17.1", "lodash": "~4.17.21"}, "devDependencies": {"mocha": "^9.0.0"}}'
    path = Path("/tmp/test_package.json")
    path.write_text(content)
    deps = parse_package_json(path)
    assert len(deps) == 3
    names = {d["name"] for d in deps}
    assert "express" in names
    assert "lodash" in names
    assert "mocha" in names
    path.unlink()


def test_parse_cargo_lock():
    content = '{"package": [{"name": "serde", "version": "1.0.130"}, {"name": "tokio", "version": "1.15.0"}]}'
    path = Path("/tmp/test_cargo.json")
    path.write_text(content)
    deps = parse_cargo_lock(path)
    assert len(deps) == 2
    names = {d["name"] for d in deps}
    assert "serde" in names
    assert "tokio" in names
    path.unlink()


def test_resolve_purl():
    purl = resolve_purl("flask", "2.0.1", "pypi")
    assert "pkg:pypi/flask@2.0.1" in purl

    purl = resolve_purl("express", "4.17.1", "npm")
    assert "pkg:npm/express@4.17.1" in purl
