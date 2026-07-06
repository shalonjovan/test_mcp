from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any


def measure_memory_usage(pid: int | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {}
    try:
        import psutil
        process = psutil.Process(pid or os.getpid())
        mem = process.memory_info()
        result = {
            "rss_mb": round(mem.rss / 1024 / 1024, 2),
            "vms_mb": round(mem.vms / 1024 / 1024, 2),
            "percent": process.memory_percent(),
        }
    except ImportError:
        try:
            proc_path = Path(f"/proc/{pid or os.getpid()}/status")
            if proc_path.exists():
                for line in proc_path.read_text().split("\n"):
                    if line.startswith("VmRSS:"):
                        result["rss_kb"] = line.split()[1]
                    elif line.startswith("VmSize:"):
                        result["vms_kb"] = line.split()[1]
        except (OSError, IndexError):
            result["error"] = "Could not read memory info"
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        result["error"] = "Could not access process"
    return result


async def profile_api_memory(
    url: str,
    iterations: int = 10,
    warmup: int = 2,
) -> dict[str, Any]:
    import httpx

    memories: list[float] = []
    latencies: list[float] = []

    async with httpx.AsyncClient(timeout=30) as client:
        for i in range(iterations + warmup):
            start = time.time()
            try:
                await client.get(url)
                latencies.append(round(time.time() - start, 4))
            except Exception:
                latencies.append(0)
            mem = measure_memory_usage()
            if i >= warmup:
                memories.append(mem.get("rss_mb", 0))

    total_alloc = max(memories) - min(memories) if memories else 0

    return {
        "url": url,
        "iterations": iterations,
        "memory_usage": {
            "samples": memories,
            "min_mb": round(min(memories), 2) if memories else 0,
            "max_mb": round(max(memories), 2) if memories else 0,
            "avg_mb": round(sum(memories) / len(memories), 2) if memories else 0,
            "total_allocated_mb": round(total_alloc, 2),
        },
        "latency": {
            "min_ms": round(min(latencies) * 1000, 2) if latencies else 0,
            "max_ms": round(max(latencies) * 1000, 2) if latencies else 0,
            "avg_ms": round((sum(latencies) / len(latencies)) * 1000, 2) if latencies else 0,
        },
    }


def measure_startup_resources(
    command: list[str],
    cwd: Path | None = None,
    iterations: int = 3,
) -> dict[str, Any]:
    import subprocess

    times: list[float] = []
    memories: list[float] = []

    for _ in range(iterations):
        start = time.time()
        try:
            proc = subprocess.run(command, cwd=cwd, capture_output=True, timeout=30)
            elapsed = round(time.time() - start, 4)
            times.append(elapsed)
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            return {"error": str(e)}

    return {
        "command": " ".join(command),
        "iterations": iterations,
        "startup_time": {
            "min_s": min(times),
            "max_s": max(times),
            "avg_s": round(sum(times) / len(times), 4),
        },
    }


def get_network_io() -> dict[str, Any]:
    result: dict[str, Any] = {}
    try:
        net_path = Path("/proc/net/dev")
        if net_path.exists():
            interfaces: dict[str, dict[str, int]] = {}
            for line in net_path.read_text().split("\n")[2:]:
                if ":" in line:
                    name, data = line.split(":", 1)
                    vals = data.split()
                    interfaces[name.strip()] = {
                        "rx_bytes": int(vals[0]),
                        "tx_bytes": int(vals[8]),
                    }
            result["interfaces"] = interfaces
    except (OSError, IndexError, ValueError):
        result["error"] = "Could not read network info"

    return result


def get_disk_io() -> dict[str, Any]:
    result: dict[str, Any] = {}
    try:
        disk_path = Path("/proc/diskstats")
        if disk_path.exists():
            devices: dict[str, dict[str, int]] = {}
            for line in disk_path.read_text().split("\n"):
                parts = line.split()
                if len(parts) >= 14 and not parts[2].startswith(("loop", "ram")):
                    devices[parts[2]] = {
                        "reads": int(parts[3]),
                        "read_sectors": int(parts[5]),
                        "writes": int(parts[7]),
                        "write_sectors": int(parts[9]),
                    }
            result["devices"] = devices
    except (OSError, IndexError, ValueError):
        result["error"] = "Could not read disk info"

    return result


def get_cpu_info() -> dict[str, Any]:
    result: dict[str, Any] = {}
    try:
        cpu_path = Path("/proc/stat")
        if cpu_path.exists():
            for line in cpu_path.read_text().split("\n"):
                if line.startswith("cpu"):
                    parts = line.split()
                    if len(parts) >= 5:
                        total = sum(int(p) for p in parts[1:])
                        idle = int(parts[4])
                        result[parts[0]] = {
                            "usage_percent": round((1 - idle / total) * 100, 1) if total else 0,
                            "total_ticks": total,
                            "idle_ticks": idle,
                        }
    except (OSError, IndexError, ValueError):
        result["error"] = "Could not read CPU info"

    return result
