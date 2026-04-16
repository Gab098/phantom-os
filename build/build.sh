#!/bin/bash
set -euo pipefail

echo "PhantomOS Build System v0.1"
echo "============================"

# Configuration
ARCH="amd64"
SUITE="stable"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
WORKDIR="${PROJECT_ROOT}/build"
OUTDIR="${PROJECT_ROOT}/iso"
ROOTFS_DIR="${WORKDIR}/rootfs"
ISO_TREE="${WORKDIR}/iso"
ISO_NAME="PhantomOS-v0.1.iso"
BUNDLE_NAME="PhantomOS-devkit-v0.1.tar.gz"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

check_deps() {
    log_info "Checking build dependencies..."
    local deps=(debootstrap mksquashfs xorriso grub-mkrescue)
    local missing=0
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            log_warn "Missing: $dep"
            missing=1
        fi
    done
    return "$missing"
}

validate_sources() {
    log_info "Validating source tree..."
    local required=(
        "${PROJECT_ROOT}/README.md"
        "${PROJECT_ROOT}/docs/SPEC.md"
        "${PROJECT_ROOT}/system/config/config.json"
        "${PROJECT_ROOT}/boot/grub/grub.cfg"
        "${PROJECT_ROOT}/boot/init.sh"
        "${PROJECT_ROOT}/gui/wayland/configs/sway.config"
        "${PROJECT_ROOT}/gui/wayland/configs/waybar/config.jsonc"
        "${PROJECT_ROOT}/gui/wayland/configs/waybar/style.css"
        "${PROJECT_ROOT}/gui/wayland/configs/alacritty.toml"
        "${PROJECT_ROOT}/gui/wayland/configs/wofi/style.css"
        "${PROJECT_ROOT}/gui/wayland/configs/mako/config"
        "${PROJECT_ROOT}/gui/themes/mint.json"
        "${PROJECT_ROOT}/gui/themes/phantom-dark.json"
        "${PROJECT_ROOT}/gui/themes/phantom-light.json"
        "${PROJECT_ROOT}/system/config/zshrc"
        "${PROJECT_ROOT}/system/config/starship.toml"
        "${PROJECT_ROOT}/system/config/phantom-agent.service"
        "${PROJECT_ROOT}/system/config/phantom-ai.service"
        "${PROJECT_ROOT}/system/config/phantom-privacy.service"
        "${PROJECT_ROOT}/system/config/phantom-vm.service"
        "${PROJECT_ROOT}/system/config/greetd.toml"
        "${PROJECT_ROOT}/system/config/pipewire.conf"
        "${PROJECT_ROOT}/system/config/pipewire-pulse.conf"
        "${PROJECT_ROOT}/gui/wayland/configs/gtk-3.0/settings.ini"
        "${PROJECT_ROOT}/gui/wayland/configs/qt5ct/qt5ct.conf"
        "${PROJECT_ROOT}/gui/wayland/configs/swaylock/config"
        "${PROJECT_ROOT}/boot/plymouth/phantom.plymouth"
        "${PROJECT_ROOT}/boot/plymouth/phantom.script"
        "${PROJECT_ROOT}/privacy/firewall/sysctl-hardened.conf"
        "${PROJECT_ROOT}/privacy/tools/apparmor/usr.lib.firefox"
        "${PROJECT_ROOT}/privacy/tools/apparmor/phantom-sandbox"
        "${PROJECT_ROOT}/kernel/config"
        "${PROJECT_ROOT}/system/config/phantom-update.timer"
        "${PROJECT_ROOT}/system/config/phantom-update.service"
        "${PROJECT_ROOT}/system/config/phantom-cleanup.timer"
        "${PROJECT_ROOT}/system/config/phantom-cleanup.service"
        "${PROJECT_ROOT}/requirements.txt"
    )

    local missing=0
    for file in "${required[@]}"; do
        if [[ ! -e "${file}" ]]; then
            log_error "Required file missing: ${file}"
            missing=1
        fi
    done

    python3 -m compileall \
        "${PROJECT_ROOT}/ai" \
        "${PROJECT_ROOT}/compatibility" \
        "${PROJECT_ROOT}/gui" \
        "${PROJECT_ROOT}/privacy" \
        "${PROJECT_ROOT}/system" \
        "${PROJECT_ROOT}/phantom_env.py" >/dev/null

    bash -n "${PROJECT_ROOT}/build/build.sh"
    bash -n "${PROJECT_ROOT}/build/setup.sh"
    bash -n "${PROJECT_ROOT}/build/create-usb.sh"
    bash -n "${PROJECT_ROOT}/boot/init.sh"
    bash -n "${PROJECT_ROOT}/boot/mkinitramfs.sh"
    bash -n "${PROJECT_ROOT}/system/config/post-install.sh"
    bash -n "${PROJECT_ROOT}/ai/terminal/phantom-term"

    if [[ "$missing" -ne 0 ]]; then
        return 1
    fi

    log_info "Validation complete."
}

