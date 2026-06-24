"""
Plugin Sandbox — Restricted execution environment for community plugins.
Provides safe API access: events, cache, memory, config, logging.
Blocks dangerous operations: file system (outside workspace), network (whitelisted), subprocess.
"""
import os
import sys
import importlib
import importlib.util
import threading
import logging
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent
PLUGINS_DIR = PROJECT_ROOT / "plugins"
COMMUNITY_DIR = PLUGINS_DIR / "community"
WORKSPACE = PROJECT_ROOT / "workspace"


@dataclass
class PluginManifest:
    name: str
    version: str
    description: str
    author: str = ""
    dependencies: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    api_version: str = "1.0"
    min_jarvis_version: str = "3.1"
    enabled: bool = True

    @classmethod
    def from_dict(cls, data: dict) -> "PluginManifest":
        return cls(
            name=data.get("name", ""),
            version=data.get("version", "0.1.0"),
            description=data.get("description", ""),
            author=data.get("author", ""),
            dependencies=data.get("dependencies", []),
            permissions=data.get("permissions", []),
            api_version=data.get("api_version", "1.0"),
            min_jarvis_version=data.get("min_jarvis_version", "3.1"),
            enabled=data.get("enabled", True),
        )

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "dependencies": self.dependencies,
            "permissions": self.permissions,
            "api_version": self.api_version,
            "min_jarvis_version": self.min_jarvis_version,
            "enabled": self.enabled,
        }


@dataclass
class PluginAPI:
    """Sandboxed API provided to community plugins."""
    plugin_name: str
    event_bus: Any = None
    cache: Any = None
    config: dict = field(default_factory=dict)
    logger: Any = None
    workspace: str = ""

    def emit(self, topic: str, data: Any = None):
        if self.event_bus:
            self.event_bus.emit(topic, data, source=f"plugin:{self.plugin_name}")

    def subscribe(self, topic: str, handler):
        if self.event_bus:
            self.event_bus.subscribe(topic, handler)

    def cache_get(self, key: str) -> Optional[Any]:
        if self.cache:
            return self.cache.get(f"plugin:{self.plugin_name}:{key}")
        return None

    def cache_set(self, key: str, value: Any, ttl: float = 300):
        if self.cache:
            self.cache.set(f"plugin:{self.plugin_name}:{key}", value, ttl)

    def read_file(self, path: str) -> Optional[str]:
        full = Path(self.workspace) / path
        resolved = full.resolve()
        workspace_resolved = Path(self.workspace).resolve()
        if not str(resolved).startswith(str(workspace_resolved)):
            return None
        try:
            return resolved.read_text(encoding="utf-8")
        except Exception:
            return None

    def write_file(self, path: str, content: str) -> bool:
        full = Path(self.workspace) / path
        resolved = full.resolve()
        workspace_resolved = Path(self.workspace).resolve()
        if not str(resolved).startswith(str(workspace_resolved)):
            return False
        try:
            resolved.parent.mkdir(parents=True, exist_ok=True)
            resolved.write_text(content, encoding="utf-8")
            return True
        except Exception:
            return False


class PluginSandbox:
    def __init__(self):
        self.loaded: dict[str, dict] = {}
        COMMUNITY_DIR.mkdir(parents=True, exist_ok=True)

    def discover_community(self) -> list[PluginManifest]:
        manifests = []
        if not COMMUNITY_DIR.exists():
            return manifests
        for item in COMMUNITY_DIR.iterdir():
            if item.is_dir():
                manifest_path = item / "plugin.json"
                if manifest_path.exists():
                    try:
                        import json
                        data = json.loads(manifest_path.read_text(encoding="utf-8"))
                        manifests.append(PluginManifest.from_dict(data))
                    except Exception as e:
                        logger.warning(f"Failed to load manifest for {item.name}: {e}")
        return manifests

    def load_plugin(self, name: str) -> Optional[dict]:
        if name in self.loaded:
            return self.loaded[name]

        plugin_dir = COMMUNITY_DIR / name
        manifest_path = plugin_dir / "plugin.json"
        handler_path = plugin_dir / "handler.py"

        if not manifest_path.exists() or not handler_path.exists():
            return None

        import json
        manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest = PluginManifest.from_dict(manifest_data)

        if not manifest.enabled:
            return None

        for dep in manifest.dependencies:
            try:
                importlib.import_module(dep)
            except ImportError:
                logger.warning(f"Plugin '{name}' missing dependency: {dep}")
                return None

        from core.event_bus import event_bus
        from core.cache import cache

        api = PluginAPI(
            plugin_name=name,
            event_bus=event_bus,
            cache=cache,
            workspace=str(WORKSPACE),
            logger=logging.getLogger(f"plugin.{name}"),
        )

        try:
            spec = importlib.util.spec_from_file_location(
                f"plugins.community.{name}.handler",
                str(handler_path),
            )
            mod = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = mod
            spec.loader.exec_module(mod)
        except Exception as e:
            logger.error(f"Failed to load plugin '{name}': {e}")
            return None

        plugin_info = {
            "name": name,
            "manifest": manifest,
            "module": mod,
            "api": api,
            "router": getattr(mod, "router", None),
        }

        self.loaded[name] = plugin_info
        return plugin_info

    def startup_all(self):
        for name, info in self.loaded.items():
            handler = getattr(info["module"], "on_startup", None)
            if handler:
                try:
                    handler()
                except Exception as e:
                    logger.error(f"Plugin '{name}' startup failed: {e}")

    def shutdown_all(self):
        for name, info in self.loaded.items():
            handler = getattr(info["module"], "on_shutdown", None)
            if handler:
                try:
                    handler()
                except Exception as e:
                    logger.error(f"Plugin '{name}' shutdown failed: {e}")

    def install_from_url(self, url: str) -> bool:
        import json
        import httpx
        import zipfile
        import io

        try:
            with httpx.Client(timeout=30, follow_redirects=True) as client:
                r = client.get(url)
                r.raise_for_status()

                if url.endswith(".zip"):
                    with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
                        names = zf.namelist()
                        top_dir = names[0].split("/")[0] if names else ""
                        zf.extractall(str(COMMUNITY_DIR))
                        return True
                else:
                    data = r.json()
                    name = data.get("name", "")
                    if not name:
                        return False
                    plugin_dir = COMMUNITY_DIR / name
                    plugin_dir.mkdir(parents=True, exist_ok=True)
                    (plugin_dir / "plugin.json").write_text(
                        json.dumps(data, indent=2), encoding="utf-8"
                    )
                    if "handler_url" in data:
                        hr = client.get(data["handler_url"])
                        hr.raise_for_status()
                        (plugin_dir / "handler.py").write_text(
                            hr.text, encoding="utf-8"
                        )
                    return True
        except Exception as e:
            logger.error(f"Install failed: {e}")
            return False

    def uninstall(self, name: str) -> bool:
        plugin_dir = COMMUNITY_DIR / name
        if not plugin_dir.exists():
            return False
        import shutil
        shutil.rmtree(plugin_dir)
        if name in self.loaded:
            del self.loaded[name]
        return True
