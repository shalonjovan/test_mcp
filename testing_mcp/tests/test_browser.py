
import pytest

from testing_mcp.browser.stealth_browser import BrowserSession


def test_session_defaults():
    sess = BrowserSession()
    assert sess.session_id
    assert len(sess.session_id) == 8
    assert sess.viewport == {"width": 1920, "height": 1080}
    assert sess.headless is True
    assert sess._page is None
    assert sess._browser is None
    assert sess.is_open is False


def test_session_custom_viewport():
    sess = BrowserSession(viewport={"width": 800, "height": 600})
    assert sess.viewport["width"] == 800


def test_session_custom_session_id():
    sess = BrowserSession(session_id="my-session-1")
    assert sess.session_id == "my-session-1"


def test_guard_page_returns_error_when_not_started():
    sess = BrowserSession()
    result = sess._guard_page()
    assert result is not None
    assert result["success"] is False
    assert "error" in result


def test_guard_page_returns_none_with_default():
    sess = BrowserSession()
    result = sess._guard_page(default_result={"custom": True})
    assert result is not None
    assert result["success"] is False


def test_to_dict_includes_basic_info():
    sess = BrowserSession()
    d = sess.to_dict()
    assert d["session_id"] == sess.session_id
    assert d["headless"] is True
    assert d["is_open"] is False
    assert d["navigations"] == 0
    assert d["errors"] == []


@pytest.mark.asyncio
async def test_page_op_returns_guard_error_when_no_page():
    sess = BrowserSession()
    result = await sess._page_op(lambda r: None)
    assert result["success"] is False
    assert "Session not started" in result["error"]


@pytest.mark.asyncio
async def test_page_op_catches_exception():
    sess = BrowserSession()
    sess._page = True  # bypass guard by setting truthy value
    result = await sess._page_op(lambda r: exec("raise ValueError('boom')"))
    assert result["success"] is False
    assert "boom" in result.get("error", "")


@pytest.mark.asyncio
async def test_page_op_success():
    sess = BrowserSession()
    sess._page = True  # bypass guard
    results: list[str] = []

    async def my_fn(r):
        results.append("called")

    result = await sess._page_op(my_fn)
    assert result["success"] is True
    assert results == ["called"]
    assert sess._last_active > 0


def test_to_dict_includes_errors():
    sess = BrowserSession()
    sess._errors.append("err1")
    sess._errors.append("err2")
    d = sess.to_dict()
    assert "err1" in d["errors"]
    assert len(d["errors"]) == 2
