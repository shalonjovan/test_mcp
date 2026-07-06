from testing_mcp.generators.tests import generate_unit_tests, save_generated_tests


def test_generate_pytest():
    result = generate_unit_tests("testing_mcp/cli.py", framework="pytest", functions=["serve"])
    assert "error" not in result
    assert result["framework"] == "pytest"
    assert len(result["test_files"]) == 1
    content = result["test_files"][0]["content"]
    assert "def test_serve():" in content
    assert "pytest.raises" in content


def test_generate_jest():
    result = generate_unit_tests("testing_mcp/cli.py", framework="jest", functions=["serve"])
    assert "error" not in result
    content = result["test_files"][0]["content"]
    assert "describe(" in content
    assert "it(" in content


def test_save_dry_run():
    result = generate_unit_tests("testing_mcp/cli.py", framework="pytest", functions=["serve"])
    save_result = save_generated_tests(result, dry_run=True)
    assert save_result["dry_run"] is True
    assert save_result["saved_files"] == []
    assert len(save_result["would_create"]) == 1


def test_generate_no_functions():
    result = generate_unit_tests("testing_mcp/cli.py", framework="pytest", functions=[])
    assert "error" in result


def test_file_not_found():
    result = generate_unit_tests("nonexistent.py")
    assert "error" in result
