#!/usr/bin/env python3
import subprocess
import json
import time
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from phantom_env import data_dir


class VMManager:
    def __init__(self):
        self.vm_dir = data_dir() / "vms"
        self.vm_dir.mkdir(parents=True, exist_ok=True)
        self.libvirt_dir = Path("/etc/libvirt")
        
    def create_vm(self, name, memory=4096, cpus=2, disk_size=20, iso=None, bridge="default"):
        vm_path = self.vm_dir / name
        vm_path.mkdir(parents=True, exist_ok=True)
        
        disk_path = vm_path / f"{name}.qcow2"
        
        subprocess.run([
            "qemu-img", "create", "-f", "qcow2",
            str(disk_path), f"{disk_size}G"
        ], check=True)
        
        cmd = [
            "virt-install",
            "--name", name,
            "--memory", str(memory),
            "--vcpus", str(cpus),
            "--disk", f"path={disk_path},format=qcow2",
            "--os-variant", "generic",
            "--network", f"bridge={bridge}",
            "--graphics", "spice",
            "--noautoconsole"
        ]
        
        if iso:
            cmd.extend(["--cdrom", iso])
            
        subprocess.run(cmd, check=True)
        
        self._save_vm_config(name, {
            "memory": memory,
            "cpus": cpus,
            "disk": str(disk_path),
            "iso": iso,
            "status": "stopped"
        })
        
        print(f"VM '{name}' created successfully")
        
    def quickboot_snapshot(self, vm_name):
        snapshot_name = f"{vm_name}_quickboot"
        
        subprocess.run([
            "virsh", "snapshot-create-as", vm_name,
            "--name", snapshot_name,
            "--atomic"
        ], check=True)
        
        print(f"QuickBoot snapshot created: {snapshot_name}")
        
    def start_vm(self, vm_name, quickboot=False):
        if quickboot:
            snapshot_name = f"{vm_name}_quickboot"
            try:
                subprocess.run([
                    "virsh", "revert", vm_name, snapshot_name
                ], check=True, capture_output=True)
            except subprocess.CalledProcessError:
                pass
                
        subprocess.run(["virsh", "start", vm_name], check=True)
        self._update_status(vm_name, "running")
        
    def start_gui(self, vm_name):
        subprocess.run([
            "virt-manager", "--connect", "qemu:///system",
            "--show-domain-visual", vm_name
        ], check=False)
        
    def stop_vm(self, vm_name):
        subprocess.run(["virsh", "shutdown", vm_name], check=False)
        time.sleep(5)
        subprocess.run(["virsh", "destroy", vm_name], check=False)
        self._update_status(vm_name, "stopped")
        
    def list_vms(self):
        result = subprocess.run(
            ["virsh", "list", "--all", "--name"],
            capture_output=True, text=True, check=True
        )
        
        vms = []
        for line in result.stdout.strip().split('\n'):
            if line:
                vms.append(line)
                
        return vms
        
    def gpu_passthrough(self, vm_name, gpu_bdf):
        self._load_vm_config(vm_name)
        
        hostdev = f"--hostdev pci_{gpu_bdf.replace(':', '_').replace('.', '_')}"
        
        subprocess.run([
            "virsh", "detach-device", vm_name, hostdev
        ], capture_output=True)
        
        print(f"GPU passthrough configured for {vm_name}")
        
    def _save_vm_config(self, name, config):
        config_file = self.vm_dir / name / "config.json"
        with open(config_file, "w") as f:
            json.dump(config, f, indent=2)
            
    def _load_vm_config(self, name):
        config_file = self.vm_dir / name / "config.json"
        if config_file.exists():
            with open(config_file) as f:
                return json.load(f)
        return {}
        
    def _update_status(self, name, status):
        config = self._load_vm_config(name)
        config["status"] = status
        self._save_vm_config(name, config)

if __name__ == "__main__":
    vm = VMManager()
    print("Available VMs:", vm.list_vms())
