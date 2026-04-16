# PhantomOS Installation Guide

## System Requirements

| Component | Minimum    | Recommended |
|-----------|-----------|-------------|
| CPU       | x86-64    | x86-64      |
| RAM       | 4 GB      | 8 GB        |
| Storage   | 20 GB     | 40 GB       |
| GPU       | Intel/AMD | NVIDIA (for GPU passthrough) |

## Option 1: Live USB

### Create the ISO

```bash
# Clone the repository
git clone https://github.com/phantomos/phantomos.git
cd phantomos

# Install build dependencies
make deps

# Build the ISO (requires root)
sudo make build
```

The ISO will be at `iso/PhantomOS-v0.1.iso`.

### Write to USB

```bash
sudo ./build/create-usb.sh /dev/sdX iso/PhantomOS-v0.1.iso
```

> **WARNING**: Replace `/dev/sdX` with your actual USB device. All data on the device will be destroyed.

### Boot

1. Insert the USB and reboot
2. Select **PhantomOS (Live ISO)** from the GRUB menu
3. The system boots into a full desktop with OverlayFS (changes are lost on reboot)

## Option 2: Install to Disk

### From the Live Environment

1. Boot from the Live USB
2. Open a terminal (`Super+Return`)
3. Run the installer:

```bash
sudo /opt/phantom/system/scripts/install.sh
sudo /opt/phantom/system/config/post-install.sh
```

### LUKS Encryption (Recommended)

During installation, encrypt your root partition:

```bash
# Format with LUKS
sudo cryptsetup luksFormat /dev/sda2

# Open the encrypted volume
sudo cryptsetup open /dev/sda2 cryptroot

# Create filesystem
sudo mkfs.ext4 /dev/mapper/cryptroot

# Mount and install
sudo mount /dev/mapper/cryptroot /mnt
```

## Option 3: Virtual Machine

### QEMU/KVM

```bash
# Create a disk image
qemu-img create -f qcow2 phantomos.qcow2 20G

# Boot from ISO
qemu-system-x86_64 \
    -enable-kvm \
    -m 4096 \
    -cpu host \
    -smp 2 \
    -cdrom iso/PhantomOS-v0.1.iso \
    -drive file=phantomos.qcow2,format=qcow2 \
    -boot d
```

### VirtualBox

1. Create a new VM (Linux → Debian 64-bit)
2. Allocate 4 GB RAM, 2 CPUs
3. Attach `PhantomOS-v0.1.iso` as optical drive
4. Boot and install

## Post-Install

After first boot, the system will:

1. Start the Sway Wayland compositor  
2. Launch `phantom-agent` (system daemon)
3. Enable the firewall (default deny incoming)
4. Start Tor for privacy routing

### First Steps

```bash
# Launch the AI terminal
phantom-term

# Check system status
python3 /opt/phantom/system/base/phantom_base.py

# Change your password
passwd

# Set your locale
sudo localectl set-locale LANG=it_IT.UTF-8
```

## Development Setup (No Root Required)

```bash
make validate     # Check all source files
make dev-setup    # Create Python virtualenv
make smoke        # Test LLM server + terminal
make test         # Run unit tests
make bundle       # Create portable tarball
```
