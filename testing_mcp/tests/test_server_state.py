
from testing_mcp.server.state import get_settings, get_start_time, set_settings
from testing_mcp.utils.config import Settings


def test_get_start_time_returns_float():
    t = get_start_time()
    assert isinstance(t, float)
    assert t > 0


def test_get_start_time_monotonic():
    t1 = get_start_time()
    t2 = get_start_time()
    assert t2 >= t1


def test_get_settings_returns_settings():
    s = get_settings()
    assert isinstance(s, Settings)
    assert hasattr(s, "host")
    assert hasattr(s, "port")
    assert hasattr(s, "version")


def test_set_settings_overrides():
    original = get_settings()
    custom = Settings(host="10.0.0.1", port=9999)
    set_settings(custom)
    try:
        assert get_settings().host == "10.0.0.1"
        assert get_settings().port == 9999
    finally:
        set_settings(original)
    assert get_settings().host == original.host
