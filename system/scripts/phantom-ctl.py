#!/usr/bin/env python3
"""phantom-ctl — Unified CLI for managing PhantomOS.

Usage:
    phantom-ctl status              Show system overview
    phantom-ctl services [start|stop|restart|status] [name]
    phantom-ctl privacy [firewall|tor|vpn|mac] [args...]
    phantom-ctl ai [start|stop|status|query "..."]
    phantom-ctl vm [list|create|start|stop|snapshot] [name]
    phantom-ctl theme [list|apply|create] [name]
    phantom-ctl ext [list|install|uninstall|enable|disable] [name]
    phantom-ctl plugin [list|install|uninstall|enable|disable] [name]
    phantom-ctl pkg [install|remove|update|search|list-upgradeable] [name]
    phantom-ctl net [status|wifi|vpn|dns|mac] [args...]
    phantom-ctl update [--dry-run]
    phantom-ctl info
    phantom-ctl help
"""

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from phantom_env import load_system_config, resolve_model_path, config_dir, data_dir

# ── ANSI helpers ─────────────────────────────────────────────
RESET  = "\033[0m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
GREEN  = "\033[38;5;35m"
CYAN   = "\033[38;5;37m"
YELLOW = "\033[38;5;220m"
RED    = "\033[38;5;196m"
MINT   = "\033[38;5;43m"
GRAY   = "\033[38;5;245m"


def c(color, text):
    return f"{color}{text}{RESET}"


def header(title):
    width = 56
    print()
    print(c(MINT, "  ╔" + "═" * width + "╗"))
    print(c(MINT, "  ║") + c(BOLD + MINT, f"  {title}".ljust(width)) + c(MINT, "║"))
    print(c(MINT, "  ╚" + "═" * width + "╝"))
    print()


def ok(msg):     print(f"  {c(GREEN, '✓')} {msg}")
def warn(msg):   print(f"  {c(YELLOW, '⚠')} {msg}")
def err(msg):    print(f"  {c(RED, '✗')} {msg}")
def info(msg):   print(f"  {c(CYAN, '▸')} {msg}")
def dim(msg):    print(f"  {c(GRAY, msg)}")


# ── Commands ─────────────────────────────────────────────────

def cmd_status():
    """Show full system overview."""
    from system.base.phantom_base import PhantomBase
    base = PhantomBase()
    base.print_banner()

    header("System Status")
    si = base.system_info()
    info(f"Kernel:  {si.get('kernel', '?')}")
    info(f"Arch:    {si.get('arch', '?')}")
    info(f"Host:    {si.get('hostname', '?')}")
    info(f"Python:  {si.get('python', '?')}")
    if "cpu_count" in si:
        info(f"CPU:     {si['cpu_count']} cores @ {si.get('cpu_percent', '?')}%")
        info(f"RAM:     {si.get('ram_total_mb', '?')} MB ({si.get('ram_used_pct', '?')}% used)")
        info(f"Disk:    {si.get('disk_usage_pct', '?')}% used")

    header("Services")
    for name, state in base.service_status().items():
        if state == "active":
            ok(f"{name}: {state}")
        elif state in ("inactive", "dead"):
            dim(f"{name}: {state}")
        else:
            warn(f"{name}: {state}")

    header("AI Model")
    ai = base.ai_status()
    if ai["exists"]:
        ok(f"Model: {Path(ai['model_path']).name} ({ai['size_mb']} MB)")
    else:
        warn(f"Model not found: {ai['model_path']}")

    header("Storage")
    for label, data in base.storage_summary().items():
        info(f"{label:8s} {data['size_mb']:>8.2f} MB  {c(DIM, data['path'])}")
    print()


def cmd_services(args):
    """Manage systemd services."""
    services = ["phantom-agent", "phantom-ai", "phantom-privacy", "phantom-vm", "tor", "libvirtd"]

    if not args:
        header("PhantomOS Services")
        for svc in services:
            r = subprocess.run(["systemctl", "is-active", svc], capture_output=True, text=True)
            state = r.stdout.strip()
            if state == "active":
                ok(f"{svc}")
            else:
                dim(f"{svc}: {state}")
        return

    action = args[0]
    if action == "status":
        name = args[1] if len(args) > 1 else None
        targets = [name] if name else services
        for svc in targets:
            subprocess.run(["systemctl", "status", svc, "--no-pager", "-l"])
    elif action in ("start", "stop", "restart", "enable", "disable"):
        if len(args) < 2:
            err(f"Usage: phantom-ctl services {action} <name>")
            return
        subprocess.run(["sudo", "systemctl", action, args[1]])
    else:
        err(f"Unknown action: {action}")


