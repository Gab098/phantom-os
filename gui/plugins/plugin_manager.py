#!/usr/bin/env python3
"""PhantomShell Plugin Manager — discover, load, and manage GUI plugins."""

import importlib
import importlib.util
import json
import shutil
import sys
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from phantom_env import opt_dir, user_state_dir


class PluginManager:
    """Manage PhantomShell GUI plugins.

    Plugins live in directories that contain a ``plugin.json`` manifest::

        {
            "name": "my-plugin",
            "version": "1.0.0",
            "author": "...",
            "description": "...",
            "entry_point": "main.py",
            "permissions": ["ui.panel"]
        }
    """

    def __init__(self):
        self.system_dir = opt_dir() / "plugins"
        self.user_dir = user_state_dir() / "plugins"
        self.system_dir.mkdir(parents=True, exist_ok=True)
        self.user_dir.mkdir(parents=True, exist_ok=True)
        self._enabled_path = self.user_dir / "enabled.json"
        self._loaded: dict[str, object] = {}

    # ------------------------------------------------------------------
    # Install / Uninstall
    # ------------------------------------------------------------------

    def install(self, source: str | Path) -> tuple[bool, str]:
        """Install a plugin from a directory or a .zip archive."""
        source = Path(source)
        if source.suffix == ".zip":
            name = source.stem
            target = self.user_dir / name
            with ZipFile(source) as zf:
                zf.extractall(target)
        elif source.is_dir():
            name = source.name
            target = self.user_dir / name
            shutil.copytree(source, target, dirs_exist_ok=True)
        else:
            return False, f"Unsupported source: {source}"

        manifest = self._load_manifest(target)
        if manifest is None:
            shutil.rmtree(target, ignore_errors=True)
            return False, "Invalid plugin (missing plugin.json)"

        print(f"Installed plugin: {manifest.get('name', name)}")
        return True, "OK"

    def uninstall(self, name: str) -> tuple[bool, str]:
        """Remove a plugin by name."""
        for base in (self.user_dir, self.system_dir):
            target = base / name
            if target.exists():
                self.disable(name)
                shutil.rmtree(target)
                return True, "Uninstalled"
        return False, "Plugin not found"

    # ------------------------------------------------------------------
    # Enable / Disable
    # ------------------------------------------------------------------

    def enable(self, name: str) -> None:
        enabled = self._get_enabled()
        if name not in enabled:
            enabled.append(name)
            self._save_enabled(enabled)

    def disable(self, name: str) -> None:
        enabled = self._get_enabled()
        enabled = [n for n in enabled if n != name]
        self._save_enabled(enabled)
        self._loaded.pop(name, None)

    # ------------------------------------------------------------------
    # Load / Discover
    # ------------------------------------------------------------------

    def load_enabled(self) -> list[str]:
        """Load all enabled plugins and return their names."""
        loaded = []
        for name in self._get_enabled():
            try:
                self._load_plugin(name)
                loaded.append(name)
            except Exception as exc:
                print(f"Failed to load plugin '{name}': {exc}")
        return loaded

    def list_all(self) -> list[dict]:
        """List all discovered plugins with their manifests."""
        results = []
        seen: set[str] = set()
        for base in (self.system_dir, self.user_dir):
            if not base.exists():
                continue
            for entry in sorted(base.iterdir()):
                if not entry.is_dir() or entry.name in seen:
                    continue
                manifest = self._load_manifest(entry)
                if manifest:
                    seen.add(entry.name)
                    manifest["_dir"] = str(entry)
                    manifest["_enabled"] = entry.name in self._get_enabled()
                    results.append(manifest)
        return results

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _load_plugin(self, name: str) -> object:
        if name in self._loaded:
            return self._loaded[name]

        plugin_dir = self._find_plugin_dir(name)
        if plugin_dir is None:
            raise FileNotFoundError(f"Plugin '{name}' not found")

        manifest = self._load_manifest(plugin_dir)
        entry = manifest.get("entry_point", "main.py")
        entry_path = plugin_dir / entry

        spec = importlib.util.spec_from_file_location(f"phantom_plugin_{name}", entry_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load {entry_path}")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        self._loaded[name] = mod
        return mod

    def _find_plugin_dir(self, name: str) -> Path | None:
        for base in (self.user_dir, self.system_dir):
            candidate = base / name
            if candidate.is_dir():
                return candidate
        return None

    def _load_manifest(self, plugin_dir: Path) -> dict | None:
        manifest_path = plugin_dir / "plugin.json"
        if not manifest_path.exists():
            return None
        with manifest_path.open() as fh:
            return json.load(fh)

    def _get_enabled(self) -> list[str]:
        if self._enabled_path.exists():
            with self._enabled_path.open() as fh:
                return json.load(fh)
        return []

    def _save_enabled(self, enabled: list[str]) -> None:
        with self._enabled_path.open("w") as fh:
            json.dump(enabled, fh, indent=2)


if __name__ == "__main__":
    mgr = PluginManager()
    if len(sys.argv) < 2:
        print("Usage: plugin_manager.py install|uninstall|list|enable|disable <name>")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "list":
        for p in mgr.list_all():
            status = "✓" if p.get("_enabled") else "·"
            print(f"  {status} {p.get('name', '?')} v{p.get('version', '?')}")
    elif cmd == "install" and len(sys.argv) > 2:
        mgr.install(sys.argv[2])
    elif cmd == "uninstall" and len(sys.argv) > 2:
        mgr.uninstall(sys.argv[2])
    elif cmd == "enable" and len(sys.argv) > 2:
        mgr.enable(sys.argv[2])
    elif cmd == "disable" and len(sys.argv) > 2:
        mgr.disable(sys.argv[2])
