#!/usr/bin/env python3
import os
import sys
import shutil
import subprocess
from pathlib import Path

def install_wayland():
    pkgs = [
        "sway", "wayland", "wayland-protocols",
        "wl-clipboard", "grim", "slurp",
        "mako", "waybar", "wofi",
        "alacritty", "foot"
    ]
    print("Installing Wayland stack...")
    for pkg in pkgs:
        subprocess.run(["apt-get", "install", "-y", pkg], capture_output=True)

def install_tools():
    pkgs = [
        "git", "vim", "neovim", "htop", "btop",
        "curl", "wget", "rsync", "tmux",
        "zsh", "fish", "starship",
        "python3", "python3-pip", "nodejs", "npm"
    ]
    print("Installing tools...")
    for pkg in pkgs:
        subprocess.run(["apt-get", "install", "-y", pkg], capture_output=True)

def install_ai_deps():
    print("Installing AI dependencies...")
    pkgs = ["python3-pip", "python3-venv", "python3-dev", "libopenblas-dev"]
    subprocess.run(["apt-get", "install", "-y"] + pkgs, capture_output=True)
    
    subprocess.run([
        "pip3", "install", "torch", "--index-url", 
        "https://download.pytorch.org/whl/cpu"
    ], capture_output=True)
    
    subprocess.run([
        "pip3", "install", "transformers", "accelerate", 
        "sentencepiece", "peft"
    ], capture_output=True)

def install_privacy():
    pkgs = ["tor", "iptables", "ufw", "cryptsetup", "wireguard-tools"]
    print("Installing privacy tools...")
    for pkg in pkgs:
        subprocess.run(["apt-get", "install", "-y", pkg], capture_output=True)

def install_compat():
    pkgs = ["wine", "wine64", "flatpak", "snapd", "gdebi"]
    print("Installing compatibility tools...")
    for pkg in pkgs:
        subprocess.run(["apt-get", "install", "-y", pkg], capture_output=True)

def install_vm():
    pkgs = ["qemu-kvm", "libvirt-clients", "libvirt-daemon-system",
            "bridge-utils", "virt-manager", "virtinst"]
    print("Installing VM stack...")
    for pkg in pkgs:
        subprocess.run(["apt-get", "install", "-y", pkg], capture_output=True)
    subprocess.run(["systemctl", "enable", "libvirtd"], capture_output=True)

def main():
    print("PhantomOS Installation Script")
    print("===============================")
    
    install_wayland()
    install_tools()
    install_ai_deps()
    install_privacy()
    install_compat()
    install_vm()
    
    print("\nInstallation complete!")
    print("Run 'phantom-term' to start AI terminal")

if __name__ == "__main__":
    main()