#!/usr/bin/env python3
import os
import subprocess
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from phantom_env import opt_dir, user_state_dir


class CompatibilityLayer:
    def __init__(self):
        self.prefixes = user_state_dir() / "prefixes"
        self.prefixes.mkdir(parents=True, exist_ok=True)
        
    def wine_setup(self, prefix_name="default"):
        prefix_path = self.prefixes / prefix_name
        prefix_path.mkdir(parents=True, exist_ok=True)
        
        env = os.environ.copy()
        env["WINEPREFIX"] = str(prefix_path)
        
        wine_dir = prefix_path / "drive_c"
        wine_dir.mkdir(exist_ok=True)
        
        print(f"Wine prefix created: {prefix_path}")
        return str(prefix_path)
        
    def run_exe(self, exe_path, prefix="default"):
        prefix_path = self.prefixes / prefix
        
        env = os.environ.copy()
        env["WINEPREFIX"] = str(prefix_path)
        
        result = subprocess.run(
            ["wine", exe_path],
            env=env,
            capture_output=True,
            text=True
        )
        return result.returncode == 0
        
    def proton_setup(self, app_name):
        proton_dir = self.prefixes / "proton" / app_name
        proton_dir.mkdir(parents=True, exist_ok=True)
        
        proton_cfg = {
            "name": app_name,
            "proton_version": "GE-Proton8",
            "compat_dir": str(proton_dir)
        }
        
        cfg_file = proton_dir / "config.json"
        with open(cfg_file, "w") as f:
            json.dump(proton_cfg, f, indent=2)
            
        return str(proton_dir)
        
    def install_deb(self, deb_path):
        result = subprocess.run(
            ["dpkg", "-i", deb_path],
            capture_output=True
        )
        
        if result.returncode != 0:
            subprocess.run(["apt-get", "-f", "install", "-y"], check=False)
            
        return result.returncode == 0
        
    def install_flatpak(self, flatpak_id):
        subprocess.run([
            "flatpak", "install", "-y", flatpak_id
        ], check=True)
        
    def install_appimage(self, appimage_path):
        dest = opt_dir() / "applications"
        dest.mkdir(parents=True, exist_ok=True)
        
        target = dest / Path(appimage_path).name
        shutil.copy(appimage_path, target)
        target.chmod(0o755)
        
        print(f"AppImage installed to: {target}")
        
    def install_snap(self, snap_name):
        subprocess.run([
            "snap", "install", snap_name
        ], check=True)
        
    def create_launcher(self, name, command, icon=None, category="Utility"):
        desktop_file = user_state_dir() / "applications" / f"{name}.desktop"
        desktop_file.parent.mkdir(parents=True, exist_ok=True)
        
        content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name={name}
Exec={command}
"""
        if icon:
            content += f"Icon={icon}\n"
        content += f"Categories={category};\n"
        
        desktop_file.write_text(content)
        print(f"Launcher created: {desktop_file}")

if __name__ == "__main__":
    c = CompatibilityLayer()
    c.wine_setup("gaming")
