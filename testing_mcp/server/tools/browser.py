from __future__ import annotations

import asyncio

from fastmcp import FastMCP

from testing_mcp.browser import close_session, list_sessions, new_session, set_active_session
from testing_mcp.server.tools._helpers import _browser_sess, _resolve_url


def register_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    def browser_new_session(
        session_id: str = "",
        viewport_width: int = 1920,
        viewport_height: int = 1080,
        user_agent: str = "",
        locale: str = "en-US",
        timezone_id: str = "America/New_York",
        headless: bool = True,
    ) -> dict:
        """Create a new stealth browser session with anti-bot fingerprinting."""
        return asyncio.run(new_session(
            session_id=session_id,
            viewport={"width": viewport_width, "height": viewport_height},
            user_agent=user_agent,
            locale=locale,
            timezone_id=timezone_id,
            headless=headless,
        ))

    @mcp.tool()
    def browser_list_sessions() -> dict:
        """List all active browser sessions with their status."""
        return list_sessions()

    @mcp.tool()
    def browser_set_active_session(session_id: str) -> dict:
        """Switch the active browser session by ID."""
        return set_active_session(session_id)

    @mcp.tool()
    def browser_close_session(session_id: str = "") -> dict:
        """Close a browser session (defaults to active session)."""
        return asyncio.run(close_session(session_id))

    @mcp.tool()
    def browser_navigate(
        url: str,
        session_id: str = "",
        wait_until: str = "domcontentloaded",
        timeout: int = 30000,
        screenshot: bool = False,
    ) -> dict:
        """Navigate to a URL using the stealth browser session."""
        _resolve_url(url, allow_internal=False)
        sess, err = _browser_sess(session_id)
        if err:
            return err
        return asyncio.run(sess.navigate(url=url, wait_until=wait_until, timeout=timeout, screenshot=screenshot))

    @mcp.tool()
    def browser_click(selector: str, session_id: str = "", wait_after: int = 2000, timeout: int = 10000) -> dict:
        """Click an element identified by CSS selector."""
        sess, err = _browser_sess(session_id)
        if err:
            return err
        return asyncio.run(sess.click(selector, wait_after=wait_after, timeout=timeout))

    @mcp.tool()
    def browser_fill(selector: str, value: str, session_id: str = "", timeout: int = 10000) -> dict:
        """Fill a form field identified by CSS selector."""
        sess, err = _browser_sess(session_id)
        if err:
            return err
        return asyncio.run(sess.fill(selector, value, timeout=timeout))

    @mcp.tool()
    def browser_select_option(selector: str, value: str, session_id: str = "", timeout: int = 10000) -> dict:
        """Select an option from a dropdown/select element."""
        sess, err = _browser_sess(session_id)
        if err:
            return err
        return asyncio.run(sess.select_option(selector, value, timeout=timeout))

    @mcp.tool()
    def browser_get_text(selector: str = "body", session_id: str = "", timeout: int = 5000) -> dict:
        """Get visible text content from a page element."""
        sess, err = _browser_sess(session_id)
        if err:
            return err
        return asyncio.run(sess.get_text(selector, timeout=timeout))

    @mcp.tool()
    def browser_get_html(selector: str = "body", session_id: str = "") -> dict:
        """Get the full page HTML or inner HTML of a specific element."""
        sess, err = _browser_sess(session_id)
        if err:
            return err
        return asyncio.run(sess.get_html(selector))

    @mcp.tool()
    def browser_evaluate(js: str, session_id: str = "") -> dict:
        """Execute JavaScript in the browser page and return the result."""
        sess, err = _browser_sess(session_id)
        if err:
            return err
        return asyncio.run(sess.evaluate(js))

    @mcp.tool()
    def browser_screenshot(path: str = "", full_page: bool = True, session_id: str = "") -> dict:
        """Take a screenshot of the current page.
        If path is empty, returns base64-encoded PNG."""
        sess, err = _browser_sess(session_id)
        if err:
            return err
        return asyncio.run(sess.screenshot(path=path, full_page=full_page))

    @mcp.tool()
    def browser_get_cookies(session_id: str = "") -> dict:
        """Get all cookies from the current browser session."""
        sess, err = _browser_sess(session_id)
        if err:
            return err
        return asyncio.run(sess.get_cookies())
