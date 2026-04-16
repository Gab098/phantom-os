#!/bin/bash
set -euo pipefail
# PhantomOS Font Setup — Install Inter + JetBrains Mono system-wide

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
FONT_DIR="/usr/share/fonts/truetype/phantom"

echo "PhantomOS Font Installer"
echo "========================"

mkdir -p "${FONT_DIR}"

# --- Inter (UI font) ---
INTER_VERSION="4.1"
INTER_URL="https://github.com/rsms/inter/releases/download/v${INTER_VERSION}/Inter-${INTER_VERSION}.zip"
INTER_TMP="$(mktemp -d)"

echo "[1/3] Downloading Inter v${INTER_VERSION}..."
if curl -fsSL "${INTER_URL}" -o "${INTER_TMP}/inter.zip"; then
    unzip -q "${INTER_TMP}/inter.zip" -d "${INTER_TMP}/inter"
    find "${INTER_TMP}/inter" -name "*.ttf" -exec cp {} "${FONT_DIR}/" \;
    echo "  Installed Inter"
else
    echo "  WARNING: Could not download Inter, using system fallback"
fi
rm -rf "${INTER_TMP}"

# --- JetBrains Mono (Terminal font) ---
JBM_VERSION="2.304"
JBM_URL="https://github.com/JetBrains/JetBrainsMono/releases/download/v${JBM_VERSION}/JetBrainsMono-${JBM_VERSION}.zip"
JBM_TMP="$(mktemp -d)"

echo "[2/3] Downloading JetBrains Mono v${JBM_VERSION}..."
if curl -fsSL "${JBM_URL}" -o "${JBM_TMP}/jbm.zip"; then
    unzip -q "${JBM_TMP}/jbm.zip" -d "${JBM_TMP}/jbm"
    find "${JBM_TMP}/jbm" -name "*.ttf" -exec cp {} "${FONT_DIR}/" \;
    echo "  Installed JetBrains Mono"
else
    echo "  WARNING: Could not download JetBrains Mono, using system fallback"
fi
rm -rf "${JBM_TMP}"

# --- Fontconfig ---
echo "[3/3] Updating font cache..."
fc-cache -f "${FONT_DIR}" 2>/dev/null || true

# Set preferred fonts via fontconfig
FONTCONFIG_DIR="/etc/fonts/conf.d"
mkdir -p "${FONTCONFIG_DIR}"

cat > "${FONTCONFIG_DIR}/99-phantom-fonts.conf" << 'EOF'
<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "urn:fontconfig:fonts.dtd">
<fontconfig>
  <!-- Prefer Inter for sans-serif -->
  <alias>
    <family>sans-serif</family>
    <prefer>
      <family>Inter</family>
      <family>Noto Sans</family>
    </prefer>
  </alias>

  <!-- Prefer JetBrains Mono for monospace -->
  <alias>
    <family>monospace</family>
    <prefer>
      <family>JetBrains Mono</family>
      <family>Noto Sans Mono</family>
    </prefer>
  </alias>

  <!-- Enable good rendering -->
  <match target="font">
    <edit name="antialias" mode="assign"><bool>true</bool></edit>
    <edit name="hinting" mode="assign"><bool>true</bool></edit>
    <edit name="hintstyle" mode="assign"><const>hintslight</const></edit>
    <edit name="rgba" mode="assign"><const>rgb</const></edit>
    <edit name="lcdfilter" mode="assign"><const>lcddefault</const></edit>
  </match>
</fontconfig>
EOF

echo ""
echo "Fonts installed to ${FONT_DIR}"
echo "Preferred: Inter (UI), JetBrains Mono (terminal)"
