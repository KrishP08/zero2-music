"""
Configuration for the iPod Clone Music Player.
Auto-detects Pi vs Desktop environment.
"""

import os
import platform

# ── Platform Detection ──────────────────────────────────────────────
IS_PI = os.path.exists("/proc/device-tree/model") and "raspberry" in open(
    "/proc/device-tree/model"
).read().lower()

# ── Display Settings ────────────────────────────────────────────────
SCREEN_WIDTH = 320
SCREEN_HEIGHT = 240
FPS = 30

# SPI display pins (matched to /boot/firmware/config.txt)
DISPLAY_SPI_PORT = 0
DISPLAY_SPI_CS = 0
DISPLAY_DC_PIN = 24
DISPLAY_RST_PIN = 25

# ── GPIO Button Pins (gamepad layout) ──────────────────────────────
GPIO_BUTTONS = {
    "DPAD_UP":   17,
    "DPAD_DOWN": 27,
    "DPAD_LEFT": 22,
    "DPAD_RIGHT":23,
    "A":         4,
    "B":         3,
    "X":         2,
    "Y":         18,
    "L":         5,
    "R":         6,
    "L2":        12,
    "R2":        16,
    "START":     20,
    "SELECT":    21,
}

# ── Volume ──────────────────────────────────────────────────────────
VOLUME_STEP = 0.05

# ── Audio ───────────────────────────────────────────────────────────
AUDIO_FREQUENCY = 44100
AUDIO_SIZE = -16
AUDIO_CHANNELS = 2
AUDIO_BUFFER = 2048

# ── Music Library ───────────────────────────────────────────────────
MUSIC_DIRECTORY = "/home/krish/Music"
SUPPORTED_FORMATS = (".mp3", ".flac", ".wav", ".ogg", ".m4a", ".aac")
LIBRARY_CACHE_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "library_cache.json"
)

# ── Theme ───────────────────────────────────────────────────────────
FONT_NAME = "Inter"
FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "fonts")
ICON_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "icons")
THEME = "modern"

# ── Paths ───────────────────────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
