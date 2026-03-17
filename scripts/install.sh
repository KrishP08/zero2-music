#!/bin/bash
# ─────────────────────────────────────────────────────────────────
# Zero2 Music Player — Pi Install Script
# Run on your Raspberry Pi Zero 2 W
# ─────────────────────────────────────────────────────────────────

set -e

echo "🎵 Zero2 Music Player — Installation"
echo "───────────────────────────────────────"

# System dependencies
echo "[1/4] Installing system dependencies..."
sudo apt-get update -qq
sudo apt-get install -y -qq \
    python3-pip \
    python3-pygame \
    python3-pil \
    python3-rpi.gpio \
    libsdl2-dev \
    libsdl2-image-dev \
    libsdl2-mixer-dev \
    libsdl2-ttf-dev

# Python dependencies
echo "[2/4] Installing Python packages..."
pip3 install --user mutagen

# Create music directory
echo "[3/4] Setting up directories..."
mkdir -p ~/Music
mkdir -p "$(dirname "$0")/assets/fonts"
mkdir -p "$(dirname "$0")/assets/icons"

# Download Inter font
echo "[4/4] Downloading Inter font..."
FONT_DIR="$(dirname "$0")/assets/fonts"
if [ ! -f "$FONT_DIR/Inter-Regular.ttf" ]; then
    wget -q -O /tmp/inter.zip "https://github.com/rsms/inter/releases/download/v4.0/Inter-4.0.zip" 2>/dev/null || true
    if [ -f /tmp/inter.zip ]; then
        unzip -q -o /tmp/inter.zip -d /tmp/inter 2>/dev/null || true
        find /tmp/inter -name "Inter-Regular.ttf" -exec cp {} "$FONT_DIR/" \; 2>/dev/null || true
        find /tmp/inter -name "Inter-Bold.ttf" -exec cp {} "$FONT_DIR/" \; 2>/dev/null || true
        rm -rf /tmp/inter /tmp/inter.zip
        echo "   ✓ Inter font installed"
    else
        echo "   ⚠ Could not download Inter font (will use system fallback)"
    fi
else
    echo "   ✓ Inter font already present"
fi

echo ""
echo "───────────────────────────────────────"
echo "✅ Installation complete!"
echo ""
echo "To run:"
echo "  cd '$(dirname "$0")'"
echo "  python3 main.py"
echo ""
echo "Add your music files to ~/Music"
echo "───────────────────────────────────────"
