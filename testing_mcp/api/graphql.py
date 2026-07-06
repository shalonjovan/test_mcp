from __future__ import annotations

import time
from typing import Any

import httpx


async def detect_graphql_endpoint(base_url: str) -> str | None:
    common_paths = ["/graphql", "/v1/graphql", "/api/graphql", "/gql", "/query"]
    async with httpx.AsyncClient(timeout=5.0) as client:
        for path in common_paths:
            try:
                resp = await client.post(
                    f"{base_url}{path}",
                    json={"query": "{ __typename }"},
                    headers={"Content-Type": "application/json"},
                )
                if resp.status_code == 200:
                    try:
                        data = resp.json()
                        if "data" in data or "errors" in data:
                            return path
                    except ValueError:
                        pass
            except httpx.HTTPError:
                continue
    return None


async def run_graphql_query(
    url: str,
    query: str,
    variables: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = 30.0,
) -> dict[str, Any]:
    start = time.time()
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(
                url,
                json={"query": query, "variables": variables or {}},
                headers={"Content-Type": "application/json", **(headers or {})},
            )
    except httpx.ConnectError:
        return {"error": f"Could not connect to {url}", "passed": False}
    except httpx.TimeoutException:
        return {"error": f"Request timed out", "passed": False}
    except Exception as e:
        return {"error": str(e), "passed": False}

    duration = round(time.time() - start, 3)
    passed = resp.status_code == 200

    try:
        body = resp.json()
    except ValueError:
        body = {"raw": resp.text[:1000]}

    if isinstance(body, dict):
        if "errors" in body:
            passed = False

    return {
        "passed": passed,
        "url": url,
        "duration": duration,
        "status_code": resp.status_code,
        "body": body,
    }


async def introspect_schema(url: str, timeout: float = 30.0) -> dict[str, Any]:
    introspection_query = """
    query IntrospectionQuery {
      __schema {
        queryType { name }
        mutationType { name }
        subscriptionType { name }
        types {
          name
          kind
          description
          fields {
            name
            type { name kind ofType { name kind } }
          }
        }
      }
    }
    """
    result = await run_graphql_query(url, introspection_query, timeout=timeout)
    if result.get("passed") and isinstance(result.get("body"), dict):
        schema = result["body"].get("data", {}).get("__schema", {})
        types = [t["name"] for t in schema.get("types", []) if not t["name"].startswith("__")]
        return {
            "passed": True,
            "has_queries": schema.get("queryType") is not None,
            "has_mutations": schema.get("mutationType") is not None,
            "has_subscriptions": schema.get("subscriptionType") is not None,
            "types_count": len(types),
            "types": types,
        }
    return {"passed": False, "error": "Schema introspection failed"}
