from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class Plugin(ABC):
    name: str = ""
    version: str = "0.1.0"
    description: str = ""

    @abstractmethod
    def can_handle(self, project_root: Path) -> bool:
        ...

    @abstractmethod
    def run(self, project_root: Path, **kwargs: Any) -> dict[str, Any]:
        ...


class LanguagePlugin(Plugin, ABC):
    language: str = ""


class FrameworkPlugin(Plugin, ABC):
    framework: str = ""


class ReporterPlugin(Plugin, ABC):
    format: str = ""


class PluginManager:
    def __init__(self) -> None:
        self._plugins: dict[str, list[Plugin]] = {
            "language": [],
            "framework": [],
            "reporter": [],
            "browser": [],
            "database": [],
            "performance": [],
            "security": [],
        }

    def register(self, plugin: Plugin) -> None:
        for category in self._plugins:
            if isinstance(plugin, (LanguagePlugin,)):
                self._plugins["language"].append(plugin)
                return
            elif isinstance(plugin, (FrameworkPlugin,)):
                self._plugins["framework"].append(plugin)
                return
            elif isinstance(plugin, (ReporterPlugin,)):
                self._plugins["reporter"].append(plugin)
                return
        self._plugins.setdefault("custom", []).append(plugin)

    def get_plugins(self, category: str = "") -> list[Plugin]:
        if category:
            return self._plugins.get(category, [])
        all_plugins: list[Plugin] = []
        for cat_plugins in self._plugins.values():
            all_plugins.extend(cat_plugins)
        return all_plugins

    def discover(self, search_path: Path | None = None) -> list[Plugin]:
        if search_path is None:
            search_path = Path.cwd() / "plugins"

        if not search_path.is_dir():
            return []

        import importlib.util
        import inspect

        discovered: list[Plugin] = []
        for py_file in search_path.glob("*.py"):
            if py_file.name.startswith("_"):
                continue
            spec = importlib.util.spec_from_file_location(py_file.stem, py_file)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                for _, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, Plugin) and obj is not Plugin:
                        instance = obj()
                        self.register(instance)
                        discovered.append(instance)

        return discovered


plugin_manager = PluginManager()
