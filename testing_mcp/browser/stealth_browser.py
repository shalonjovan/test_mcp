from __future__ import annotations

import base64
import time
import uuid
from pathlib import Path
from typing import Any

STEALTH_INIT_SCRIPT = """
// Webdriver
Object.defineProperty(navigator, 'webdriver', { get: () => false });

// Plugins
Object.defineProperty(navigator, 'plugins', {
    get: () => [
        { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer' },
        { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' },
        { name: 'Native Client', filename: 'internal-nacl-plugin' }
    ]
});

// Languages
Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });

// Chrome runtime
window.chrome = {
    runtime: {},
    loadTimes: function() {},
    csi: function() {},
    app: {}
};

// Permissions
const originalQuery = window.navigator.permissions.query;
window.navigator.permissions.query = (parameters) => (
    parameters.name === 'notifications'
        ? Promise.resolve({ state: 'denied' })
        : originalQuery(parameters)
);

// WebGL vendor/renderer
const getParameter = WebGLRenderingContext.prototype.getParameter;
WebGLRenderingContext.prototype.getParameter = function(p) {
    if (p === 37445) return 'Intel Inc.';
    if (p === 37446) return 'Intel Iris OpenGL Engine';
    return getParameter(p);
};
"""


class BrowserSession:
    def __init__(
        self,
        session_id: str = "",
        viewport: dict[str, int] | None = None,
        user_agent: str = "",
        locale: str = "en-US",
        timezone_id: str = "America/New_York",
        headless: bool = True,
    ):
        self.session_id = session_id or str(uuid.uuid4())[:8]
        self.viewport = viewport or {"width": 1920, "height": 1080}
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/127.0.0.0 Safari/537.36"
        )
        self.locale = locale
        self.timezone_id = timezone_id
        self.headless = headless

        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None
        self._created_at: float = 0.0
        self._last_active: float = 0.0
        self._navigations: int = 0
        self._errors: list[str] = []

    @property
    def is_open(self) -> bool:
        return self._page is not None

    @property
    def current_url(self) -> str:
        if self._page:
            try:
                import asyncio
                return asyncio.run_coroutine_threadsafe(
                    self._page.evaluate("() => window.location.href"),
                    asyncio.get_event_loop(),
                ).result(timeout=2)
            except Exception:
                return ""
        return ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "viewport": self.viewport,
            "user_agent": self.user_agent[:80],
            "locale": self.locale,
            "timezone": self.timezone_id,
            "headless": self.headless,
            "is_open": self.is_open,
            "url": self.current_url,
            "navigations": self._navigations,
            "created_at": self._created_at,
            "last_active": self._last_active,
            "errors": self._errors[-5:],
        }

    async def start(self) -> dict[str, Any]:
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            return {
                "success": False,
                "error": "Playwright not installed. Run: pip install playwright && playwright install",
            }

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=self.headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
                f"--window-size={self.viewport['width']},{self.viewport['height']}",
            ],
        )

        self._context = await self._browser.new_context(
            viewport=self.viewport,
            user_agent=self.user_agent,
            locale=self.locale,
            timezone_id=self.timezone_id,
            color_scheme="light",
            device_scale_factor=1,
        )

        await self._context.add_init_script(STEALTH_INIT_SCRIPT)

        self._page = await self._context.new_page()

        self._page.on("pageerror", lambda err: self._errors.append(str(err)[:200]))

        self._created_at = time.time()
        self._last_active = time.time()

        return {
            "success": True,
            "session_id": self.session_id,
            "message": f"Browser session {self.session_id} started",
        }

    async def navigate(
        self,
        url: str,
        wait_until: str = "domcontentloaded",
        timeout: int = 30000,
        screenshot: bool = False,
    ) -> dict[str, Any]:
        if not self._page:
            return {"success": False, "error": "Session not started"}

        result: dict[str, Any] = {
            "success": True,
            "url": url,
            "final_url": "",
            "title": "",
            "status_code": 0,
            "cloudflare_blocked": False,
        }

        try:
            resp = await self._page.goto(url, wait_until=wait_until, timeout=timeout)
            if resp:
                result["status_code"] = resp.status
                result["final_url"] = resp.url

            await self._page.wait_for_timeout(2000)

            title = await self._page.title()
            result["title"] = title

            body_text = await self._page.text_content("body") or ""
            body_lower = body_text.lower()

            is_blocked = (
                "attention required" in title.lower()
                or "cloudflare" in title.lower()
                or (resp and resp.status in (403, 503, 429))
            )

            if is_blocked:
                result["cloudflare_blocked"] = True
                result["warning"] = "Cloudflare challenge detected — waiting for resolution"

                for attempt in range(3):
                    await self._page.wait_for_timeout(10000)
                    title2 = await self._page.title()
                    body2 = await self._page.text_content("body") or ""

                    if "attention required" not in title2.lower() and "cloudflare" not in title2.lower():
                        result["cloudflare_blocked"] = False
                        result["warning"] = "Cloudflare challenge resolved"
                        result["title"] = title2
                        break
                    elif attempt == 2:
                        result["warning"] = "Cloudflare challenge could not be resolved automatically"

            self._navigations += 1
            self._last_active = time.time()

            if screenshot:
                b64 = await self._take_screenshot_b64()
                result["screenshot"] = b64

        except Exception as e:
            result["success"] = False
            result["error"] = str(e)
            self._errors.append(str(e)[:200])

        return result

    async def click(
        self,
        selector: str,
        wait_after: int = 2000,
        timeout: int = 10000,
    ) -> dict[str, Any]:
        if not self._page:
            return {"success": False, "error": "Session not started"}

        result: dict[str, Any] = {"success": True, "selector": selector}

        try:
            await self._page.click(selector, timeout=timeout)
            await self._page.wait_for_timeout(wait_after)
            result["url"] = self._page.url
            result["title"] = await self._page.title()
            self._last_active = time.time()
        except Exception as e:
            result["success"] = False
            result["error"] = str(e)
            self._errors.append(str(e)[:200])

        return result

    async def fill(
        self,
        selector: str,
        value: str,
        timeout: int = 10000,
    ) -> dict[str, Any]:
        if not self._page:
            return {"success": False, "error": "Session not started"}

        result: dict[str, Any] = {"success": True, "selector": selector}

        try:
            await self._page.fill(selector, value, timeout=timeout)
            self._last_active = time.time()
        except Exception as e:
            result["success"] = False
            result["error"] = str(e)
            self._errors.append(str(e)[:200])

        return result

    async def select_option(
        self,
        selector: str,
        value: str,
        timeout: int = 10000,
    ) -> dict[str, Any]:
        if not self._page:
            return {"success": False, "error": "Session not started"}

        result: dict[str, Any] = {"success": True, "selector": selector}

        try:
            await self._page.select_option(selector, value, timeout=timeout)
            self._last_active = time.time()
        except Exception as e:
            result["success"] = False
            result["error"] = str(e)

        return result

    async def get_text(self, selector: str = "body", timeout: int = 5000) -> dict[str, Any]:
        if not self._page:
            return {"success": False, "error": "Session not started"}

        result: dict[str, Any] = {"success": True}

        try:
            element = await self._page.wait_for_selector(selector, timeout=timeout)
            if element:
                text = await element.text_content()
                result["text"] = (text or "").strip()
            else:
                result["text"] = ""
                result["warning"] = f"Selector '{selector}' not found"
        except Exception as e:
            result["success"] = False
            result["error"] = str(e)

        return result

    async def get_html(self, selector: str = "body") -> dict[str, Any]:
        if not self._page:
            return {"success": False, "error": "Session not started"}

        result: dict[str, Any] = {"success": True}

        try:
            if selector == "body":
                html = await self._page.content()
            else:
                element = await self._page.query_selector(selector)
                if element:
                    html = await element.inner_html()
                else:
                    html = ""
            result["html"] = html
            result["length"] = len(html)
        except Exception as e:
            result["success"] = False
            result["error"] = str(e)

        return result

    async def evaluate(self, js: str) -> dict[str, Any]:
        if not self._page:
            return {"success": False, "error": "Session not started"}

        result: dict[str, Any] = {"success": True}

        try:
            value = await self._page.evaluate(js)
            result["result"] = value
        except Exception as e:
            result["success"] = False
            result["error"] = str(e)

        return result

    async def screenshot(
        self,
        path: str = "",
        full_page: bool = True,
    ) -> dict[str, Any]:
        if not self._page:
            return {"success": False, "error": "Session not started"}

        result: dict[str, Any] = {"success": True}

        try:
            if path:
                await self._page.screenshot(path=path, full_page=full_page)
                result["path"] = path
            else:
                b64 = await self._take_screenshot_b64(full_page=full_page)
                result["screenshot"] = b64
        except Exception as e:
            result["success"] = False
            result["error"] = str(e)

        return result

    async def _take_screenshot_b64(self, full_page: bool = True) -> str:
        ss_bytes = await self._page.screenshot(full_page=full_page)
        return base64.b64encode(ss_bytes).decode()

    async def get_cookies(self) -> dict[str, Any]:
        if not self._context:
            return {"success": False, "error": "Session not started"}

        result: dict[str, Any] = {"success": True}

        try:
            cookies = await self._context.cookies()
            result["cookies"] = [
                {"name": c["name"], "value": c["value"][:40], "domain": c["domain"], "path": c["path"]}
                for c in cookies
            ]
            result["count"] = len(cookies)
        except Exception as e:
            result["success"] = False
            result["error"] = str(e)

        return result

    async def close(self) -> dict[str, Any]:
        errors = []
        try:
            if self._page:
                await self._page.close()
        except Exception as e:
            errors.append(str(e)[:100])

        try:
            if self._context:
                await self._context.close()
        except Exception as e:
            errors.append(str(e)[:100])

        try:
            if self._browser:
                await self._browser.close()
        except Exception as e:
            errors.append(str(e)[:100])

        try:
            if self._playwright:
                await self._playwright.stop()
        except Exception as e:
            errors.append(str(e)[:100])

        self._page = None
        self._context = None
        self._browser = None
        self._playwright = None

        return {
            "success": len(errors) == 0,
            "session_id": self.session_id,
            "errors": errors if errors else None,
        }


