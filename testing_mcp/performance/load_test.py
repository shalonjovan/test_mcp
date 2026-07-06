from __future__ import annotations

import json
import math
import statistics
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import httpx


def _perform_request(
    url: str,
    method: str,
    headers: dict[str, str],
    body: str | None,
    timeout: int,
) -> httpx.Response:
    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        method = method.upper()
        if method == "GET":
            return client.get(url, headers=headers)
        elif method == "POST":
            return client.post(url, headers=headers, content=body)
        elif method == "PUT":
            return client.put(url, headers=headers, content=body)
        elif method == "DELETE":
            return client.delete(url, headers=headers)
        elif method == "PATCH":
            return client.patch(url, headers=headers, content=body)
        elif method == "HEAD":
            return client.head(url, headers=headers)
        elif method == "OPTIONS":
            return client.options(url, headers=headers)
        raise ValueError(f"Unsupported HTTP method: {method}")


def _compute_percentile(sorted_data: list[float], percentile: float) -> float:
    if not sorted_data:
        return 0.0
    k = (len(sorted_data) - 1) * percentile / 100.0
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_data[int(k)]
    return sorted_data[f] * (c - k) + sorted_data[c] * (k - f)


def run_load_test(
    url: str,
    method: str = "GET",
    concurrent_users: int = 10,
    duration: int = 30,
    ramp_up: int = 5,
    think_time: float = 0.0,
    headers: str = "{}",
    body: str = "",
    timeout: int = 30,
) -> dict[str, Any]:
    headers_dict: dict[str, str] = json.loads(headers) if isinstance(headers, str) else headers
    body_str: str | None = body if body else None
    stagger = ramp_up / max(concurrent_users, 1)

    lock = threading.Lock()
    total_requests = 0
    successful = 0
    failed = 0
    latencies: list[float] = []
    status_codes: dict[str, int] = {}
    errors: dict[str, int] = {}
    total_bytes = 0

    test_start = time.monotonic()

    def _worker(user_id: int) -> None:
        nonlocal total_requests, successful, failed, total_bytes

        if stagger > 0 and user_id > 0:
            time.sleep(user_id * stagger)

        while time.monotonic() - test_start < duration:
            req_start = time.monotonic()
            try:
                resp = _perform_request(url, method, headers_dict, body_str, timeout)
                elapsed = (time.monotonic() - req_start) * 1000
                status_str = str(resp.status_code)

                with lock:
                    total_requests += 1
                    latencies.append(elapsed)
                    status_codes[status_str] = status_codes.get(status_str, 0) + 1
                    total_bytes += len(resp.content)
                    if resp.status_code < 400:
                        successful += 1
                    else:
                        failed += 1
            except httpx.TimeoutException:
                elapsed = (time.monotonic() - req_start) * 1000
                with lock:
                    total_requests += 1
                    latencies.append(elapsed)
                    failed += 1
                    errors["timeout"] = errors.get("timeout", 0) + 1
            except httpx.ConnectError:
                elapsed = (time.monotonic() - req_start) * 1000
                with lock:
                    total_requests += 1
                    latencies.append(elapsed)
                    failed += 1
                    errors["connection_error"] = errors.get("connection_error", 0) + 1
            except Exception as e:
                elapsed = (time.monotonic() - req_start) * 1000
                with lock:
                    total_requests += 1
                    latencies.append(elapsed)
                    failed += 1
                    err_type = type(e).__name__
                    errors[err_type] = errors.get(err_type, 0) + 1

            if think_time > 0:
                time.sleep(think_time)

    with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
        list(executor.map(_worker, range(concurrent_users)))

    actual_duration = time.monotonic() - test_start
    sorted_latencies = sorted(latencies)

    latency_ms: dict[str, float] = {}
    if sorted_latencies:
        latency_ms = {
            "min": round(sorted_latencies[0], 2),
            "max": round(sorted_latencies[-1], 2),
            "mean": round(statistics.mean(sorted_latencies), 2),
            "median": round(statistics.median(sorted_latencies), 2),
            "p50": round(_compute_percentile(sorted_latencies, 50), 2),
            "p95": round(_compute_percentile(sorted_latencies, 95), 2),
            "p99": round(_compute_percentile(sorted_latencies, 99), 2),
        }

    error_list = [{"type": k, "count": v} for k, v in sorted(errors.items(), key=lambda x: -x[1])]
    total_errors = sum(errors.values())

    return {
        "url": url,
        "method": method.upper(),
        "concurrent_users": concurrent_users,
        "planned_duration": duration,
        "ramp_up": ramp_up,
        "think_time": think_time,
        "actual_duration": round(actual_duration, 2),
        "total_requests": total_requests,
        "successful": successful,
        "failed": failed,
        "error_rate": round(total_errors / max(total_requests, 1) * 100, 2),
        "requests_per_sec": round(total_requests / max(actual_duration, 0.001), 2),
        "throughput_mbps": round(total_bytes / max(actual_duration, 0.001) / 1_048_576, 3),
        "total_bytes": total_bytes,
        "latency_ms": latency_ms,
        "status_codes": dict(sorted(status_codes.items(), key=lambda x: -x[1])),
        "errors": error_list,
    }
