#!/usr/bin/env python3
import time
import sys
from pathlib import Path

try:
    import psutil
except ImportError:  # pragma: no cover
    psutil = None

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from phantom_env import config_dir, data_dir, resolve_model_path, user_state_dir

class PhantomAgent:
    def __init__(self):
        self.name = "PhantomAgent"
        self.version = "0.1.0"
        self.running = True
        self.services = {}
        
    def start(self):
        print(f"Starting {self.name} v{self.version}...")
        self._init_services()
        self._main_loop()
        
    def _init_services(self):
        self.services = {
            "privacy": self._check_privacy,
            "ai": self._check_ai,
            "vm": self._check_vm,
            "compatibility": self._check_compat
        }
        
        for name, check in self.services.items():
            try:
                check()
                print(f"  {name}: OK")
            except Exception as e:
                print(f"  {name}: FAILED - {e}")
                
    def _check_privacy(self):
        return (config_dir() / "privacy" / "config.json").exists()
        
    def _check_ai(self):
        return resolve_model_path().exists()
        
    def _check_vm(self):
        return (data_dir() / "vms").exists()
        
    def _check_compat(self):
        return user_state_dir().exists()
        
    def _main_loop(self):
        while self.running:
            self._monitor_system()
            time.sleep(30)
            
    def _monitor_system(self):
        if psutil is None:
            return

        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory().percent
        psutil.disk_usage('/').percent
        
        if cpu > 90 or mem > 90:
            print(f"WARNING: High usage - CPU: {cpu}%, MEM: {mem}%")
            
    def stop(self):
        print(f"Stopping {self.name}...")
        self.running = False

if __name__ == "__main__":
    agent = PhantomAgent()
    try:
        agent.start()
    except KeyboardInterrupt:
        agent.stop()
