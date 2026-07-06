from __future__ import annotations

from pathlib import Path
from typing import Any


TEMPLATES: dict[str, str] = {
    "pytest": """import pytest


def test_{name}():
    result = {name}()
    assert result is not None


def test_{name}_edge_case():
    with pytest.raises((ValueError, TypeError)):
        {name}(None)
""",
    "unittest": """import unittest


class Test{CapitalName}(unittest.TestCase):

    def test_{name}(self):
        result = {name}()
        self.assertIsNotNone(result)

    def test_{name}_edge(self):
        with self.assertRaises((ValueError, TypeError)):
            {name}(None)


if __name__ == "__main__":
    unittest.main()
""",
    "jest": """describe('{name}', () => {{
  it('should work', () => {{
    const result = {name}();
    expect(result).not.toBeNull();
  }});

  it('should handle edge cases', () => {{
    expect(() => {name}(null)).toThrow();
  }});
}});
""",
}


def detect_functions(path: Path) -> list[str]:
    functions: list[str] = []
    if path.suffix == ".py":
        content = path.read_text()
        for line in content.split("\n"):
            stripped = line.strip()
            if stripped.startswith("def ") and "(" in stripped:
                name = stripped[4:].split("(")[0].strip()
                if not name.startswith("_"):
                    functions.append(name)
    elif path.suffix in {".js", ".ts"}:
        content = path.read_text()
        import re
        matches = re.findall(r"(?:export\s+)?(?:function|const)\s+(\w+)", content)
        for name in matches:
            if not name.startswith("_"):
                functions.append(name)
    return functions


def generate_unit_tests(
    source_file: str,
    framework: str = "auto",
    functions: list[str] | None = None,
) -> dict[str, Any]:
    src_path = Path(source_file)
    if not src_path.exists():
        return {"error": f"File not found: {source_file}"}

    if not functions:
        functions = detect_functions(src_path)

    if not functions:
        return {"error": "No functions found to generate tests for"}

    if framework == "auto":
        if src_path.suffix == ".py":
            framework = "pytest"
        elif src_path.suffix in {".js", ".ts"}:
            framework = "jest"
        else:
            framework = "pytest"

    template = TEMPLATES.get(framework)
    if not template:
        return {"error": f"Unsupported framework: {framework}"}

    test_files: list[dict[str, Any]] = []

    for func in functions:
        capital_name = func[0].upper() + func[1:] if func else func
        test_content = template.format(name=func, CapitalName=capital_name)

        test_filename = f"test_{src_path.stem}{src_path.suffix}"
        if framework == "jest":
            test_filename = f"{src_path.stem}.test{src_path.suffix}"

        test_filepath = src_path.parent / test_filename

        test_files.append({
            "function": func,
            "framework": framework,
            "test_file": str(test_filepath),
            "content": test_content,
        })

    return {
        "source_file": source_file,
        "framework": framework,
        "functions_analyzed": functions,
        "test_count": len(test_files),
        "test_files": test_files,
    }


def save_generated_tests(test_data: dict[str, Any], dry_run: bool = True) -> dict[str, Any]:
    if "error" in test_data:
        return test_data

    saved: list[str] = []
    for tf in test_data.get("test_files", []):
        filepath = Path(tf["test_file"])
        if not dry_run:
            filepath.write_text(tf["content"])
            saved.append(str(filepath))

    return {
        "dry_run": dry_run,
        "saved_files": saved if not dry_run else [],
        "would_create": [tf["test_file"] for tf in test_data.get("test_files", [])],
    }
