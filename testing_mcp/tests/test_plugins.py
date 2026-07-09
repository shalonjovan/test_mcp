from pathlib import Path

from testing_mcp.plugins.base import LanguagePlugin, PluginManager


class MockLanguagePlugin(LanguagePlugin):
    name = "mock-python"
    language = "python"

    def can_handle(self, project_root: Path) -> bool:
        return (project_root / "pyproject.toml").exists()

    def run(self, project_root: Path, **kwargs):
        return {"language": "python", "detected": True}


def test_plugin_registration():
    mgr = PluginManager()
    plugin = MockLanguagePlugin()
    mgr.register(plugin)
    plugins = mgr.get_plugins("language")
    assert len(plugins) == 1
    assert plugins[0].name == "mock-python"


def test_get_all_plugins():
    mgr = PluginManager()
    mgr.register(MockLanguagePlugin())
    all_plugins = mgr.get_plugins()
    assert len(all_plugins) >= 1


def test_plugin_can_handle():
    plugin = MockLanguagePlugin()
    assert plugin.can_handle(Path.cwd())
    assert not plugin.can_handle(Path("/tmp"))
