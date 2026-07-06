from testing_mcp.runners.analysis import analyze_failure, suggest_fix


def test_assertion_failure():
    result = analyze_failure("test_foo", stderr="AssertionError: assert 1 == 2")
    assert result["probable_cause"] == "Assertion failure"
    assert result["confidence"] == 0.9


def test_missing_dependency():
    result = analyze_failure("test_foo", stderr="ModuleNotFoundError: No module named pandas")
    assert "Missing dependency" in result["probable_cause"]
    assert result["confidence"] == 0.95


def test_timeout_failure():
    result = analyze_failure("test_foo", stderr="TimeoutError: operation timed out")
    assert result["probable_cause"] == "Timeout"
    assert result["confidence"] == 0.8


def test_suggest_fix_multiple():
    results = [
        {"passed": True, "name": "test_ok", "stdout": ""},
        {"passed": False, "name": "test_fail", "stderr": "AssertionError: assert x == y"},
    ]
    fixes = suggest_fix(results)
    assert len(fixes) == 1
    assert fixes[0]["test_name"] == "test_fail"


def test_empty_results():
    fixes = suggest_fix([])
    assert fixes == []


def test_all_passed():
    results = [
        {"passed": True, "name": "test_a"},
        {"passed": True, "name": "test_b"},
    ]
    fixes = suggest_fix(results)
    assert fixes == []
