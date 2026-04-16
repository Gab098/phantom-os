#!/usr/bin/env python3
"""PhantomOS Wine/Proton Manager — manage Wine prefixes, DXVK, and Proton runners."""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from phantom_env import user_state_dir, opt_dir


class WineManager:
    """Create, configure, and run Wine/Proton prefixes."""

    def __init__(self):
        self.prefix_root = user_state_dir() / "prefixes"
        self.prefix_root.mkdir(parents=True, exist_ok=True)
        self.runners_dir = opt_dir() / "runners"
        self.runners_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Prefix management
    # ------------------------------------------------------------------

    def create_prefix(self, name: str, *, arch: str = "win64") -> Path:
        """Create a new Wine prefix."""
        prefix = self.prefix_root / name
        prefix.mkdir(parents=True, exist_ok=True)

        env = os.environ.copy()
        env["WINEPREFIX"] = str(prefix)
        env["WINEARCH"] = arch

        subprocess.run(["wineboot", "--init"], env=env, capture_output=True)

        cfg = {"name": name, "arch": arch, "dxvk": False, "runner": "wine"}
        self._save_config(name, cfg)

        print(f"Wine prefix created: {prefix} ({arch})")
        return prefix

    def delete_prefix(self, name: str) -> bool:
        """Delete a Wine prefix."""
        prefix = self.prefix_root / name
        if prefix.exists():
            shutil.rmtree(prefix)
            print(f"Deleted prefix: {name}")
            return True
        print(f"Prefix not found: {name}")
        return False

    def list_prefixes(self) -> list[dict]:
        """List all configured prefixes."""
        results = []
        for entry in sorted(self.prefix_root.iterdir()):
            if entry.is_dir():
                cfg = self._load_config(entry.name)
                results.append({"name": entry.name, **cfg})
        return results

    # ------------------------------------------------------------------
    # DXVK
    # ------------------------------------------------------------------

    def install_dxvk(self, prefix_name: str) -> bool:
        """Install DXVK into a prefix for Vulkan-translated DirectX."""
        prefix = self.prefix_root / prefix_name
        env = os.environ.copy()
        env["WINEPREFIX"] = str(prefix)

        result = subprocess.run(
            ["setup_dxvk", "install"],
            env=env,
            capture_output=True,
        )
        if result.returncode == 0:
            cfg = self._load_config(prefix_name)
            cfg["dxvk"] = True
            self._save_config(prefix_name, cfg)
            print(f"DXVK installed in prefix: {prefix_name}")
            return True
        print(f"DXVK install failed: {result.stderr.decode()}")
        return False

    def remove_dxvk(self, prefix_name: str) -> bool:
        """Remove DXVK from a prefix."""
        prefix = self.prefix_root / prefix_name
        env = os.environ.copy()
        env["WINEPREFIX"] = str(prefix)

        result = subprocess.run(
            ["setup_dxvk", "uninstall"],
            env=env,
            capture_output=True,
        )
        if result.returncode == 0:
            cfg = self._load_config(prefix_name)
            cfg["dxvk"] = False
            self._save_config(prefix_name, cfg)
        return result.returncode == 0

    # ------------------------------------------------------------------
    # Runner selection (Wine vs Proton-GE vs custom)
    # ------------------------------------------------------------------

    def set_runner(self, prefix_name: str, runner: str) -> None:
        """Set the Wine runner for a prefix ('wine', 'proton-ge', or a custom path)."""
        cfg = self._load_config(prefix_name)
        cfg["runner"] = runner
        self._save_config(prefix_name, cfg)
        print(f"Runner for '{prefix_name}' set to: {runner}")

    def list_runners(self) -> list[str]:
        """List available runners."""
        runners = ["wine"]
        if shutil.which("proton"):
            runners.append("proton")
        for entry in self.runners_dir.iterdir():
            if entry.is_dir():
                runners.append(entry.name)
        return runners

    # ------------------------------------------------------------------
    # Run
    # ------------------------------------------------------------------

    def run(self, exe_path: str, prefix_name: str = "default", *, args: list[str] | None = None) -> int:
        """Run an .exe inside a Wine prefix."""
        prefix = self.prefix_root / prefix_name
        cfg = self._load_config(prefix_name)
        runner = cfg.get("runner", "wine")

        env = os.environ.copy()
        env["WINEPREFIX"] = str(prefix)

        cmd = [runner, exe_path] + (args or [])
        result = subprocess.run(cmd, env=env)
        return result.returncode

    # ------------------------------------------------------------------
    # Winetricks
    # ------------------------------------------------------------------

    def winetricks(self, prefix_name: str, verbs: list[str]) -> bool:
        """Run winetricks verbs inside a prefix."""
        prefix = self.prefix_root / prefix_name
        env = os.environ.copy()
        env["WINEPREFIX"] = str(prefix)

        result = subprocess.run(
            ["winetricks"] + verbs,
            env=env,
            capture_output=True,
        )
        return result.returncode == 0

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _config_path(self, name: str) -> Path:
        return self.prefix_root / name / "phantom-wine.json"

    def _save_config(self, name: str, cfg: dict) -> None:
        path = self._config_path(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w") as fh:
            json.dump(cfg, fh, indent=2)

    def _load_config(self, name: str) -> dict:
        path = self._config_path(name)
        if path.exists():
            with path.open() as fh:
                return json.load(fh)
        return {"name": name, "arch": "win64", "dxvk": False, "runner": "wine"}


if __name__ == "__main__":
    mgr = WineManager()
    print("Prefixes:", mgr.list_prefixes())
    print("Runners:", mgr.list_runners())