def cmd_privacy(args):
    """Manage privacy features."""
    from privacy.firewall.phantom_privacy import PhantomPrivacy

    if not args:
        header("Privacy Controls")
        info("phantom-ctl privacy firewall [default|strict|paranoid]")
        info("phantom-ctl privacy tor [start|stop|status]")
        info("phantom-ctl privacy vpn [add|start|stop] <name> [config]")
        info("phantom-ctl privacy mac [randomize|restore] [interface]")
        return

    p = PhantomPrivacy()
    sub = args[0]

    if sub == "firewall":
        profile = args[1] if len(args) > 1 else "default"
        p.setup_firewall(profile)
        ok(f"Firewall set to '{profile}' profile")

    elif sub == "tor":
        action = args[1] if len(args) > 1 else "status"
        subprocess.run(["sudo", "systemctl", action, "tor"])

    elif sub == "vpn":
        # Dynamically import to avoid issues if not available
        import importlib
        importlib.import_module("system.scripts.phantom-network")

    elif sub == "mac":
        from system.scripts.phantom_network import PhantomNetwork  # type: ignore[import]
        net = PhantomNetwork()
        iface = args[2] if len(args) > 2 else "wlan0"
        action = args[1] if len(args) > 1 else "randomize"
        if action == "randomize":
            net.randomize_mac(iface)
        else:
            net.restore_mac(iface)


def cmd_ai(args):
    """Manage the AI subsystem."""
    if not args:
        header("AI Terminal")
        info("phantom-ctl ai start       Start LLM server")
        info("phantom-ctl ai stop        Stop LLM server")
        info("phantom-ctl ai status      Check server health")
        info('phantom-ctl ai query "..." Send a prompt')
        return

    action = args[0]

    if action == "start":
        subprocess.run(["sudo", "systemctl", "start", "phantom-ai"])
        ok("AI service started")

    elif action == "stop":
        subprocess.run(["sudo", "systemctl", "stop", "phantom-ai"])
        ok("AI service stopped")

    elif action == "status":
        import urllib.request
        import urllib.error
        config = load_system_config()
        port = config.get("ai", {}).get("server_port", 8080)
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=3) as resp:
                data = json.loads(resp.read().decode())
                ok(f"Server ready on port {port}")
                info(f"Model: {data.get('model_path', '?')}")
        except Exception:
            warn(f"Server not responding on port {port}")

    elif action == "query":
        if len(args) < 2:
            err("Usage: phantom-ctl ai query \"your prompt\"")
            return
        import urllib.request
        config = load_system_config()
        port = config.get("ai", {}).get("server_port", 8080)
        prompt = " ".join(args[1:])
        body = json.dumps({"prompt": prompt, "max_tokens": 128, "temperature": 0.7}).encode()
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}",
            data=body,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())
                print(f"\n  {c(MINT, '▸')} {data.get('response', data.get('error', '?'))}\n")
        except Exception as e:
            err(f"Query failed: {e}")

    elif action == "terminal":
        os.execvp("python3", ["python3", str(ROOT / "ai" / "terminal" / "phantom_terminal.py")])


def cmd_vm(args):
    """Manage virtual machines."""
    from compatibility.vm.vm_manager import VMManager
    vm = VMManager()

    if not args or args[0] == "list":
        header("Virtual Machines")
        try:
            vms = vm.list_vms()
            if vms:
                for name in vms:
                    info(name)
            else:
                dim("No VMs configured")
        except Exception:
            warn("libvirt not available")
        return

    action = args[0]
    if action == "create":
        if len(args) < 2:
            err("Usage: phantom-ctl vm create <name> [--iso path] [--mem 4096] [--cpus 2]")
            return
        name = args[1]
        iso = None
        mem = 4096
        cpus = 2
        i = 2
        while i < len(args):
            if args[i] == "--iso" and i + 1 < len(args):
                iso = args[i + 1]
                i += 2
            elif args[i] == "--mem" and i + 1 < len(args):
                mem = int(args[i + 1])
                i += 2
            elif args[i] == "--cpus" and i + 1 < len(args):
                cpus = int(args[i + 1])
                i += 2
            else:
                i += 1
        vm.create_vm(name, memory=mem, cpus=cpus, iso=iso)
        ok(f"VM '{name}' created")

    elif action == "start" and len(args) > 1:
        quickboot = "--quickboot" in args
        vm.start_vm(args[1], quickboot=quickboot)
        ok(f"VM '{args[1]}' started")

    elif action == "stop" and len(args) > 1:
        vm.stop_vm(args[1])
        ok(f"VM '{args[1]}' stopped")

    elif action == "snapshot" and len(args) > 1:
        vm.quickboot_snapshot(args[1])
        ok(f"QuickBoot snapshot created for '{args[1]}'")

    elif action == "gui" and len(args) > 1:
        vm.start_gui(args[1])


