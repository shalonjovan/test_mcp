from __future__ import annotations

import asyncio

from fastmcp import FastMCP

from testing_mcp.ui.accessibility import check_color_contrast, run_accessibility_scan
from testing_mcp.ui.playwright import run_ui_test_sync
from testing_mcp.ui.visual_regression import compare_screenshots, generate_diff_gif, take_screenshot


def register_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    def ui_test(
        url: str,
        actions: list[dict] | None = None,
        viewport: dict[str, int] | None = None,
        screenshot: bool = True,
        timeout: int = 30000,
    ) -> dict:
        """Run browser-based UI tests using Playwright."""
        return run_ui_test_sync(
            url=url,
            actions=actions,
            viewport=viewport,
            screenshot=screenshot,
            timeout=timeout,
        )

    @mcp.tool()
    def visual_regression(
        baseline: str,
        current: str,
        output_diff: str = "",
        threshold: float = 0.0,
    ) -> dict:
        """Compare two screenshots and highlight visual differences."""
        return compare_screenshots(baseline, current, output_path=output_diff, threshold=threshold)

    @mcp.tool()
    def take_screenshot_tool(
        url: str,
        output_path: str = "",
        viewport: dict[str, int] | None = None,
        full_page: bool = True,
    ) -> dict:
        """Take a screenshot of a webpage."""
        return take_screenshot(url, output_path=output_path, viewport=viewport, full_page=full_page)

    @mcp.tool()
    def create_diff_gif(
        baseline: str,
        current: str,
        output_path: str = "diff.gif",
        duration: int = 500,
    ) -> dict:
        """Create an animated GIF showing the transition between two screenshots."""
        return generate_diff_gif(baseline, current, output_path=output_path, duration=duration)

    @mcp.tool()
    def accessibility_scan(
        url: str,
        standard: str = "wcag2aa",
        include_iframe: bool = True,
        timeout: int = 30000,
    ) -> dict:
        """Run WCAG accessibility scan using axe-core."""
        return asyncio.run(run_accessibility_scan(url, standard=standard, include_iframe=include_iframe, timeout=timeout))

    @mcp.tool()
    def check_color_contrast_tool(foreground: str, background: str) -> dict:
        """Check WCAG color contrast ratio between two colors."""
        return check_color_contrast(foreground, background)
