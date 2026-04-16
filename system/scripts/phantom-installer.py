#!/usr/bin/env python3
"""PhantomOS TUI Installer — Interactive disk partitioning, user creation, and system installation.

Runs in a terminal with a text-based interface using standard Python (no curses dependency).
"""

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

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
BG     = "\033[48;5;234m"


def c(color, text):
    return f"{color}{text}{RESET}"


def clear():
    os.system("clear")


def banner():
    clear()
    print()
    print(c(MINT, "  ╔══════════════════════════════════════════════════════╗"))
    print(c(MINT, "  ║") + c(BOLD + MINT, "   PhantomOS Installer v0.1                          ") + c(MINT, "║"))
    print(c(MINT, "  ║") + c(DIM,         "   Privacy-first Linux Distribution                   ") + c(MINT, "║"))
    print(c(MINT, "  ╚══════════════════════════════════════════════════════╝"))
    print()


def prompt(msg, default=None):
    suffix = f" [{default}]" if default else ""
    result = input(f"  {c(CYAN, '▸')} {msg}{suffix}: ").strip()
    return result or default


def confirm(msg):
    result = input(f"  {c(YELLOW, '?')} {msg} (y/n): ").strip().lower()
    return result == "y"


def ok(msg):     print(f"  {c(GREEN, '✓')} {msg}")
def warn(msg):   print(f"  {c(YELLOW, '⚠')} {msg}")
def err(msg):    print(f"  {c(RED, '✗')} {msg}")
def info(msg):   print(f"  {c(CYAN, '▸')} {msg}")
def section(t):  print(f"\n  {c(BOLD + MINT, f'── {t} ──')}\n")


