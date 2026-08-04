"""Auto-discovery plugin registry for Parser Engine v2."""

from __future__ import annotations

import importlib
import logging
import pkgutil
from typing import Iterable

from parser_engine.v2.contracts import BaseParserV2

log = logging.getLogger(__name__)


class PluginRegistry:
    def __init__(self) -> None:
        self._plugins: dict[str, BaseParserV2] = {}

    def register(self, plugin: BaseParserV2) -> None:
        if not getattr(plugin, "parser_id", None):
            raise ValueError("Plugin missing parser_id")
        self._plugins[plugin.parser_id] = plugin
        log.debug("Registered parser plugin: %s", plugin.parser_id)

    def get(self, parser_id: str) -> BaseParserV2 | None:
        return self._plugins.get(parser_id)

    def all(self) -> list[BaseParserV2]:
        return list(self._plugins.values())

    def ids(self) -> list[str]:
        return sorted(self._plugins.keys())

    def discover(self, package_name: str = "parser_engine.v2.plugins") -> int:
        """Import all modules under plugins package and register PLUGIN / create_plugin."""
        count = 0
        try:
            pkg = importlib.import_module(package_name)
        except ImportError:
            return 0
        if not getattr(pkg, "__path__", None):
            return 0
        for modinfo in pkgutil.iter_modules(pkg.__path__, pkg.__name__ + "."):
            try:
                mod = importlib.import_module(modinfo.name)
            except Exception as exc:  # noqa: BLE001
                log.warning("Failed loading plugin module %s: %s", modinfo.name, exc)
                continue
            plugin = getattr(mod, "PLUGIN", None)
            if plugin is None and hasattr(mod, "create_plugin"):
                plugin = mod.create_plugin()
            if isinstance(plugin, BaseParserV2):
                self.register(plugin)
                count += 1
            elif isinstance(plugin, Iterable):
                for item in plugin:
                    if isinstance(item, BaseParserV2):
                        self.register(item)
                        count += 1
        # Optional entry points
        try:
            from importlib.metadata import entry_points

            eps = entry_points()
            selected = eps.select(group="parser_engine.v2_plugins") if hasattr(eps, "select") else []
            for ep in selected:
                try:
                    obj = ep.load()
                    plugin = obj() if callable(obj) and not isinstance(obj, BaseParserV2) else obj
                    if isinstance(plugin, BaseParserV2):
                        self.register(plugin)
                        count += 1
                except Exception as exc:  # noqa: BLE001
                    log.warning("Entry point plugin failed %s: %s", ep.name, exc)
        except Exception:
            pass
        return count


def default_registry() -> PluginRegistry:
    reg = PluginRegistry()
    reg.discover()
    return reg
