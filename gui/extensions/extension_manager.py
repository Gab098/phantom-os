#!/usr/bin/env python3
# PhantomShell Extension Manager

import json
import shutil
import sys
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from phantom_env import opt_dir, user_state_dir

class ExtensionManager:
    def __init__(self):
        self.ext_dir = opt_dir() / "extensions"
        self.user_ext_dir = user_state_dir() / "extensions"
        self.ext_dir.mkdir(parents=True, exist_ok=True)
        self.user_ext_dir.mkdir(parents=True, exist_ok=True)
        
    def install(self, package_path):
        name = Path(package_path).stem
        
        if package_path.endswith('.zip'):
            with ZipFile(package_path, 'r') as z:
                z.extractall(self.ext_dir / name)
        else:
            shutil.copytree(package_path, self.ext_dir / name, dirs_exist_ok=True)
            
        manifest = self._load_manifest(self.ext_dir / name)
        if not manifest:
            return False, "Invalid extension (no manifest.json)"
            
        print(f"Installed: {manifest.get('name', name)}")
        return True, "OK"
        
    def uninstall(self, name):
        target = self.ext_dir / name
        if target.exists():
            shutil.rmtree(target)
            return True, "Uninstalled"
        return False, "Not found"
        
    def list_installed(self):
        results = []
        for ext in self.ext_dir.iterdir():
            manifest = self._load_manifest(ext)
            if manifest:
                results.append({
                    "name": manifest.get("name"),
                    "version": manifest.get("version"),
                    "author": manifest.get("author")
                })
        return results
        
    def enable(self, name):
        enabled_file = self.user_ext_dir / "enabled.json"
        enabled = []
        if enabled_file.exists():
            with open(enabled_file) as f:
                enabled = json.load(f)
        if name not in enabled:
            enabled.append(name)
            with open(enabled_file, "w") as f:
                json.dump(enabled, f)
                
    def disable(self, name):
        enabled_file = self.user_ext_dir / "enabled.json"
        if enabled_file.exists():
            with open(enabled_file) as f:
                enabled = json.load(f)
            enabled = [n for n in enabled if n != name]
            with open(enabled_file, "w") as f:
                json.dump(enabled, f)
                
    def _load_manifest(self, ext_path):
        manifest_path = ext_path / "manifest.json"
        if manifest_path.exists():
            with open(manifest_path) as f:
                return json.load(f)
        return None

if __name__ == "__main__":
    import sys
    mgr = ExtensionManager()
    
    if len(sys.argv) < 2:
        print("Usage: extmgr install|uninstall|list|enable|disable <name>")
        sys.exit(1)
        
    cmd = sys.argv[1]
    
    if cmd == "list":
        for ext in mgr.list_installed():
            print(f"  {ext['name']} v{ext['version']} by {ext['author']}")
    elif cmd == "install" and len(sys.argv) > 2:
        mgr.install(sys.argv[2])
    elif cmd == "uninstall" and len(sys.argv) > 2:
        mgr.uninstall(sys.argv[2])
    elif cmd == "enable" and len(sys.argv) > 2:
        mgr.enable(sys.argv[2])
    elif cmd == "disable" and len(sys.argv) > 2:
        mgr.disable(sys.argv[2])
