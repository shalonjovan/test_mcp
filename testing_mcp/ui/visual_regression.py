from __future__ import annotations

import base64
from pathlib import Path
from typing import Any


def take_screenshot(
    url: str,
    output_path: str = "",
    viewport: dict[str, int] | None = None,
    full_page: bool = True,
) -> dict[str, Any]:
    import asyncio

    async def _capture() -> dict[str, Any]:
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            return {"error": "Playwright not installed"}

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport=viewport or {"width": 1280, "height": 720},
            )
            page = await context.new_page()

            try:
                await page.goto(url, wait_until="networkidle", timeout=30000)
            except Exception as e:
                await browser.close()
                return {"error": f"Failed to load {url}: {e}"}

            if not output_path:
                output_path = f"screenshot_{url.replace('://', '_').replace('/', '_')}.png"

            await page.screenshot(path=output_path, full_page=full_page)
            await browser.close()

            with open(output_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()

            if Path(output_path).exists() and not output_path.startswith("/"):
                pass

            return {
                "url": url,
                "screenshot_path": output_path,
                "screenshot_base64": b64,
                "viewport": viewport or {"width": 1280, "height": 720},
                "full_page": full_page,
            }

    return asyncio.run(_capture())


def compare_screenshots(
    baseline_path: str,
    current_path: str,
    output_path: str = "",
    threshold: float = 0.0,
) -> dict[str, Any]:
    try:
        from PIL import Image, ImageChops, ImageDraw
    except ImportError:
        return {"error": "Pillow not installed. Run: pip install Pillow"}

    baseline = Image.open(baseline_path)
    current = Image.open(current_path)

    if baseline.size != current.size:
        current = current.resize(baseline.size)

    diff = ImageChops.difference(baseline, current)
    bbox = diff.getbbox()

    has_diff = bbox is not None

    diff_pixels = 0
    total_pixels = baseline.width * baseline.height

    if has_diff:
        diff_pixels = sum(1 for pixel in diff.getdata() if any(c > threshold for c in pixel))

    diff_percentage = (diff_pixels / total_pixels) * 100

    if has_diff and output_path:
        highlighted = baseline.copy()
        draw = ImageDraw.Draw(highlighted)
        draw.rectangle(bbox, outline="red", width=3)
        highlighted.save(output_path)

    result: dict[str, Any] = {
        "baseline": baseline_path,
        "current": current_path,
        "has_differences": has_diff,
        "diff_pixels": diff_pixels,
        "total_pixels": total_pixels,
        "diff_percentage": round(diff_percentage, 4),
    }

    if has_diff and bbox:
        result["diff_region"] = {
            "left": bbox[0],
            "top": bbox[1],
            "right": bbox[2],
            "bottom": bbox[3],
            "width": bbox[2] - bbox[0],
            "height": bbox[3] - bbox[1],
        }

    if output_path and Path(output_path).exists():
        result["diff_image"] = output_path

    return result


def generate_diff_gif(
    baseline_path: str,
    current_path: str,
    output_path: str = "diff.gif",
    duration: int = 500,
) -> dict[str, Any]:
    try:
        from PIL import Image
    except ImportError:
        return {"error": "Pillow not installed. Run: pip install Pillow"}

    baseline = Image.open(baseline_path)
    current = Image.open(current_path)

    if baseline.size != current.size:
        current = current.resize(baseline.size)

    frames: list[Image.Image] = []
    blend_steps = 10
    for i in range(blend_steps + 1):
        alpha = i / blend_steps
        blended = Image.blend(baseline, current, alpha)
        frames.append(blended)

    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=duration,
        loop=0,
    )

    with open(output_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()

    return {
        "gif_path": output_path,
        "gif_base64": b64,
        "frames": len(frames),
        "duration_per_frame": duration,
    }