def cmd_theme(args):
    """Manage themes."""
    from gui.themes.theme_manager import ThemeManager
    mgr = ThemeManager()

    if not args or args[0] == "list":
        header("Themes")
        for name in mgr.list_themes():
            info(name)
        return

    if args[0] == "apply" and len(args) > 1:
        success, msg = mgr.apply_theme(args[1])
        if success:
            ok(msg)
        else:
            err(msg)

    elif args[0] == "create" and len(args) > 1:
        mgr.create_theme(args[1], {
            "bg_primary": "#1A1A2E",
            "bg_secondary": "#16213E",
            "fg_primary": "#E0E0E0",
            "fg_secondary": "#8888AA",
            "accent": "#0F3460",
        })
        ok(f"Theme '{args[1]}' created — edit it in ~/.phantom/themes/{args[1]}/")


def cmd_ext(args):
    """Manage extensions."""
    from gui.extensions.extension_manager import ExtensionManager
    mgr = ExtensionManager()

    if not args or args[0] == "list":
        header("Extensions")
        exts = mgr.list_installed()
        if exts:
            for ext in exts:
                info(f"{ext['name']} v{ext['version']} by {ext['author']}")
        else:
            dim("No extensions installed")
        return

    action = args[0]
    if action == "install" and len(args) > 1:
        success, msg = mgr.install(args[1])
        ok(msg) if success else err(msg)
    elif action == "uninstall" and len(args) > 1:
        success, msg = mgr.uninstall(args[1])
        ok(msg) if success else err(msg)
    elif action == "enable" and len(args) > 1:
        mgr.enable(args[1])
        ok(f"Enabled: {args[1]}")
    elif action == "disable" and len(args) > 1:
        mgr.disable(args[1])
        ok(f"Disabled: {args[1]}")


def cmd_pkg(args):
    """Package management wrapper."""
    from system.base.updater import Updater
    updater = Updater()

    if not args:
        header("Package Manager")
        info("phantom-ctl pkg install <name>")
        info("phantom-ctl pkg remove <name>")
        info("phantom-ctl pkg update")
        info("phantom-ctl pkg search <query>")
        info("phantom-ctl pkg list-upgradeable")
        info("phantom-ctl pkg history")
        return

    action = args[0]

    if action == "install" and len(args) > 1:
        result = updater.install_package(args[1])
        if result["returncode"] == 0:
            ok(f"Installed: {args[1]}")
        else:
            err(f"Failed to install: {args[1]}")

    elif action == "remove" and len(args) > 1:
        result = updater.remove_package(args[1])
        if result["returncode"] == 0:
            ok(f"Removed: {args[1]}")
        else:
            err(f"Failed to remove: {args[1]}")

    elif action == "update":
        dry = "--dry-run" in args
        result = updater.upgrade_all(dry_run=dry)
        if result["returncode"] == 0:
            ok(result.get("message", f"Updated {len(result.get('packages', []))} packages"))
        else:
            err("Update failed")

    elif action == "search" and len(args) > 1:
        result = subprocess.run(
            ["apt-cache", "search", args[1]],
            capture_output=True, text=True
        )
        for line in result.stdout.strip().splitlines()[:20]:
            info(line)

    elif action == "list-upgradeable":
        pkgs = updater.check_updates()
        header(f"Upgradeable Packages ({len(pkgs)})")
        for p in pkgs:
            info(p)

    elif action == "history":
        entries = updater.history()
        header("Update History")
        for entry in entries:
            ts = entry.get("timestamp", "?")[:19]
            pkgs = ", ".join(entry.get("packages", [])[:3])
            rc = entry.get("returncode", "?")
            status = c(GREEN, "OK") if rc == 0 else c(RED, f"rc={rc}")
            info(f"{ts}  {status}  {pkgs}")


