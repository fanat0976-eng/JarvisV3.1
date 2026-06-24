"""
Jarvis V3.1 — Plugin Manager
Auto-discovery, lifecycle hooks, config-driven enable/disable.
"""
import importlib
import sys
from pathlib import Path
from typing import Optional

import yaml

PLUGINS_DIR = Path(__file__).parent.parent / "plugins"
CONFIG_PATH = Path(__file__).parent / "config.yaml"


def load_config() -> dict:
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def save_config(config: dict):
    with open(CONFIG_PATH, "w") as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)


class PluginManager:
    def __init__(self):
        self.plugins: dict[str, dict] = {}
        self.config = load_config()

    def discover(self) -> list[str]:
        discovered = []
        for item in PLUGINS_DIR.iterdir():
            if item.is_dir() and not item.name.startswith("_"):
                handler = item / "handler.py"
                if handler.exists():
                    discovered.append(item.name)
        return discovered

    def load_plugin(self, name: str) -> Optional[dict]:
        if name in self.plugins:
            return self.plugins[name]

        plugin_dir = PLUGINS_DIR / name
        handler_path = plugin_dir / "handler.py"

        if not handler_path.exists():
            return None

        plugin_config = self.config.get("plugins", {}).get(name, {})
        if not plugin_config.get("enabled", True):
            return None

        if str(PLUGINS_DIR.parent) not in sys.path:
            sys.path.insert(0, str(PLUGINS_DIR.parent))

        module_name = f"plugins.{name}.handler"
        try:
            mod = importlib.import_module(module_name)
        except Exception as e:
            print(f"  Failed to load plugin '{name}': {e}")
            return None

        plugin_info = {
            "name": name,
            "module": mod,
            "config": plugin_config,
            "router": getattr(mod, "router", None),
            "description": plugin_config.get("description", ""),
        }

        self.plugins[name] = plugin_info
        return plugin_info

    def load_all(self) -> dict[str, dict]:
        discovered = self.discover()
        for name in discovered:
            self.load_plugin(name)
        return self.plugins

    def startup_all(self):
        for name, info in self.plugins.items():
            handler = getattr(info["module"], "on_startup", None)
            if handler:
                try:
                    handler()
                    print(f"  [startup] {name}")
                except Exception as e:
                    print(f"  [startup] {name} ERROR: {e}")

    def shutdown_all(self):
        for name, info in self.plugins.items():
            handler = getattr(info["module"], "on_shutdown", None)
            if handler:
                try:
                    handler()
                    print(f"  [shutdown] {name}")
                except Exception as e:
                    print(f"  [shutdown] {name} ERROR: {e}")

    def get_plugin(self, name: str) -> Optional[dict]:
        return self.plugins.get(name)

    def get_status(self) -> dict:
        result = {}
        for name in self.config.get("plugins", {}):
            pc = self.config["plugins"][name]
            if not pc.get("enabled", True):
                continue
            loaded = name in self.plugins
            result[name] = {
                "enabled": True,
                "loaded": loaded,
                "description": pc.get("description", ""),
            }
        return result

    def toggle_plugin(self, name: str, enabled: bool) -> bool:
        if name not in self.config.get("plugins", {}):
            return False
        self.config["plugins"][name]["enabled"] = enabled
        save_config(self.config)
        if not enabled and name in self.plugins:
            info = self.plugins[name]
            shutdown_handler = getattr(info["module"], "on_shutdown", None)
            if shutdown_handler:
                try:
                    shutdown_handler()
                except Exception:
                    pass
            del self.plugins[name]
        elif enabled and name not in self.plugins:
            self.load_plugin(name)
        return True
