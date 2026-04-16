#!/usr/bin/env python3
import os
import subprocess
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from phantom_env import config_dir, load_system_config, resolve_model_path

class LocaleManager:
    def __init__(self):
        self.locale_dir = config_dir() / "locales"
        self.locale_dir.mkdir(parents=True, exist_ok=True)
        
    def set_locale(self, locale):
        locale_file = self.locale_dir / f"{locale}.json"
        if locale_file.exists():
            with open(locale_file) as f:
                json.load(f)
        
        os.environ["LANG"] = locale
        os.environ["LC_ALL"] = locale
        
    def install_locale(self, locale):
        subprocess.run(["locale-gen", locale], check=True)
        
    def list_available(self):
        result = subprocess.run(["locale", "-a"], capture_output=True, text=True)
        return result.stdout.strip().split("\n")

class AIManager:
    def __init__(self, model_path=None):
        config = load_system_config()
        self.model_path = str(resolve_model_path(model_path or config.get("ai", {}).get("model_path")))
        self.port = str(config.get("ai", {}).get("server_port", 8080))
        self.server_script = ROOT / "ai" / "llm" / "llm_server.py"
        
    def start(self):
        if not os.path.exists(self.model_path):
            print(f"Model not found at {self.model_path}")
            return False
            
        subprocess.Popen([
            "python3", str(self.server_script),
            self.model_path, self.port
        ])
        return True
        
    def stop(self):
        subprocess.run(["pkill", "-f", "llm_server.py"])
        
    def status(self):
        result = subprocess.run(["pgrep", "-f", "llm_server.py"], 
                             capture_output=True)
        return result.returncode == 0
