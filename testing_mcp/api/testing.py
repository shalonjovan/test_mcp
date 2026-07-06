from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import httpx


def _discover_openapi_spec(project_root: Path) -> Path | None:
    for pattern in ["**/openapi.*", "**/swagger.*", "**/api-docs.*"]:
        matches = list(project_root.glob(pattern))
        if matches:
            return matches[0]
    return None


def _load_openapi_spec(spec_path: Path) -> dict[str, Any] | None:
    try:
        content = spec_path.read_text()
        return json.loads(content)
    except (json.JSONDecodeError, OSError):
        return None


def _extract_endpoints_from_openapi(spec: dict[str, Any]) -> list[dict[str, Any]]:
    endpoints: list[dict[str, Any]] = []
    paths = spec.get("paths", {})
    for path, methods in paths.items():
        for method in ("get", "post", "put", "delete", "patch"):
            if method in methods:
                endpoints.append({
                    "path": path,
                    "method": method.upper(),
                    "summary": methods[method].get("summary", ""),
                    "parameters": methods[method].get("parameters", []),
                    "request_body": methods[method].get("requestBody", {}),
                })
    return endpoints


async def discover_api_endpoints(base_url: str, paths: list[str] | None = None) -> list[dict[str, Any]]:
    discovered: list[dict[str, Any]] = []

    if paths:
        for p in paths:
            discovered.append({"path": p, "method": "GET", "source": "user"})
        return discovered

    common_paths = [
        "/api", "/api/v1", "/api/v2", "/health", "/healthz",
        "/swagger.json", "/openapi.json", "/api-docs",
    ]

    async with httpx.AsyncClient(timeout=5.0) as client:
        for path in common_paths:
            try:
                resp = await client.get(f"{base_url}{path}")
                if resp.status_code < 500:
                    discovered.append({
                        "path": path,
                        "method": "GET",
                        "status": resp.status_code,
                        "source": "discovery",
                    })
            except (httpx.ConnectError, httpx.TimeoutException):
                pass

    if not discovered:
        discovered.append({"path": "/", "method": "GET", "source": "fallback"})

    return discovered


async def run_api_test(
    base_url: str,
    method: str = "GET",
    path: str = "/",
    headers: dict[str, str] | None = None,
    body: dict[str, Any] | None = None,
    expected_status: int = 200,
    expected_schema: dict[str, Any] | None = None,
    timeout: float = 30.0,
) -> dict[str, Any]:
    start = time.time()

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.request(
                method=method,
                url=f"{base_url}{path}",
                headers=headers or {},
                json=body,
            )
    except httpx.ConnectError:
        return {
            "passed": False,
            "error": f"Could not connect to {base_url}",
            "name": f"{method} {path}",
        }
    except httpx.TimeoutException:
        return {
            "passed": False,
            "error": f"Request timed out after {timeout}s",
            "name": f"{method} {path}",
        }
    except Exception as e:
        return {
            "passed": False,
            "error": f"Request failed: {e}",
            "name": f"{method} {path}",
        }

    duration = round(time.time() - start, 3)
    status_ok = response.status_code == expected_status

    schema_ok = True
    schema_errors: list[str] = []
    if expected_schema and response.headers.get("content-type", "").startswith("application/json"):
        try:
            data = response.json()
            _validate_schema(data, expected_schema, schema_errors, "")
        except ValueError:
            schema_ok = False
            schema_errors.append("Response is not valid JSON")
        if schema_errors:
            schema_ok = False

    passed = status_ok and schema_ok

    result: dict[str, Any] = {
        "passed": passed,
        "name": f"{method} {path}",
        "duration": duration,
        "status_code": response.status_code,
        "expected_status": expected_status,
        "status_match": status_ok,
        "schema_match": schema_ok,
    }

    if schema_errors:
        result["schema_errors"] = schema_errors

    content_type = response.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            result["body"] = response.json()
        except ValueError:
            result["body"] = response.text[:1000]
    else:
        result["body"] = response.text[:1000]

    if not passed:
        result["headers"] = dict(response.headers)

    return result


def _validate_schema(data: Any, schema: dict[str, Any], errors: list[str], path: str) -> None:
    if "type" in schema:
        expected_type = schema["type"]
        actual_type = type(data).__name__
        if expected_type == "object" and not isinstance(data, dict):
            errors.append(f"{path}: expected object, got {actual_type}")
            return
        if expected_type == "array" and not isinstance(data, list):
            errors.append(f"{path}: expected array, got {actual_type}")
            return
        if expected_type == "string" and not isinstance(data, str):
            errors.append(f"{path}: expected string, got {actual_type}")
            return
        if expected_type == "number" and not isinstance(data, (int, float)):
            errors.append(f"{path}: expected number, got {actual_type}")
            return
        if expected_type == "boolean" and not isinstance(data, bool):
            errors.append(f"{path}: expected boolean, got {actual_type}")
            return

    if "properties" in schema and isinstance(data, dict):
        for prop, prop_schema in schema["properties"].items():
            if prop in data:
                _validate_schema(data[prop], prop_schema, errors, f"{path}.{prop}")
            elif prop_schema.get("required", False):
                errors.append(f"{path}.{prop}: missing required property")

    if "items" in schema and isinstance(data, list):
        for i, item in enumerate(data):
            _validate_schema(item, schema["items"], errors, f"{path}[{i}]")


def run_api_test_sync(**kwargs: Any) -> dict[str, Any]:
    import asyncio
    return asyncio.run(run_api_test(**kwargs))


async def discover_endpoints_sync(base_url: str, paths: list[str] | None = None) -> list[dict[str, Any]]:
    return await discover_api_endpoints(base_url, paths)
