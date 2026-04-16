#!/bin/bash
set -euo pipefail
# PhantomOS initramfs generator — build a minimal initramfs from init.sh + modules

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
INITRAMFS_DIR="${PROJECT_ROOT}/build/initramfs"
OUTPUT="${PROJECT_ROOT}/build/initrd.img-phantomos"

echo "PhantomOS initramfs builder"
echo "==========================="

cleanup() {
    rm -rf "${INITRAMFS_DIR}"
}
trap cleanup EXIT

mkdir -p "${INITRAMFS_DIR}"/{bin,sbin,etc,proc,sys,dev,mnt/root,lib/modules,usr/bin,usr/sbin,usr/lib}

# --- Copy busybox (static) as the base userland ---
BUSYBOX="$(command -v busybox 2>/dev/null || echo /bin/busybox)"
if [[ -x "${BUSYBOX}" ]]; then
    cp "${BUSYBOX}" "${INITRAMFS_DIR}/bin/busybox"
    chroot "${INITRAMFS_DIR}" /bin/busybox --install -s /bin 2>/dev/null || true
else
    echo "WARNING: busybox not found — initramfs will rely on host binaries"
    for bin in sh mount umount switch_root modprobe mkdir; do
        src="$(command -v "${bin}" 2>/dev/null || true)"
        if [[ -n "${src}" ]]; then
            cp "${src}" "${INITRAMFS_DIR}/bin/"
        fi
    done
fi

# --- Copy cryptsetup for LUKS unlock ---
CRYPTSETUP="$(command -v cryptsetup 2>/dev/null || true)"
if [[ -n "${CRYPTSETUP}" ]]; then
    cp "${CRYPTSETUP}" "${INITRAMFS_DIR}/sbin/"
    # Copy required libraries
    for lib in $(ldd "${CRYPTSETUP}" 2>/dev/null | awk '/=>/ {print $3}'); do
        if [[ -f "${lib}" ]]; then
            mkdir -p "${INITRAMFS_DIR}/$(dirname "${lib}")"
            cp "${lib}" "${INITRAMFS_DIR}/${lib}"
        fi
    done
fi

# --- Copy kernel modules ---
KVER="${1:-$(uname -r)}"
MOD_DIR="/lib/modules/${KVER}"
if [[ -d "${MOD_DIR}" ]]; then
    echo "Copying kernel modules for ${KVER}..."
    MODULES=(
        dm-crypt xts aes-generic sha256_generic sha512_generic
        ext4 xfs btrfs
        virtio virtio_pci virtio_blk virtio_net virtio_scsi
        i915 amdgpu nouveau
        loop squashfs overlay
    )
    for mod in "${MODULES[@]}"; do
        mod_path="$(find "${MOD_DIR}" -name "${mod}.ko*" 2>/dev/null | head -1)"
        if [[ -n "${mod_path}" ]]; then
            rel="${mod_path#/lib/modules/}"
            dest="${INITRAMFS_DIR}/lib/modules/${rel}"
            mkdir -p "$(dirname "${dest}")"
            cp "${mod_path}" "${dest}"
        fi
    done
    # Copy modules.dep etc.
    for f in modules.dep modules.dep.bin modules.alias modules.alias.bin; do
        if [[ -f "${MOD_DIR}/${f}" ]]; then
            cp "${MOD_DIR}/${f}" "${INITRAMFS_DIR}/lib/modules/${KVER}/"
        fi
    done
else
    echo "WARNING: No modules found for kernel ${KVER}"
fi

# --- Copy init script ---
install -m 0755 "${PROJECT_ROOT}/boot/init.sh" "${INITRAMFS_DIR}/init"

echo "Building initramfs cpio archive..."
(cd "${INITRAMFS_DIR}" && find . | cpio -o -H newc 2>/dev/null | gzip -9 > "${OUTPUT}")

echo "initramfs created: ${OUTPUT} ($(du -h "${OUTPUT}" | cut -f1))"
