
from fastmcp import FastMCP

from testing_mcp.server.app import create_app
from testing_mcp.utils.config import Settings


def test_create_app_returns_fastmcp():
    app = create_app(Settings())
    assert isinstance(app, FastMCP)


def test_create_app_sets_name():
    app = create_app(Settings())
    assert app.name == "Testing MCP"
