
from testing_mcp.server.stdio import run_stdio


def test_run_stdio_is_callable():
    assert callable(run_stdio)
