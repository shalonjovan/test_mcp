import pytest

from testing_mcp.api.graphql import detect_graphql_endpoint, run_graphql_query


@pytest.mark.asyncio
async def test_graphql_query_invalid_url():
    result = await run_graphql_query("http://localhost:1/graphql", "{ __typename }", timeout=1.0)
    assert result["passed"] is False
    assert "error" in result


@pytest.mark.asyncio
async def test_detect_graphql_no_server():
    result = await detect_graphql_endpoint("http://localhost:1")
    assert result is None
