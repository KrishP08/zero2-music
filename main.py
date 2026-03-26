#!/usr/bin/env python3
"""
Zero2 Music Player — iPod Clone for Raspberry Pi Zero 2 W
Innioasis Y1-inspired glassmorphic dark theme.

Desktop: python main.py
Pi:      python main.py

Controls (desktop):
  ↑/↓      Scroll / Volume (on Now Playing)
  Enter    Select
  Escape   Back
  Space    Play/Pause
  ←/→      Prev/Next track
  +/-      Volume
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config

# ── Set SDL environment BEFORE importing/initializing pygame ────────
# This MUST happen before pygame.init() touches the audio/video drivers
if config.IS_PI:
    os.environ["SDL_AUDIODRIVER"] = "alsa"
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    os.environ["SDL_NOMOUSE"] = "1"

import pygame
from core.audio_engine import AudioEngine
from core.music_library import MusicLibrary
from core.playlist import Playlist
from core.bluetooth_manager import BluetoothManager
from core.wifi_manager import WiFiManager
from hardware.display import Display
from hardware.input_handler import InputHandler, InputAction
from ui.screen_manager import ScreenManager
from ui.screens.main_menu import MainMenuScreen
from core.cava_visualizer import CavaVisualizer


class App:
    """
    Main application — ties together audio, library, UI, and input.
    All screens receive a reference to this object.
    """

    def __init__(self):
        # ── Initialize Pygame ───────────────────────────────────
        pygame.init()

        # ── Display ─────────────────────────────────────────────
        self.display = Display()
        self.screen = self.display.init()

        # ── Audio ───────────────────────────────────────────────
        self.audio = AudioEngine(
            frequency=config.AUDIO_FREQUENCY,
            size=config.AUDIO_SIZE,
            channels=config.AUDIO_CHANNELS,
            buffer=config.AUDIO_BUFFER,
        )

        # ── Music Library ───────────────────────────────────────
        self.library = MusicLibrary()
        print("[App] Scanning music library...")
        if not self.library.load_cache():
            self.library.scan()
            self.library.save_cache()
        print(f"[App] Library: {len(self.library.tracks)} tracks ready")

        # ── Playlist / Queue ────────────────────────────────────
        self.playlist = Playlist()

        # ── Bluetooth ───────────────────────────────────────────
        self.bluetooth = BluetoothManager()
        print(f"[App] Bluetooth: {'available' if self.bluetooth.available else 'not available'}")

        # ── WiFi ────────────────────────────────────────────────
        self.wifi = WiFiManager()
        print(f"[App] WiFi: {'available' if self.wifi.available else 'not available'}")

        # ── Visualizer ──────────────────────────────────────────
        self.cava = CavaVisualizer(bars=32)
        self.cava.start()

        # ── Input ───────────────────────────────────────────────
        self.input = InputHandler()

        # ── Screen Manager ──────────────────────────────────────
        self.screen_manager = ScreenManager(self.screen)

        # Register audio end-of-track handler
        self.audio.on("on_track_end", self._on_track_end)

        # ── Clock ───────────────────────────────────────────────
        self.clock = pygame.time.Clock()
        self.running = True

    def _on_track_end(self):
        """Called when a track finishes playing — auto-advance."""
        current = self.playlist.current_track
        if current:
            current.play_count += 1
            self.library.save_cache()
            
        track = self.playlist.next_track()
        if track:
            self.audio.play(track.filepath)

    def run(self):
        """Main loop."""
        # Start with main menu
        main_menu = MainMenuScreen(self)
        self.screen_manager.push(main_menu, animate=False)

        print("[App] ♪ Zero2 Music Player running!")
        print("[App] Use arrow keys to navigate, Enter to select, Esc to go back")

        while self.running:
            dt = self.clock.tick(config.FPS) / 1000.0

            # ── Input ───────────────────────────────────────────
            actions = self.input.poll()
            for action in actions:
                if action == "__QUIT__":
                    self.running = False
                    break
                elif isinstance(action, tuple) and action[0] == "__PYGAME_EVENT__":
                    self.audio.handle_event(action[1])
                elif action == InputAction.VOLUME_UP:
                    self.audio.volume_up(config.VOLUME_STEP)
                elif action == InputAction.VOLUME_DOWN:
                    self.audio.volume_down(config.VOLUME_STEP)
                else:
                    self.screen_manager.handle_input(action)

            # ── Update ──────────────────────────────────────────
            self.screen_manager.update(dt)

            # ── Render ──────────────────────────────────────────
            self.screen_manager.render(self.screen)

            # ── Flip ────────────────────────────────────────────
            self.display.update()

        self._cleanup()

    def _cleanup(self):
        """Graceful shutdown."""
        print("[App] Shutting down...")
        self.cava.stop()
        self.audio.cleanup()
        self.bluetooth.cleanup()
        self.wifi.cleanup()
        self.input.cleanup()
        self.display.cleanup()
        pygame.quit()


def main():
    # Ensure music directory exists
    os.makedirs(config.MUSIC_DIRECTORY, exist_ok=True)

    # Ensure assets directories exist
    os.makedirs(config.FONT_DIR, exist_ok=True)
    os.makedirs(config.ICON_DIR, exist_ok=True)

    app = App()
    app.run()


if __name__ == "__main__":
    main()
