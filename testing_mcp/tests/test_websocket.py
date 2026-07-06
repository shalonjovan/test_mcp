import pytest

from testing_mcp.api.websocket_test import run_websocket_test


@pytest.mark.asyncio
async def test_websocket_invalid_url():
    result = await run_websocket_test("ws://localhost:1", timeout=1.0)
    assert result["passed"] is False
    assert "error" in result or not result["connected"]
