from __future__ import annotations

__test__ = False

from typing import Any


async def detect_grpc_endpoint(url: str) -> dict[str, Any]:
    result: dict[str, Any] = {
        "url": url,
        "grpc_detected": False,
        "services": [],
        "error": None,
    }

    try:
        import httpx
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(
                url,
                headers={"Content-Type": "application/grpc", "TE": "trailers"},
                content=b"",
            )
            if resp.status_code in (200, 404, 405, 415):
                result["grpc_detected"] = True
    except ImportError:
        result["error"] = "httpx not installed"
    except Exception as e:
        result["error"] = str(e)

    return result


async def run_grpc_test(
    url: str,
    service: str = "",
    method: str = "",
    request_body: str = "",
    timeout: float = 30.0,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "url": url,
        "service": service,
        "method": method,
        "passed": False,
    }

    if not service or not method:
        result["error"] = "Service and method required for gRPC calls"
        return result

    try:
        import httpx
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(
                f"{url}/{service}/{method}",
                headers={
                    "Content-Type": "application/grpc",
                    "TE": "trailers",
                },
                content=request_body.encode() if request_body else b"",
            )
            result["passed"] = resp.status_code < 500
            result["status_code"] = resp.status_code
            result["response_length"] = len(resp.content)
    except httpx.ConnectError:
        result["error"] = f"Could not connect to {url}"
    except httpx.TimeoutException:
        result["error"] = "Request timed out"
    except Exception as e:
        result["error"] = str(e)

    return result