class Installer:
    def __init__(self):
        self.config = {
            "disk": None,
            "encrypt": False,
            "username": "phantom",
            "password": "",
            "hostname": "phantomos",
            "locale": "en_US.UTF-8",
            "timezone": "Europe/Rome",
            "theme": "mint",
        }

    def run(self):
        banner()

        if os.geteuid() != 0:
            err("The installer must run as root.")
            err("Usage: sudo python3 phantom-installer.py")
            return

        self.step_welcome()
        self.step_disk()
        self.step_encryption()
        self.step_user()
        self.step_locale()
        self.step_timezone()
        self.step_theme()
        self.step_confirm()
        self.step_install()

    def step_welcome(self):
        section("Welcome")
        print("  This wizard will guide you through installing PhantomOS")
        print("  on your computer. You can press Ctrl+C at any time to abort.\n")
        input(f"  {c(DIM, 'Press Enter to continue...')}")

    def step_disk(self):
        banner()
        section("Disk Selection")

        # List available disks
        result = subprocess.run(
            ["lsblk", "-dpno", "NAME,SIZE,MODEL"],
            capture_output=True, text=True,
        )
        disks = []
        for line in result.stdout.strip().splitlines():
            parts = line.split(None, 2)
            if len(parts) >= 2 and not parts[0].startswith("/dev/loop"):
                disks.append(parts)
                idx = len(disks)
                info(f"{idx}. {parts[0]:15s} {parts[1]:>10s}  {parts[2] if len(parts) > 2 else ''}")

        if not disks:
            err("No disks found!")
            sys.exit(1)

        print()
        choice = prompt("Select disk number", "1")
        try:
            idx = int(choice) - 1
            self.config["disk"] = disks[idx][0]
            ok(f"Selected: {self.config['disk']}")
        except (ValueError, IndexError):
            err("Invalid selection")
            sys.exit(1)

    def step_encryption(self):
        print()
        section("Disk Encryption")
        self.config["encrypt"] = confirm("Enable full-disk encryption (LUKS)?")
        if self.config["encrypt"]:
            ok("LUKS encryption will be enabled")
            self.config["luks_password"] = prompt("Encryption password")
        else:
            info("No encryption — disk will be unencrypted")

    def step_user(self):
        banner()
        section("User Account")
        self.config["username"] = prompt("Username", "phantom")
        self.config["password"] = prompt("Password", "phantom")
        self.config["hostname"] = prompt("Hostname", "phantomos")
        ok(f"User: {self.config['username']}@{self.config['hostname']}")

    def step_locale(self):
        print()
        section("Locale")
        locales = [
            ("1", "en_US.UTF-8", "English (US)"),
            ("2", "it_IT.UTF-8", "Italiano"),
            ("3", "de_DE.UTF-8", "Deutsch"),
            ("4", "fr_FR.UTF-8", "Français"),
            ("5", "es_ES.UTF-8", "Español"),
            ("6", "pt_BR.UTF-8", "Português (BR)"),
            ("7", "ja_JP.UTF-8", "日本語"),
            ("8", "zh_CN.UTF-8", "中文"),
        ]
        for num, code, name in locales:
            info(f"{num}. {name} ({code})")
        print()
        choice = prompt("Select locale", "1")
        try:
            idx = int(choice) - 1
            self.config["locale"] = locales[idx][1]
            ok(f"Locale: {self.config['locale']}")
        except (ValueError, IndexError):
            self.config["locale"] = "en_US.UTF-8"

    def step_timezone(self):
        print()
        section("Timezone")
        self.config["timezone"] = prompt("Timezone", "Europe/Rome")
        ok(f"Timezone: {self.config['timezone']}")

    def step_theme(self):
        print()
        section("Theme")
        themes = ["mint", "phantom-dark", "phantom-light"]
        for i, t in enumerate(themes, 1):
            info(f"{i}. {t}")
        print()
        choice = prompt("Select theme", "1")
        try:
            idx = int(choice) - 1
            self.config["theme"] = themes[idx]
        except (ValueError, IndexError):
            self.config["theme"] = "mint"
        ok(f"Theme: {self.config['theme']}")

    def step_confirm(self):
        banner()
        section("Installation Summary")
        info(f"Disk:       {self.config['disk']}")
        info(f"Encryption: {'LUKS' if self.config['encrypt'] else 'None'}")
        info(f"User:       {self.config['username']}")
        info(f"Hostname:   {self.config['hostname']}")
        info(f"Locale:     {self.config['locale']}")
        info(f"Timezone:   {self.config['timezone']}")
        info(f"Theme:      {self.config['theme']}")
        print()
        warn(f"ALL DATA on {self.config['disk']} WILL BE DESTROYED!")
        print()
        if not confirm("Proceed with installation?"):
            print("\n  Aborted.\n")
            sys.exit(0)

    def step_install(self):
        banner()
        section("Installing PhantomOS")
        disk = self.config["disk"]

        # 1. Partition
        info("Partitioning disk...")
        subprocess.run(["parted", "-s", disk, "mklabel", "gpt"], check=True)
        subprocess.run(["parted", "-s", disk, "mkpart", "primary", "fat32", "1MiB", "512MiB"], check=True)
        subprocess.run(["parted", "-s", disk, "set", "1", "esp", "on"], check=True)
        subprocess.run(["parted", "-s", disk, "mkpart", "primary", "ext4", "512MiB", "100%"], check=True)
        ok("Partitioned")

        # 2. Format
        info("Formatting partitions...")
        subprocess.run(["mkfs.fat", "-F32", f"{disk}1"], check=True)

        root_dev = f"{disk}2"
        if self.config["encrypt"]:
            info("Setting up LUKS encryption...")
            subprocess.run(
                ["cryptsetup", "luksFormat", "--type", "luks2", "-q", root_dev],
                input=f"{self.config['luks_password']}\n".encode(),
                check=True,
            )
            subprocess.run(
                ["cryptsetup", "open", root_dev, "cryptroot"],
                input=f"{self.config['luks_password']}\n".encode(),
                check=True,
            )
            root_dev = "/dev/mapper/cryptroot"
            ok("LUKS encryption enabled")

        subprocess.run(["mkfs.ext4", "-F", root_dev], check=True)
        ok("Formatted")

        # 3. Mount
        info("Mounting filesystems...")
        subprocess.run(["mount", root_dev, "/mnt"], check=True)
        os.makedirs("/mnt/boot/efi", exist_ok=True)
        subprocess.run(["mount", f"{disk}1", "/mnt/boot/efi"], check=True)
        ok("Mounted")

        # 4. Debootstrap
        info("Installing base system (this may take a while)...")
        subprocess.run(
            ["debootstrap", "--arch=amd64", "stable", "/mnt", "http://deb.debian.org/debian"],
            check=True,
        )
        ok("Base system installed")

        # 5. Copy PhantomOS overlay
        info("Copying PhantomOS files...")
        os.makedirs("/mnt/opt/phantom", exist_ok=True)
        subprocess.run(["cp", "-a", str(ROOT), "/mnt/opt/phantom/"], check=True)
        ok("PhantomOS overlay installed")

        # 6. Configure
        info("Configuring system...")
        # Hostname
        Path("/mnt/etc/hostname").write_text(self.config["hostname"] + "\n")

        # Fstab
        with open("/mnt/etc/fstab", "w") as f:
            f.write(f"{root_dev}  /          ext4  defaults  0  1\n")
            f.write(f"{disk}1     /boot/efi  vfat  defaults  0  2\n")

        # Run post-install in chroot
        subprocess.run(
            ["chroot", "/mnt", "bash", "/opt/phantom/system/config/post-install.sh"],
            check=True,
        )
        ok("System configured")

        # 7. Bootloader
        info("Installing GRUB bootloader...")
        subprocess.run([
            "chroot", "/mnt",
            "grub-install", "--target=x86_64-efi",
            "--efi-directory=/boot/efi", "--bootloader-id=PhantomOS"
        ], check=True)
        subprocess.run(["chroot", "/mnt", "update-grub"], check=True)
        ok("Bootloader installed")

        # 8. Cleanup
        info("Cleaning up...")
        subprocess.run(["umount", "-R", "/mnt"], check=False)
        if self.config["encrypt"]:
            subprocess.run(["cryptsetup", "close", "cryptroot"], check=False)
        ok("Cleanup complete")

        # 9. Done
        print()
        print(c(BOLD + MINT, "  ╔══════════════════════════════════════════════════════╗"))
        print(c(BOLD + MINT, "  ║   Installation Complete!                             ║"))
        print(c(BOLD + MINT, "  ║   Remove the installation media and reboot.          ║"))
        print(c(BOLD + MINT, "  ╚══════════════════════════════════════════════════════╝"))
        print()
        info(f"Login as '{self.config['username']}' with your chosen password")
        info("The desktop will start automatically via greetd")
        print()


if __name__ == "__main__":
    try:
        installer = Installer()
        installer.run()
    except KeyboardInterrupt:
        print("\n\n  Installation aborted.\n")
        sys.exit(1)