def cmd_net(args):
    """Network management."""
    # Import at function level to avoid import errors if module has issues
    sys.path.insert(0, str(ROOT / "system" / "scripts"))

    if not args or args[0] == "status":
        header("Network Status")
        result = subprocess.run(["ip", "-br", "addr"], capture_output=True, text=True)
        for line in result.stdout.strip().splitlines():
            parts = line.split()
            if len(parts) >= 2:
                name = parts[0]
                state = parts[1]
                addrs = " ".join(parts[2:]) if len(parts) > 2 else ""
                if state == "UP":
                    ok(f"{name:16s} {c(GREEN, state):>20s}  {addrs}")
                else:
                    dim(f"{name:16s} {state:>8s}  {addrs}")
        return

    sub = args[0]
    if sub == "wifi":
        if len(args) > 1 and args[1] == "scan":
            result = subprocess.run(
                ["nmcli", "-t", "-f", "SSID,SIGNAL,SECURITY", "device", "wifi", "list"],
                capture_output=True, text=True,
            )
            header("Wi-Fi Networks")
            for line in result.stdout.strip().splitlines():
                parts = line.split(":")
                if len(parts) >= 3:
                    info(f"{parts[0]:30s} {parts[1]:>4s}% {c(DIM, parts[2])}")
        elif len(args) > 2 and args[1] == "connect":
            ssid = args[2]
            password = args[3] if len(args) > 3 else ""
            subprocess.run(["nmcli", "device", "wifi", "connect", ssid, "password", password])

    elif sub == "dns":
        if len(args) > 1:
            iface = args[2] if len(args) > 2 else "eth0"
            subprocess.run(["resolvectl", "dns", iface, args[1]])
            ok(f"DNS set to {args[1]} on {iface}")
        else:
            subprocess.run(["resolvectl", "status", "--no-pager"])


def cmd_update(args):
    """System update."""
    from system.base.updater import Updater
    updater = Updater()
    dry = "--dry-run" in args

    pkgs = updater.check_updates()
    if not pkgs:
        ok("System is up to date!")
        return

    header(f"Available Updates ({len(pkgs)})")
    for p in pkgs[:15]:
        info(p)
    if len(pkgs) > 15:
        dim(f"  ... and {len(pkgs) - 15} more")

    if dry:
        warn("Dry run — no changes made")
        return

    print()
    result = updater.upgrade_all()
    if result["returncode"] == 0:
        ok(f"Updated {len(pkgs)} packages")
    else:
        err("Update failed — check logs")


def cmd_info():
    """Show PhantomOS version info."""
    from system.base.phantom_base import PhantomBase
    base = PhantomBase()
    base.print_banner()
    info(f"Version:  {base.VERSION}")
    info(f"Codename: {base.CODENAME}")
    info(f"Config:   {config_dir()}")
    info(f"Data:     {data_dir()}")
    model = resolve_model_path()
    info(f"AI Model: {model} {'✓' if model.exists() else '✗'}")
    print()


def cmd_help():
    """Print help."""
    header("phantom-ctl — PhantomOS Control Center")
    commands = [
        ("status",    "System overview (CPU, RAM, services, AI)"),
        ("services",  "Manage systemd services"),
        ("privacy",   "Firewall, Tor, VPN, MAC randomization"),
        ("ai",        "AI server (start/stop/query)"),
        ("vm",        "Virtual machines (create/start/stop/snapshot)"),
        ("theme",     "Theme management"),
        ("ext",       "Extension management"),
        ("pkg",       "Package management (install/remove/search)"),
        ("net",       "Network (status/wifi/dns)"),
        ("update",    "System update"),
        ("info",      "Version info"),
        ("help",      "This help message"),
    ]
    for cmd, desc in commands:
        print(f"  {c(MINT, cmd):>30s}  {desc}")
    print()
    dim("Examples:")
    dim("  phantom-ctl status")
    dim("  phantom-ctl privacy firewall paranoid")
    dim('  phantom-ctl ai query "list running docker containers"')
    dim("  phantom-ctl theme apply phantom-dark")
    dim("  phantom-ctl pkg install neovim")
    dim("  phantom-ctl vm create win11 --iso ~/windows.iso --mem 8192")
    print()


# ── Main dispatcher ──────────────────────────────────────────

COMMANDS = {
    "status":   lambda a: cmd_status(),
    "services": cmd_services,
    "privacy":  cmd_privacy,
    "ai":       cmd_ai,
    "vm":       cmd_vm,
    "theme":    cmd_theme,
    "ext":      cmd_ext,
    "plugin":   cmd_ext,  # alias
    "pkg":      cmd_pkg,
    "net":      cmd_net,
    "update":   cmd_update,
    "info":     lambda a: cmd_info(),
    "help":     lambda a: cmd_help(),
}


def main():
    if len(sys.argv) < 2:
        cmd_help()
        return

    cmd = sys.argv[1]
    args = sys.argv[2:]

    handler = COMMANDS.get(cmd)
    if handler:
        try:
            handler(args)
        except KeyboardInterrupt:
            print()
        except Exception as e:
            err(f"Error: {e}")
            sys.exit(1)
    else:
        err(f"Unknown command: {cmd}")
        cmd_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