build_bundle() {
    log_info "Building non-root developer bundle..."
    mkdir -p "$OUTDIR"
    tar -czf "$OUTDIR/$BUNDLE_NAME" \
        --exclude="$PROJECT_ROOT/.venv" \
        --exclude="$PROJECT_ROOT/__pycache__" \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        -C "$PROJECT_ROOT" \
        README.md \
        Makefile \
        requirements.txt \
        Qwen3.5-0.8B-BF16.gguf \
        ai \
        boot \
        build \
        compatibility \
        docs \
        gui \
        privacy \
        runtime \
        system \
        phantom_env.py
    log_info "Bundle created: $OUTDIR/$BUNDLE_NAME"
}

require_root() {
    if [[ "${EUID}" -ne 0 ]]; then
        log_error "This step must run as root."
        exit 1
    fi
}

setup_chroot() {
    log_info "Setting up chroot environment..."
    mkdir -p "$ROOTFS_DIR"
    debootstrap --arch="$ARCH" "$SUITE" "$ROOTFS_DIR" http://deb.debian.org/debian
}

install_kernel() {
    log_info "Installing hardened kernel..."
    chroot "$ROOTFS_DIR" apt-get update
    chroot "$ROOTFS_DIR" apt-get install -y linux-image-amd64
}

install_gui() {
    log_info "Installing Wayland GUI stack..."
    chroot "$ROOTFS_DIR" apt-get install -y \
        sway \
        swayidle \
        swaylock \
        wayland-protocols \
        wl-clipboard \
        grim \
        slurp \
        mako-notifier \
        waybar \
        wofi \
        alacritty \
        brightnessctl \
        polkit-gnome \
        greetd \
        tuigreet \
        pipewire \
        pipewire-alsa \
        pipewire-pulse \
        plymouth \
        plymouth-themes
}

install_shell_tools() {
    log_info "Installing shell tools..."
    chroot "$ROOTFS_DIR" apt-get install -y \
        zsh \
        zsh-autosuggestions \
        zsh-syntax-highlighting \
        curl \
        wget
    # Install starship prompt
    chroot "$ROOTFS_DIR" bash -c 'curl -sS https://starship.rs/install.sh | sh -s -- -y' || true
}

install_ai_terminal() {
    log_info "Installing AI Terminal dependencies..."
    chroot "$ROOTFS_DIR" apt-get install -y \
        python3 \
        python3-pip \
        python3-venv \
        python3-dev \
        curl
}

install_privacy() {
    log_info "Installing privacy tools..."
    chroot "$ROOTFS_DIR" apt-get install -y \
        tor \
        iptables \
        ufw \
        cryptsetup \
        wireguard-tools \
        macchanger \
        libvirt-daemon-system
}

install_compatibility() {
    log_info "Installing compatibility layer..."
    chroot "$ROOTFS_DIR" apt-get install -y \
        wine \
        flatpak \
        snapd \
        qemu-kvm \
        libvirt-clients \
        bridge-utils
}

configure_system() {
    log_info "Configuring PhantomOS system..."
    
    # Set hostname
    echo "phantomos" > "$ROOTFS_DIR/etc/hostname"
    
    # Create phantom user
    chroot "$ROOTFS_DIR" useradd -m -s /bin/zsh phantom || true
    
    # Enable services
    chroot "$ROOTFS_DIR" systemctl enable tor || true
    chroot "$ROOTFS_DIR" systemctl enable libvirtd || true
}

