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

# SPI display pins (for Pi with ST7789 / ILI9341)
DISPLAY_SPI_PORT = 0
DISPLAY_SPI_CS = 0
DISPLAY_DC_PIN = 25
DISPLAY_RST_PIN = 27
DISPLAY_BL_PIN = 18

# ── Rotary Encoder GPIO Pins ───────────────────────────────────────
ROTARY_CLK_PIN = 17
ROTARY_DT_PIN = 22
ROTARY_SW_PIN = 23

# ── Audio ───────────────────────────────────────────────────────────
AUDIO_FREQUENCY = 44100
AUDIO_SIZE = -16
AUDIO_CHANNELS = 2
AUDIO_BUFFER = 2048

# ── Music Library ───────────────────────────────────────────────────
MUSIC_DIRECTORY = os.path.expanduser("~/Music")
SUPPORTED_FORMATS = (".mp3", ".flac", ".wav", ".ogg", ".m4a", ".aac")
LIBRARY_CACHE_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "library_cache.json"
)

# ── Theme ───────────────────────────────────────────────────────────
FONT_NAME = "Inter"
FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "fonts")
ICON_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "icons")
NOW_PLAYING_THEME = "square"

# ── Paths ───────────────────────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
