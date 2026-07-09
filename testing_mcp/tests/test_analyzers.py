from pathlib import Path


from testing_mcp.analyzers.project import analyze_project


def test_analyze_project_detects_python():
    result = analyze_project(Path.cwd())
    assert "python" in result["languages"]
    assert result["languages"]["python"] > 0


def test_analyze_project_returns_root():
    result = analyze_project(Path.cwd())
    assert "project_root" in result
    assert Path(result["project_root"]).resolve() == Path.cwd().resolve()


def test_analyze_project_has_keys():
    result = analyze_project(Path.cwd())
    expected_keys = {"languages", "frameworks", "package_managers", "build_tools", "test_frameworks", "entry_points", "project_root"}
    assert expected_keys.issubset(result.keys())
