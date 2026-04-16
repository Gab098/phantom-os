# PhantomOS Developer Guide

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│ GUI Layer — "PhantomShell" (Sway + extensions)          │
│   gui/extensions/  gui/plugins/  gui/themes/            │
├─────────────────────────────────────────────────────────┤
│ Compatibility Layer (Wine/Proton, .deb, Flatpak, VM)    │
│   compatibility/packages/  compatibility/wine/  vm/     │
├─────────────────────────────────────────────────────────┤
│ AI Terminal Layer (Local LLM 0.8B + NL→bash)            │
│   ai/llm/  ai/terminal/  ai/nlp/                       │
├─────────────────────────────────────────────────────────┤
│ Privacy & Security (Tor, Firewall, Encryption)          │
│   privacy/firewall/  privacy/encryption/  privacy/tools/│
├─────────────────────────────────────────────────────────┤
│ System Base (Agent, Updater, Network)                   │
│   system/base/  system/scripts/  system/config/         │
├─────────────────────────────────────────────────────────┤
│ Kernel Hardened (Linux 6.x + Debian base)               │
│   kernel/  boot/                                        │
└─────────────────────────────────────────────────────────┘
```

## Adding Extensions

Extensions are JS/CSS packages loaded by PhantomShell.

### Extension Structure

```
my-extension/
├── manifest.json
├── index.js
├── style.css (optional)
└── assets/ (optional)
```

### manifest.json

```json
{
    "name": "My Extension",
    "version": "1.0.0",
    "author": "Your Name",
    "description": "What it does",
    "permissions": ["ui.panel", "system.fs.read"],
    "entry_point": "index.js"
}
```

### Available Permissions

| Permission | Description |
|-----------|-------------|
| `ui.panel` | Add items to the panel |
| `ui.widget` | Create desktop widgets |
| `ui.notification` | Send notifications |
| `ui.tray` | Add tray icons |
| `system.fs.read` | Read filesystem |
| `system.fs.write` | Write filesystem |
| `system.process` | Manage processes |
| `system.network` | Network access |
| `system.privacy` | Privacy settings |
| `ai.terminal` | AI terminal integration |
| `ai.completion` | AI code completion |
| `ai.voice` | Voice recognition |

### Install & Manage

```bash
python3 gui/extensions/extension_manager.py install ./my-extension/
python3 gui/extensions/extension_manager.py enable my-extension
python3 gui/extensions/extension_manager.py list
python3 gui/extensions/extension_manager.py disable my-extension
python3 gui/extensions/extension_manager.py uninstall my-extension
```

## Adding Plugins

Plugins are Python-based GUI modules loaded dynamically.

### Plugin Structure

```
my-plugin/
├── plugin.json
├── main.py
└── resources/ (optional)
```

### plugin.json

```json
{
    "name": "my-plugin",
    "version": "1.0.0",
    "author": "Your Name",
    "description": "A GUI plugin",
    "entry_point": "main.py",
    "permissions": ["ui.panel"]
}
```

### Install & Manage

```bash
python3 gui/plugins/plugin_manager.py install ./my-plugin/
python3 gui/plugins/plugin_manager.py enable my-plugin
python3 gui/plugins/plugin_manager.py list
```

## Creating Themes

### Theme JSON

```json
{
    "name": "my-theme",
    "version": "1.0.0",
    "author": "Your Name",
    "colors": {
        "bg_primary": "#1A1A2E",
        "bg_secondary": "#16213E",
        "fg_primary": "#E0E0E0",
        "fg_secondary": "#8888AA",
        "accent": "#0F3460",
        "accent_alt": "#533483",
        "warning": "#FFB800",
        "error": "#E94560",
        "success": "#00B894"
    },
    "fonts": {
        "ui": "Inter, sans-serif",
        "mono": "JetBrains Mono, monospace"
    },
    "borders": {
        "radius": "8px",
        "width": "1px"
    },
    "spacing": {
        "base": "8px",
        "padding": "12px"
    },
    "effects": {
        "shadow": "0 2px 8px rgba(0,0,0,0.3)",
        "transitions": "0.2s ease"
    }
}
```

### Apply

```bash
python3 gui/themes/theme_manager.py
# Or programmatically:
# ThemeManager().apply_theme("my-theme")
```

## Adding Privacy Tools

Privacy tools are Python classes in `privacy/tools/`.

### Example Tool

```python
#!/usr/bin/env python3
import subprocess
from pathlib import Path

class MySecurityTool:
    def __init__(self):
        self.name = "my-tool"
    
    def scan(self, target):
        result = subprocess.run(
            ["nmap", "-sV", target],
            capture_output=True, text=True, timeout=60
        )
        return result.stdout
    
    def report(self, results):
        Path("/var/lib/phantom/reports").mkdir(parents=True, exist_ok=True)
        # ... save report
```

## Running Tests

```bash
make dev-setup       # One-time venv setup
make test            # Run all unit tests
make lint            # Run ruff linter
make validate        # Static checks + compileall
make smoke           # Integration test with LLM
```

## Build Pipeline

```
make validate  →  make dev-setup  →  make smoke  →  make bundle
                                                          ↓
                                              PhantomOS-devkit-v0.1.tar.gz

sudo make build  →  debootstrap  →  chroot install  →  overlay  →  squashfs  →  ISO
```

## Directory Map

```
os/
├── ai/                         # AI terminal layer
│   ├── llm/llm_server.py       #   LLM HTTP server
│   ├── nlp/locale_manager.py   #   Locale + AI manager
│   └── terminal/               #   NL→bash terminal
├── boot/                       # Boot chain
│   ├── grub/grub.cfg           #   GRUB config
│   ├── init.sh                 #   initramfs init script
│   └── mkinitramfs.sh          #   initramfs builder
├── build/                      # Build pipeline
│   ├── build.sh                #   Main build script
│   ├── setup.sh                #   Quick setup wizard
│   ├── dev-setup.sh            #   Dev venv creator
│   ├── smoke.sh                #   Smoke test runner
│   └── create-usb.sh           #   USB writer
├── compatibility/              # App compatibility
│   ├── packages/               #   .deb, Flatpak, AppImage, Snap
│   ├── vm/                     #   KVM/QEMU VM manager
│   └── wine/                   #   Wine/Proton manager
├── docs/                       # Documentation
├── gui/                        # GUI layer
│   ├── extensions/             #   JS/CSS extension system
│   ├── plugins/                #   Python plugin system
│   ├── themes/                 #   Theme definitions
│   └── wayland/                #   Sway/Waybar/Alacritty configs
├── kernel/                     # Kernel config
├── privacy/                    # Privacy & security
│   ├── encryption/             #   LUKS disk encryption
│   ├── firewall/               #   iptables/UFW wrapper
│   └── tools/                  #   Hacking/security tools
├── runtime/                    # Runtime data tree
├── system/                     # System management
│   ├── base/                   #   Core OS, updater
│   ├── config/                 #   Configs, systemd units
│   └── scripts/                #   Agent, network, installer
├── tests/                      # Unit tests
├── phantom_env.py              # Shared path resolution
├── Makefile                    # Build targets
└── requirements.txt            # Python dependencies
```
