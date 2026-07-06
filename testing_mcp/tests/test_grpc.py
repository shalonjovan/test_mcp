import pytest

from testing_mcp.api.grpc_test import run_grpc_test


@pytest.mark.asyncio
async def test_grpc_missing_params():
    result = await run_grpc_test("http://localhost:1", service="", method="")
    assert result["passed"] is False
    assert "error" in result


@pytest.mark.asyncio
async def test_grpc_invalid_url():
    result = await run_grpc_test("http://localhost:1", service="svc", method="method", timeout=1.0)
    assert result["passed"] is False
