#!/bin/bash
set -euo pipefail
# PhantomOS Quick Setup

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "PhantomOS Setup Wizard"
echo "======================"

# Check root
if [ "$EUID" -ne 0 ]; then
    echo "Run as root (sudo)"
    exit 1
fi

echo "[1/5] Installing base packages..."
apt-get update
apt-get install -y sway wayland-protocols waybar wofi alacritty mako grim slurp wl-clipboard

echo "[2/5] Installing AI dependencies..."
apt-get install -y python3-pip python3-venv python3-dev libopenblas-dev
python3 -m pip install --break-system-packages transformers llama-cpp-python

echo "[3/5] Installing privacy tools..."
apt-get install -y tor iptables ufw cryptsetup

echo "[4/5] Installing compatibility layer..."
apt-get install -y wine flatpak

echo "[5/5] Installing VM stack..."
apt-get install -y qemu-kvm libvirt-daemon-system virt-manager

# Copy configs
install -d /root/.config/sway /root/.config/waybar
install -m 0644 "${PROJECT_ROOT}/gui/wayland/configs/sway.config" /root/.config/sway/config
mkdir -p ~/.config/waybar
cp "${PROJECT_ROOT}/gui/wayland/configs/waybar/"* /root/.config/waybar/
install -d /etc/phantom
install -m 0644 "${PROJECT_ROOT}/system/config/config.json" /etc/phantom/config.json

echo ""
echo "Setup complete!"
echo "Run 'sway' to start GUI"
echo "Run 'phantom-term' for AI terminal"
