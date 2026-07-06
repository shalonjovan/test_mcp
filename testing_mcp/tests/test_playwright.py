import pytest

from testing_mcp.ui.playwright import run_ui_test


@pytest.mark.asyncio
async def test_ui_test_basic():
    result = await run_ui_test(url="https://example.com", screenshot=False, timeout=15000)
    assert result["passed"] is True
    assert result["duration"] > 0


@pytest.mark.asyncio
async def test_ui_test_with_screenshot():
    result = await run_ui_test(url="https://example.com", screenshot=True, timeout=15000)
    assert result["passed"] is True
    assert len(result["screenshots"]) > 0
    assert isinstance(result["screenshots"][0], str)


@pytest.mark.asyncio
async def test_ui_test_invalid_url():
    result = await run_ui_test(url="https://nonexistent.invalid", screenshot=False, timeout=5000)
    assert result["passed"] is False
    assert "error" in result
