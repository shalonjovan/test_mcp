
from pathlib import Path

import pytest

from testing_mcp.exceptions import ToolError, ValidationError
from testing_mcp.server.tools import _resolve_path, _resolve_url, validate_command
from testing_mcp.utils.response import ToolResponse, failure
from testing_mcp.utils.validators import validate_project_path, validate_url


def test_validate_project_path_resolves():
    resolved = validate_project_path(".")
    assert resolved.is_absolute()
    assert resolved == Path.cwd()


def test_validate_project_path_rejects_absolute_traversal():
    with pytest.raises(ValidationError):
        validate_project_path("/etc/passwd")


def test_validate_url_rejects_private_ip():
    with pytest.raises(ValidationError):
        validate_url("http://127.0.0.1:8080/test")


def test_validate_url_rejects_private_ip_10():
    with pytest.raises(ValidationError):
        validate_url("http://10.0.0.1/secret")


def test_validate_url_allows_public():
    result = validate_url("http://example.com/api")
    assert result == "http://example.com/api"


def test_validate_url_rejects_non_http():
    with pytest.raises(ValidationError):
        validate_url("file:///etc/passwd")


def test_validate_command_rejects_shell_meta():
    with pytest.raises(ValidationError):
        validate_command("echo hello; rm -rf /")


def test_validate_command_rejects_pipe():
    with pytest.raises(ValidationError):
        validate_command("ls | grep foo")


def test_validate_command_allows_simple():
    result = validate_command("python -m pytest tests/")
    assert result == ["python", "-m", "pytest", "tests/"]


def test_validate_command_rejects_subshell():
    with pytest.raises(ValidationError):
        validate_command("$(cat /etc/passwd)")


def test_validate_command_rejects_backtick():
    with pytest.raises(ValidationError):
        validate_command("echo `whoami`")


def test_validate_command_rejects_redirect():
    with pytest.raises(ValidationError):
        validate_command("ls > /tmp/out")


def test_tool_response_success():
    resp = ToolResponse(success=True, data={"key": "val"})
    assert resp.success is True
    assert resp.data["key"] == "val"


def test_tool_response_error():
    err = ToolError("something broke", code="SOMETHING_BROKE")
    resp = failure(err)
    assert resp.success is False
    assert resp.error is not None
    assert resp.error.code == "SOMETHING_BROKE"
    assert resp.error.message == "something broke"


def test_resolve_path_uses_validator():
    p = _resolve_path(".")
    assert p == Path.cwd()


def test_resolve_url_uses_validator():
    u = _resolve_url("http://example.com/")
    assert u == "http://example.com/"
