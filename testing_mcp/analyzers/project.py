from __future__ import annotations

from pathlib import Path
from typing import Any

LANGUAGE_PATTERNS: dict[str, list[str]] = {
    "python": ["*.py", "pyproject.toml", "setup.py", "requirements.txt", "Pipfile"],
    "java": ["*.java", "pom.xml", "build.gradle", "build.gradle.kts"],
    "javascript": ["*.js", "package.json"],
    "typescript": ["*.ts", "*.tsx", "tsconfig.json"],
    "rust": ["*.rs", "Cargo.toml"],
    "go": ["*.go", "go.mod"],
    "c": ["*.c", "*.h", "Makefile"],
    "cpp": ["*.cpp", "*.hpp", "CMakeLists.txt"],
    "csharp": ["*.cs", "*.csproj", "*.sln"],
    "kotlin": ["*.kt", "*.kts", "build.gradle.kts"],
    "zig": ["*.zig", "build.zig"],
}

FRAMEWORK_PATTERNS: dict[str, dict[str, list[str]]] = {
    "python": {
        "fastapi": ["fastapi"],
        "flask": ["flask"],
        "django": ["django", "manage.py"],
        "pytest": ["pytest"],
    },
    "javascript": {
        "react": ["react"],
        "vue": ["vue"],
        "angular": ["angular"],
        "next": ["next"],
        "express": ["express"],
        "jest": ["jest"],
        "playwright": ["playwright"],
        "vitest": ["vitest"],
    },
    "java": {
        "spring-boot": ["spring-boot"],
        "junit": ["junit"],
    },
}

PACKAGE_MANAGER_PATTERNS: dict[str, list[str]] = {
    "pip": ["requirements.txt"],
    "poetry": ["pyproject.toml"],
    "npm": ["package.json", "package-lock.json"],
    "yarn": ["yarn.lock"],
    "pnpm": ["pnpm-lock.yaml"],
    "cargo": ["Cargo.toml"],
    "go": ["go.mod"],
    "maven": ["pom.xml"],
    "gradle": ["build.gradle", "build.gradle.kts"],
}

BUILD_TOOL_PATTERNS: dict[str, list[str]] = {
    "make": ["Makefile"],
    "cmake": ["CMakeLists.txt"],
    "maven": ["pom.xml"],
    "gradle": ["build.gradle", "gradlew"],
    "cargo": ["Cargo.toml"],
}


def _find_files(root: Path, patterns: list[str]) -> list[Path]:
    found: list[Path] = []
    for pattern in patterns:
        matches = list(root.glob(pattern))
        found.extend(matches)
    return found


def _detect_languages(root: Path) -> dict[str, float]:
    languages: dict[str, float] = {}
    for lang, patterns in LANGUAGE_PATTERNS.items():
        matches = _find_files(root, patterns)
        if matches:
            score = min(1.0, len(matches) * 0.3)
            languages[lang] = score
    return languages


def _detect_frameworks(root: Path, languages: dict[str, float]) -> dict[str, float]:
    frameworks: dict[str, float] = {}
    for lang in languages:
        lang_frameworks = FRAMEWORK_PATTERNS.get(lang, {})
        for fw, patterns in lang_frameworks.items():
            matches = _find_files(root, patterns)
            if matches:
                fw_score = sum(1 for m in matches if m.suffix in {".py", ".js", ".ts", ".json", ".toml", ".cfg"})
                confidence = min(1.0, max(0.3, fw_score * 0.3))
                if fw == "pytest" and "conftest.py" in [m.name for m in matches]:
                    confidence = 1.0
                if fw == "junit" and any("test" in m.name.lower() for m in matches):
                    confidence = 1.0
                if fw == "playwright":
                    config_files = [m for m in matches if "playwright.config" in m.name]
                    if config_files:
                        confidence = 1.0
                frameworks[fw] = confidence
    return frameworks


def _detect_package_managers(root: Path) -> dict[str, float]:
    managers: dict[str, float] = {}
    for pm, patterns in PACKAGE_MANAGER_PATTERNS.items():
        matches = _find_files(root, patterns)
        if matches:
            if pm == "poetry" and any("poetry.lock" in m.name for m in _find_files(root, ["poetry.lock"])):
                managers[pm] = 1.0
            else:
                managers[pm] = 1.0
    return managers


def _detect_build_tools(root: Path) -> dict[str, float]:
    tools: dict[str, float] = {}
    for bt, patterns in BUILD_TOOL_PATTERNS.items():
        matches = _find_files(root, patterns)
        if matches:
            tools[bt] = 1.0
    return tools


def _detect_test_frameworks(root: Path, languages: dict[str, float]) -> dict[str, float]:
    test_frameworks: dict[str, float] = {}

    if "python" in languages:
        if _find_files(root, ["pytest.ini", "pyproject.toml", "setup.cfg"]):
            test_frameworks["pytest"] = 1.0
        if any("test" in p.name.lower() for p in root.rglob("test_*.py")):
            test_frameworks["pytest"] = max(test_frameworks.get("pytest", 0), 1.0)

    if "java" in languages:
        if _find_files(root, ["pom.xml", "build.gradle"]):
            test_frameworks["junit"] = 0.7

    if "javascript" in languages or "typescript" in languages:
        package_file = root / "package.json"
        if package_file.exists():
            import json

            try:
                data = json.loads(package_file.read_text())
                deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                mapping = {
                    "jest": "jest",
                    "vitest": "vitest",
                    "playwright": "@playwright/test",
                    "cypress": "cypress",
                }
                for fw, key in mapping.items():
                    if key in deps:
                        test_frameworks[fw] = 1.0
            except (json.JSONDecodeError, KeyError):
                pass

    if "rust" in languages:
        test_frameworks["rust-test"] = 1.0

    if "go" in languages:
        test_frameworks["go-test"] = 1.0

    return test_frameworks


def analyze_project(root: Path | None = None) -> dict[str, Any]:
    if root is None:
        root = Path.cwd()

    languages = _detect_languages(root)
    frameworks = _detect_frameworks(root, languages)
    package_managers = _detect_package_managers(root)
    build_tools = _detect_build_tools(root)
    test_frameworks = _detect_test_frameworks(root, languages)

    entry_points: list[str] = []
    for pattern in ["main.py", "app.py", "index.js", "main.go", "main.rs", "Main.java"]:
        matches = _find_files(root, [pattern])
        entry_points.extend(str(m.relative_to(root)) for m in matches)

    return {
        "languages": languages,
        "frameworks": frameworks,
        "package_managers": package_managers,
        "build_tools": build_tools,
        "test_frameworks": test_frameworks,
        "entry_points": entry_points,
        "project_root": str(root.resolve()),
    }
