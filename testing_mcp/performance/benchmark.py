from __future__ import annotations

import subprocess
import time
from pathlib import Path
from typing import Any


def measure_startup_time(command: list[str], cwd: Path | None = None, iterations: int = 3) -> dict[str, Any]:
    times: list[float] = []
    errors: list[str] = []

    for i in range(iterations):
        try:
            start = time.time()
            proc = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=30,
            )
            elapsed = round(time.time() - start, 4)
            times.append(elapsed)
        except subprocess.TimeoutExpired:
            errors.append(f"Iteration {i}: timeout")
        except FileNotFoundError:
            return {
                "error": f"Command not found: {' '.join(command)}",
                "command": " ".join(command),
            }

    if not times:
        return {"error": "All iterations failed", "command": " ".join(command)}

    return {
        "command": " ".join(command),
        "iterations": len(times),
        "times": times,
        "min": min(times),
        "max": max(times),
        "avg": round(sum(times) / len(times), 4),
        "errors": errors,
    }


async def measure_api_latency(
    url: str,
    method: str = "GET",
    iterations: int = 5,
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    import httpx

    times: list[float] = []
    errors: list[str] = []

    async with httpx.AsyncClient(timeout=30) as client:
        for i in range(iterations):
            try:
                start = time.time()
                resp = await client.request(method=method, url=url, headers=headers)
                elapsed = round(time.time() - start, 4)
                times.append(elapsed)
            except Exception as e:
                errors.append(f"Iteration {i}: {e}")

    if not times:
        return {"error": "All requests failed", "url": url}

    return {
        "url": url,
        "method": method,
        "iterations": len(times),
        "times": times,
        "min": min(times),
        "max": max(times),
        "avg": round(sum(times) / len(times), 4),
        "p50": round(sorted(times)[len(times) // 2], 4) if len(times) > 1 else times[0],
        "p95": round(sorted(times)[int(len(times) * 0.95)], 4) if len(times) >= 20 else None,
        "p99": round(sorted(times)[int(len(times) * 0.99)], 4) if len(times) >= 100 else None,
        "errors": errors,
    }


def run_locust_benchmark(
    locustfile: str | None = None,
    host: str = "http://localhost:8080",
    users: int = 10,
    spawn_rate: int = 1,
    run_time: str = "30s",
    headless: bool = True,
) -> dict[str, Any]:
    cmd = ["locust"]

    if locustfile:
        cmd.extend(["-f", locustfile])
    cmd.extend(["--host", host])
    if headless:
        cmd.append("--headless")
    cmd.extend(["-u", str(users), "-r", str(spawn_rate), "--run-time", run_time])

    cmd.extend(["--html", "locust_report.html", "--json", "locust_stats.json"])

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    except subprocess.TimeoutExpired:
        return {"error": "Locust benchmark timed out after 600s"}
    except FileNotFoundError:
        return {"error": "Locust not installed. Run: pip install locust"}

    stats: dict[str, Any] = {}
    stats_file = Path("locust_stats.json")
    if stats_file.exists():
        import json
        try:
            stats = json.loads(stats_file.read_text())
            stats_file.unlink()
        except json.JSONDecodeError:
            stats = {"error": "Failed to parse locust stats"}

    return {
        "command": " ".join(cmd),
        "return_code": proc.returncode,
        "stats": stats,
        "stdout": proc.stdout[:2000],
        "stderr": proc.stderr[:2000],
    }
