#!/bin/bash
set -euo pipefail

# PhantomOS Boot Process
# Stage 1: Kernel initialization (initramfs /init)

export PATH=/bin:/sbin:/usr/bin:/usr/sbin

mount -t proc proc /proc
mount -t sysfs sysfs /sys
mount -t devtmpfs devtmpfs /dev
mkdir -p /dev/pts
mount -t devpts devpts /dev/pts
mkdir -p /mnt/root /mnt/live /mnt/overlay /mnt/workdir

echo ""
echo "  ██████╗ ██╗  ██╗ █████╗ ███╗   ██╗████████╗ ██████╗ ███╗   ███╗"
echo "  ██╔══██╗██║  ██║██╔══██╗████╗  ██║╚══██╔══╝██╔═══██╗████╗ ████║"
echo "  ██████╔╝███████║███████║██╔██╗ ██║   ██║   ██║   ██║██╔████╔██║"
echo "  ██╔═══╝ ██╔══██║██╔══██║██║╚██╗██║   ██║   ██║   ██║██║╚██╔╝██║"
echo "  ██║     ██║  ██║██║  ██║██║ ╚████║   ██║   ╚██████╔╝██║ ╚═╝ ██║"
echo "  ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝    ╚═════╝ ╚═╝     ╚═╝"
echo "  PhantomOS v0.1 — Initializing..."
echo ""

# --- Load kernel modules ---
echo "[boot] Loading kernel modules..."
modprobe -a \
    dm-crypt xts aes-generic \
    ext4 xfs btrfs \
    virtio virtio_pci virtio_blk virtio_net virtio_scsi \
    i915 amdgpu nouveau \
    loop squashfs overlay \
    2>/dev/null || true

# --- Detect boot mode ---
BOOT_MODE="disk"
CMDLINE="$(cat /proc/cmdline)"
if echo "$CMDLINE" | grep -q "phantom.live"; then
    BOOT_MODE="live"
fi

if [ "$BOOT_MODE" = "live" ]; then
    # --- Live ISO boot with OverlayFS ---
    echo "[boot] Live ISO mode — mounting squashfs + overlay..."

    # Find the squashfs image (could be on CD or USB)
    for dev in /dev/sr0 /dev/sda1 /dev/sdb1 /dev/nvme0n1p1; do
        if [ -b "$dev" ]; then
            mount -o ro "$dev" /mnt/live 2>/dev/null || continue
            if [ -f /mnt/live/filesystem.squashfs ]; then
                echo "[boot] Found squashfs on $dev"
                break
            fi
            umount /mnt/live 2>/dev/null || true
        fi
    done

    if [ ! -f /mnt/live/filesystem.squashfs ]; then
        echo "[boot] ERROR: filesystem.squashfs not found!"
        exec /bin/sh
    fi

    # Mount the squashfs as the lower read-only layer
    mkdir -p /mnt/sqfs
    mount -t squashfs -o loop,ro /mnt/live/filesystem.squashfs /mnt/sqfs

    # Create a tmpfs overlay for writes
    mount -t tmpfs tmpfs /mnt/overlay
    mkdir -p /mnt/overlay/upper /mnt/overlay/work

    # Build the overlayfs root
    mount -t overlay overlay \
        -o lowerdir=/mnt/sqfs,upperdir=/mnt/overlay/upper,workdir=/mnt/overlay/work \
        /mnt/root

else
    # --- Standard disk boot with LUKS ---
    echo "[boot] Disk boot mode..."

    echo "[boot] Setting up encrypted volumes..."
    if [ -b /dev/sda2 ]; then
        cryptsetup luksOpen /dev/sda2 cryptroot 2>/dev/null || true
    fi

    echo "[boot] Mounting root filesystem..."
    if [ -b /dev/mapper/cryptroot ]; then
        mount -o ro /dev/mapper/cryptroot /mnt/root
    else
        mount -o ro /dev/sda3 /mnt/root 2>/dev/null || \
        mount -o ro /dev/nvme0n1p3 /mnt/root 2>/dev/null || true
    fi
fi

# --- Verify we have a root ---
if [ ! -d /mnt/root/sbin ]; then
    echo "[boot] ERROR: Root filesystem not found!"
    echo "[boot] Dropping to emergency shell..."
    exec /bin/sh
fi

# --- Start early services ---
echo "[boot] Starting privacy services..."
if [ -f /mnt/root/usr/bin/tor ]; then
    chroot /mnt/root tor --defaults-torrc /usr/share/tor/torrc-defaults \
        -f /etc/tor/torrc 2>/dev/null &
fi

echo "[boot] Starting AI services..."
if [ -f /mnt/root/opt/phantom/ai/llm/llm_server.py ]; then
    chroot /mnt/root /opt/phantom/ai/llm/start.sh 2>/dev/null &
fi

# --- Switch root ---
echo "[boot] Switching to root filesystem..."
umount /proc /sys /dev/pts 2>/dev/null || true
exec switch_root /mnt/root /sbin/init
