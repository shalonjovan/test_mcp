from pathlib import Path

from testing_mcp.runners.base import TestResult
from testing_mcp.runners.python_runner import discover_python_tests


def test_test_result_to_dict():
    r = TestResult(passed=True, name="test_foo", duration=0.5, message="ok", stdout="", stderr="")
    d = r.to_dict()
    assert d["passed"] is True
    assert d["name"] == "test_foo"
    assert d["duration"] == 0.5


def test_discover_python_tests():
    tests = discover_python_tests(Path.cwd())
    assert isinstance(tests, list)


def test_discover_js_tests():
    from testing_mcp.runners.js_runner import discover_js_tests
    tests = discover_js_tests(Path.cwd())
    assert isinstance(tests, list)


def test_discover_go_tests():
    from testing_mcp.runners.go_runner import discover_go_tests
    tests = discover_go_tests(Path.cwd())
    assert isinstance(tests, list)


def test_discover_rust_tests():
    from testing_mcp.runners.rust_runner import discover_rust_tests
    tests = discover_rust_tests(Path.cwd())
    assert isinstance(tests, list)
