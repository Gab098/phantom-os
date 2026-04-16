#!/bin/bash
# PhantomOS Live USB Creator

if [ -z "$1" ]; then
    echo "Usage: $0 <device> [iso_path]"
    echo "Example: $0 /dev/sdb /path/to/PhantomOS.iso"
    exit 1
fi

DEVICE="$1"
ISO="${2:-./iso/PhantomOS-v0.1.iso}"

echo "PhantomOS USB Creator"
echo "====================="
echo "Device: $DEVICE"
echo "ISO: $ISO"
echo ""
echo "WARNING: This will DESTROY all data on $DEVICE"
read -p "Continue? (y/n): " confirm

if [ "$confirm" != "y" ]; then
    echo "Aborted."
    exit 1
fi

# Unmount
umount ${DEVICE}* 2>/dev/null

# Partition
parted -s $DEVICE mklabel gpt
parted -s $DEVICE mkpart primary fat32 1MiB 512MiB
parted -s $DEVICE set 1 esp on
parted -s $DEVICE mkpart primary ext4 512MiB 100%

# Format
mkfs.fat -F32 ${DEVICE}1
mkfs.ext4 -F ${DEVICE}2

# Mount
mkdir -p /mnt/usb
mount ${DEVICE}2 /mnt/usb

# Copy ISO contents
mount -o loop "$ISO" /mnt/iso
cp -r /mnt/iso/* /mnt/usb/

# Install GRUB
grub-install --target=x86_64-efi --efi-directory=/mnt/usb --boot-directory=/mnt/usb/boot

# Cleanup
umount /mnt/iso
umount /mnt/usb

echo "Done! USB ready."