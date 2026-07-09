from __future__ import annotations

import asyncio

from fastmcp import FastMCP

from testing_mcp.api.graphql import detect_graphql_endpoint, introspect_schema, run_graphql_query
from testing_mcp.api.grpc_test import run_grpc_test as run_grpc
from testing_mcp.api.testing import discover_api_endpoints, run_api_test_sync
from testing_mcp.api.websocket_test import run_websocket_test as run_ws
from testing_mcp.server.tools._helpers import _resolve_url


def register_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    def api_test(
        base_url: str,
        method: str = "GET",
        path: str = "/",
        headers: dict[str, str] | None = None,
        body: dict | None = None,
        expected_status: int = 200,
        expected_schema: dict | None = None,
        timeout: float = 30.0,
    ) -> dict:
        """Test an API endpoint with request/response validation."""
        _resolve_url(base_url)
        return run_api_test_sync(
            base_url=base_url,
            method=method,
            path=path,
            headers=headers,
            body=body,
            expected_status=expected_status,
            expected_schema=expected_schema,
            timeout=timeout,
        )

    @mcp.tool()
    def discover_endpoints(
        base_url: str,
        paths: list[str] | None = None,
    ) -> list[dict]:
        """Discover API endpoints from a base URL."""
        return asyncio.run(discover_api_endpoints(base_url, paths))

    @mcp.tool()
    def graphql_test(
        url: str,
        query: str,
        variables: dict | None = None,
        timeout: float = 30.0,
    ) -> dict:
        """Run a GraphQL query against an endpoint."""
        return asyncio.run(run_graphql_query(url, query, variables=variables, timeout=timeout))

    @mcp.tool()
    def graphql_introspect(url: str) -> dict:
        """Introspect a GraphQL schema."""
        return asyncio.run(introspect_schema(url))

    @mcp.tool()
    def graphql_detect(base_url: str) -> dict:
        """Detect a GraphQL endpoint at common paths."""
        path = asyncio.run(detect_graphql_endpoint(base_url))
        return {"found": path is not None, "endpoint": f"{base_url}{path}" if path else None}

    @mcp.tool()
    def websocket_test(
        url: str,
        message: str = "",
        timeout: float = 10.0,
    ) -> dict:
        """Test a WebSocket connection."""
        _resolve_url(url)
        return asyncio.run(run_ws(url, message=message or None, timeout=timeout))

    @mcp.tool()
    def grpc_test(
        url: str,
        service: str,
        method: str,
        request_body: str = "",
        timeout: float = 30.0,
    ) -> dict:
        """Test a gRPC endpoint."""
        _resolve_url(url)
        return asyncio.run(run_grpc(url, service=service, method=method, request_body=request_body, timeout=timeout))
