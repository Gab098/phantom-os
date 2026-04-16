# PhantomOS Technical Specification v0.1

## Overview
PhantomOS is a lightweight Linux distribution focused on privacy, hacking, and extensibility.
Built on a Debian stable base with Wayland display, local AI integration, and a modular architecture.

## System Requirements
- CPU: x86-64 (64-bit only)
- RAM: 4GB minimum, 8GB recommended
- Storage: 20GB minimum
- GPU: Intel/AMD/NVIDIA (optional for GPU passthrough)

## Architecture

### Layer 1: Kernel
- Linux 6.x with hardened patches (grsecurity-style)
- 64-bit only (no 32-bit support)
- Modular design
- Init: systemd (OpenRC planned for v0.5)

### Layer 2: Privacy & Security
- Firewall: iptables/nftables with UFW wrapper
- Encryption: LUKS full disk encryption with key-file support
- Network: Tor integration, WireGuard/OpenVPN VPN, MAC randomization
- DNS: DNS-over-TLS via systemd-resolved
- App Sandbox: bubblewrap

### Layer 3: AI Terminal
- Model: Qwen3.5-0.8B GGUF (default) or a HuggingFace-compatible CPU model directory
- Runtime: llama.cpp or Transformers on CPU
- Interface: Natural language → bash conversion
- Server: HTTP REST API on localhost:8080

### Layer 4: Compatibility Layer
- Wine/Proton for .exe (with DXVK, Winetricks, prefix management)
- Flatpak, Snap, AppImage support
- dpkg for .deb
- KVM/QEMU for full VMs with QuickBoot snapshots
- GPU passthrough (VFIO/IOMMU)

### Layer 5: GUI — "PhantomShell"
- Compositor: Sway (Wayland)
- Terminal: Alacritty (themed)
- Launcher: Wofi (themed)
- Notifications: Mako (themed)
- Bar: Waybar
- Extensions: JS/CSS based plugin system
- Plugins: Python-based dynamic modules
- Themes: JSON-defined, hot-swappable (mint, dark, light)

## Directory Structure
```
os/
├── ai/                         # AI terminal layer
│   ├── llm/                    #   LLM HTTP server
│   ├── nlp/                    #   Locale + AI manager
│   └── terminal/               #   NL→bash terminal
├── boot/                       # Boot chain
│   ├── grub/                   #   GRUB configuration
│   ├── init.sh                 #   initramfs init (disk + live ISO)
│   └── mkinitramfs.sh          #   initramfs builder
├── build/                      # Build pipeline
├── compatibility/              # App compatibility
│   ├── packages/               #   .deb, Flatpak, AppImage, Snap
│   ├── vm/                     #   KVM/QEMU VM manager
│   └── wine/                   #   Wine/Proton manager
├── docs/                       # Documentation
├── gui/                        # GUI layer
│   ├── extensions/             #   JS/CSS extensions
│   ├── plugins/                #   Python plugins
│   ├── themes/                 #   Theme JSON files
│   └── wayland/                #   Sway/Waybar/Alacritty/Wofi/Mako configs
├── kernel/                     # Kernel config
├── privacy/                    # Privacy & security
│   ├── encryption/             #   LUKS disk encryption
│   ├── firewall/               #   iptables/UFW wrapper
│   └── tools/                  #   Hacking/security tools
├── runtime/                    # Runtime data tree
│   ├── etc/phantom/            #     Configuration
│   ├── var/lib/phantom/        #     Runtime data (VMs, logs)
│   ├── opt/phantom/            #     Custom packages
│   └── home/phantom/           #     User home
├── system/                     # System management
│   ├── base/                   #   Core OS info, updater
│   ├── config/                 #   JSON config, systemd units, shell config
│   └── scripts/                #   Agent, network, installer
├── tests/                      # Unit tests
├── phantom_env.py              # Shared path resolution
├── Makefile                    # Build targets
└── requirements.txt            # Python dependencies
```

## Services
| Service | Unit File | Description |
|---------|-----------|-------------|
| phantom-agent | `phantom-agent.service` | Main system daemon — monitors health, manages sub-services |
| phantom-ai | `phantom-ai.service` | LLM inference server (Qwen3.5-0.8B on localhost:8080) |
| phantom-privacy | `phantom-privacy.service` | Firewall + Tor activation on boot |
| phantom-vm | `phantom-vm.service` | VM quick-boot manager (depends on libvirtd) |

## Security Model
1. Default deny firewall (UFW)
2. LUKS-encrypted home partition with key-file support
3. Tor by default for sensitive traffic
4. WireGuard VPN support
5. MAC address randomization
6. DNS-over-TLS
7. App sandboxing via bubblewrap for untrusted apps
8. No telemetry or data collection

## Build Process
1. `make validate` — static checks + compileall
2. `make dev-setup` — create Python virtualenv
3. `make smoke` — integration test (LLM server + terminal)
4. `make test` — unit tests
5. `make bundle` — portable devkit tarball (no root)
6. `sudo make build` — full ISO build:
   - Debootstrap Debian stable
   - Install kernel + Wayland stack + Zsh/Starship
   - Configure privacy layer
   - Add compatibility tools (Wine, KVM)
   - Copy overlay (configs, themes, services)
   - Build squashfs + GRUB ISO

## Roadmap
- v0.1: Debian base + Wayland GUI + privacy core + AI terminal
- v0.5: OpenRC init option + voice AI + app store
- v1.0: Full VM Manager + Compatibility Layer + ARM support

## License
MIT
