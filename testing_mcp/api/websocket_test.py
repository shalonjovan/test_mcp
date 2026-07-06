from __future__ import annotations

__test__ = False

import time
from typing import Any


async def run_websocket_test(
    url: str,
    message: str | dict[str, Any] | None = None,
    timeout: float = 10.0,
    expected_messages: int = 1,
) -> dict[str, Any]:
    try:
        import websockets
    except ImportError:
        return {"error": "websockets not installed. Run: pip install websockets", "passed": False}

    result: dict[str, Any] = {
        "url": url,
        "connected": False,
        "messages_sent": 0,
        "messages_received": 0,
        "responses": [],
        "duration": 0,
    }

    start = time.time()
    try:
        async with websockets.connect(url, timeout=timeout) as ws:
            result["connected"] = True

            if message is not None:
                payload = message if isinstance(message, str) else str(message)
                await ws.send(payload)
                result["messages_sent"] += 1

            result["messages_received"] = 0
            while result["messages_received"] < expected_messages:
                try:
                    response = await ws.recv()
                    result["responses"].append(str(response)[:500])
                    result["messages_received"] += 1
                except Exception:
                    break

    except Exception as e:
        result["error"] = str(e)

    result["duration"] = round(time.time() - start, 3)
    result["passed"] = result["connected"]

    return result