_sessions: dict[str, BrowserSession] = {}
_active_session_id: str = ""


async def new_session(
    session_id: str = "",
    viewport: dict[str, int] | None = None,
    user_agent: str = "",
    locale: str = "en-US",
    timezone_id: str = "America/New_York",
    headless: bool = True,
) -> dict[str, Any]:
    sid = session_id or f"session_{uuid.uuid4().hex[:6]}"

    session = BrowserSession(
        session_id=sid,
        viewport=viewport,
        user_agent=user_agent,
        locale=locale,
        timezone_id=timezone_id,
        headless=headless,
    )

    result = await session.start()
    if result.get("success"):
        _sessions[sid] = session
        global _active_session_id
        _active_session_id = sid

    return result


def get_session(session_id: str = "") -> BrowserSession | None:
    sid = session_id or _active_session_id
    return _sessions.get(sid)


def set_active_session(session_id: str) -> dict[str, Any]:
    global _active_session_id
    if session_id in _sessions:
        _active_session_id = session_id
        return {"success": True, "session_id": session_id}
    return {"success": False, "error": f"Session '{session_id}' not found"}


def list_sessions() -> dict[str, Any]:
    return {
        "active_session_id": _active_session_id,
        "sessions": {sid: sess.to_dict() for sid, sess in _sessions.items()},
        "count": len(_sessions),
    }


async def close_session(session_id: str = "") -> dict[str, Any]:
    global _active_session_id

    sid = session_id or _active_session_id
    session = _sessions.get(sid)
    if not session:
        return {"success": False, "error": f"Session '{sid}' not found"}

    result = await session.close()
    if sid in _sessions:
        del _sessions[sid]
    if _active_session_id == sid:
        _active_session_id = next(iter(_sessions.keys())) if _sessions else ""

    return result
