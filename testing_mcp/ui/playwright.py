from __future__ import annotations

import asyncio
import base64
import time
from pathlib import Path
from typing import Any


async def run_ui_test(
    url: str,
    actions: list[dict[str, Any]] | None = None,
    viewport: dict[str, int] | None = None,
    screenshot: bool = True,
    timeout: int = 30000,
) -> dict[str, Any]:
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return {
            "passed": False,
            "error": "Playwright not installed. Run: pip install playwright && playwright install",
        }

    results: dict[str, Any] = {
        "passed": True,
        "url": url,
        "actions_performed": [],
        "screenshots": [],
        "console_errors": [],
        "duration": 0,
    }

    start = time.time()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport=viewport or {"width": 1280, "height": 720},
        )
        page = await context.new_page()

        page.on("console", lambda msg: results["console_errors"].append(msg.text) if msg.type == "error" else None)

        try:
            await page.goto(url, timeout=timeout, wait_until="networkidle")
        except Exception as e:
            await browser.close()
            return {"passed": False, "error": str(e), "url": url}

        if screenshot:
            ss_path = f"ui_test_{int(time.time())}.png"
            await page.screenshot(path=ss_path, full_page=True)
            with open(ss_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            results["screenshots"].append(b64)
            Path(ss_path).unlink(missing_ok=True)

        if actions:
            for i, action in enumerate(actions):
                try:
                    action_type = action.get("type", "click")
                    selector = action.get("selector", "")
                    value = action.get("value", "")

                    if action_type == "click":
                        await page.click(selector, timeout=5000)
                    elif action_type == "fill":
                        await page.fill(selector, value, timeout=5000)
                    elif action_type == "type":
                        await page.type(selector, value, delay=50)
                    elif action_type == "select":
                        await page.select_option(selector, value)
                    elif action_type == "wait":
                        await page.wait_for_timeout(int(value or 1000))
                    elif action_type == "screenshot":
                        ss_path = f"ui_test_action_{i}_{int(time.time())}.png"
                        await page.screenshot(path=ss_path, full_page=False)
                        with open(ss_path, "rb") as f:
                            b64 = base64.b64encode(f.read()).decode()
                        results["screenshots"].append(b64)
                        Path(ss_path).unlink(missing_ok=True)

                    results["actions_performed"].append({
                        "index": i,
                        "type": action_type,
                        "selector": selector,
                        "success": True,
                    })
                except Exception as e:
                    results["actions_performed"].append({
                        "index": i,
                        "type": action.get("type", "click"),
                        "selector": action.get("selector", ""),
                        "success": False,
                        "error": str(e),
                    })
                    results["passed"] = False

        await browser.close()

    results["duration"] = round(time.time() - start, 3)
    return results


def run_ui_test_sync(**kwargs: Any) -> dict[str, Any]:
    return asyncio.run(run_ui_test(**kwargs))