copy_project_overlay() {
    log_info "Copying PhantomOS overlay into rootfs..."
    mkdir -p \
        "$ROOTFS_DIR/opt/phantom" \
        "$ROOTFS_DIR/etc/phantom" \
        "$ROOTFS_DIR/etc/phantom/network" \
        "$ROOTFS_DIR/usr/local/bin" \
        "$ROOTFS_DIR/usr/share/phantom/themes" \
        "$ROOTFS_DIR/usr/share/phantom/extensions" \
        "$ROOTFS_DIR/usr/share/phantom/plugins" \
        "$ROOTFS_DIR/etc/systemd/system" \
        "$ROOTFS_DIR/etc/greetd" \
        "$ROOTFS_DIR/etc/pipewire" \
        "$ROOTFS_DIR/etc/sysctl.d" \
        "$ROOTFS_DIR/etc/apparmor.d" \
        "$ROOTFS_DIR/usr/share/plymouth/themes/phantom"

    # Core source tree
    cp -a "${PROJECT_ROOT}/ai" "${PROJECT_ROOT}/compatibility" "${PROJECT_ROOT}/gui" \
        "${PROJECT_ROOT}/privacy" "${PROJECT_ROOT}/system" "${PROJECT_ROOT}/phantom_env.py" \
        "$ROOTFS_DIR/opt/phantom/"

    # Config
    cp -a "${PROJECT_ROOT}/system/config/config.json" "$ROOTFS_DIR/etc/phantom/config.json"

    # Themes
    for theme in "${PROJECT_ROOT}"/gui/themes/*.json; do
        cp -a "${theme}" "$ROOTFS_DIR/usr/share/phantom/themes/"
    done

    # Extensions
    cp -a "${PROJECT_ROOT}/gui/extensions/manifest.json" "$ROOTFS_DIR/usr/share/phantom/extensions/manifest.json"

    # Binaries
    install -m 0755 "${PROJECT_ROOT}/ai/terminal/phantom-term" "$ROOTFS_DIR/usr/local/bin/phantom-term"
    install -m 0755 "${PROJECT_ROOT}/system/scripts/phantom-agent.py" "$ROOTFS_DIR/usr/local/bin/phantom-agent"

    # Systemd services
    for svc in phantom-agent phantom-ai phantom-privacy phantom-vm \
               phantom-update phantom-cleanup; do
        src="${PROJECT_ROOT}/system/config/${svc}.service"
        if [[ -f "${src}" ]]; then
            install -m 0644 "${src}" "$ROOTFS_DIR/etc/systemd/system/${svc}.service"
        fi
        # Install timers for these
        if [[ -f "${PROJECT_ROOT}/system/config/${svc}.timer" ]]; then
            install -m 0644 "${PROJECT_ROOT}/system/config/${svc}.timer" "$ROOTFS_DIR/etc/systemd/system/${svc}.timer"
        fi
    done

    # New config copy actions
    install -m 0644 "${PROJECT_ROOT}/system/config/greetd.toml" "$ROOTFS_DIR/etc/greetd/config.toml"
    install -m 0644 "${PROJECT_ROOT}/system/config/pipewire.conf" "$ROOTFS_DIR/etc/pipewire/pipewire.conf"
    install -m 0644 "${PROJECT_ROOT}/system/config/pipewire-pulse.conf" "$ROOTFS_DIR/etc/pipewire/pipewire-pulse.conf"
    
    install -m 0644 "${PROJECT_ROOT}/privacy/firewall/sysctl-hardened.conf" "$ROOTFS_DIR/etc/sysctl.d/99-phantom-hardened.conf"
    install -m 0644 "${PROJECT_ROOT}/privacy/tools/apparmor/usr.lib.firefox" "$ROOTFS_DIR/etc/apparmor.d/usr.lib.firefox"
    install -m 0644 "${PROJECT_ROOT}/privacy/tools/apparmor/phantom-sandbox" "$ROOTFS_DIR/etc/apparmor.d/phantom-sandbox"
    
    install -m 0644 "${PROJECT_ROOT}/boot/plymouth/phantom.plymouth" "$ROOTFS_DIR/usr/share/plymouth/themes/phantom/"
    install -m 0644 "${PROJECT_ROOT}/boot/plymouth/phantom.script" "$ROOTFS_DIR/usr/share/plymouth/themes/phantom/"
    
    install -m 0755 "${PROJECT_ROOT}/system/scripts/phantom-ctl" "$ROOTFS_DIR/usr/local/bin/phantom-ctl"
    install -m 0755 "${PROJECT_ROOT}/system/scripts/phantom-installer.py" "$ROOTFS_DIR/usr/local/bin/phantom-installer"

    # User configs (skel)
    local SKEL="$ROOTFS_DIR/etc/skel"
    install -d "${SKEL}/.config/sway" "${SKEL}/.config/waybar" "${SKEL}/.config/alacritty" \
               "${SKEL}/.config/wofi" "${SKEL}/.config/mako" \
               "${SKEL}/.config/gtk-3.0" "${SKEL}/.config/qt5ct" "${SKEL}/.config/swaylock"
    install -m 0644 "${PROJECT_ROOT}/gui/wayland/configs/sway.config"       "${SKEL}/.config/sway/config"
    cp -a "${PROJECT_ROOT}/gui/wayland/configs/waybar/"*                    "${SKEL}/.config/waybar/"
    install -m 0644 "${PROJECT_ROOT}/gui/wayland/configs/alacritty.toml"    "${SKEL}/.config/alacritty/alacritty.toml"
    install -m 0644 "${PROJECT_ROOT}/gui/wayland/configs/wofi/style.css"    "${SKEL}/.config/wofi/style.css"
    install -m 0644 "${PROJECT_ROOT}/gui/wayland/configs/mako/config"       "${SKEL}/.config/mako/config"
    install -m 0644 "${PROJECT_ROOT}/gui/wayland/configs/gtk-3.0/settings.ini" "${SKEL}/.config/gtk-3.0/settings.ini"
    install -m 0644 "${PROJECT_ROOT}/gui/wayland/configs/qt5ct/qt5ct.conf"  "${SKEL}/.config/qt5ct/qt5ct.conf"
    install -m 0644 "${PROJECT_ROOT}/gui/wayland/configs/swaylock/config"   "${SKEL}/.config/swaylock/config"
    install -m 0644 "${PROJECT_ROOT}/system/config/zshrc"                   "${SKEL}/.zshrc"
    install -d "${SKEL}/.config"
    install -m 0644 "${PROJECT_ROOT}/system/config/starship.toml"           "${SKEL}/.config/starship.toml"
}

prepare_iso_tree() {
    log_info "Preparing ISO filesystem tree..."
    mkdir -p "$ISO_TREE/boot/grub"
    cp "${PROJECT_ROOT}/boot/grub/grub.cfg" "$ISO_TREE/boot/grub/grub.cfg"
    cp "${PROJECT_ROOT}/boot/init.sh" "$ISO_TREE/boot/init.sh"
    mksquashfs "$ROOTFS_DIR" "$ISO_TREE/filesystem.squashfs" -comp zstd -noappend >/dev/null
}

build_iso() {
    log_info "Building ISO image..."
    mkdir -p "$OUTDIR"
    grub-mkrescue -o "$OUTDIR/$ISO_NAME" "$ISO_TREE" >/dev/null 2>&1
}

main() {
    case "${1:-build}" in
        validate)
            validate_sources
            exit 0
            ;;
        fast)
            check_deps || {
                log_error "Install the missing build dependencies first."
                exit 1
            }
            require_root
            setup_chroot
            configure_system
            copy_project_overlay
            prepare_iso_tree
            build_iso
            ;;
        build)
            check_deps || {
                log_error "Install the missing build dependencies first."
                exit 1
            }
            require_root
            ;;
        bundle)
            validate_sources
            build_bundle
            exit 0
            ;;
        *)
            log_error "Unknown mode: $1"
            echo "Usage: $0 [build|fast|validate|bundle]"
            exit 1
            ;;
    esac

    setup_chroot
    install_kernel
    install_gui
    install_shell_tools
    install_ai_terminal
    install_privacy
    install_compatibility
    configure_system
    copy_project_overlay
    prepare_iso_tree
    build_iso
    
    log_info "Build complete! ISO: $OUTDIR/$ISO_NAME"
}

main "$@"
