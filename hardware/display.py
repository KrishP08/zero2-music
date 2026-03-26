"""
Display — initializes the render surface and output method.

On desktop: regular Pygame window (unchanged).
On Pi:      Offscreen pygame.Surface + direct /dev/fb1 framebuffer output.
            No X server, no SDL display driver needed.
"""

import os
import pygame
import config


class Display:
    """Manages the display surface for the music player."""

    def __init__(self):
        self.width = config.SCREEN_WIDTH
        self.height = config.SCREEN_HEIGHT
        self.screen = None
        self._framebuffer = None

    def init(self):
        """Initialize the display. Call AFTER pygame.init()."""
        if config.IS_PI:
            return self._init_pi()
        else:
            return self._init_desktop()

    def _init_pi(self):
        """
        Pi mode: use SDL dummy driver for in-memory rendering,
        then output each frame to /dev/fb1 via the Framebuffer helper.
        """
        # SDL env vars are already set in main.py before pygame.init()
        # Just create the dummy display surface for pygame internals

        # Create a dummy display surface (required by pygame internals)
        # This won't appear on any screen — it's purely in-memory
        pygame.display.set_mode((1, 1))

        # Our actual render target is a plain offscreen Surface
        self.screen = pygame.Surface((self.width, self.height))

        # Open the framebuffer for direct writes
        from hardware.framebuffer import Framebuffer
        self._framebuffer = Framebuffer(
            device="/dev/fb1",
            width=self.width,
            height=self.height,
        )

        if self._framebuffer.available:
            self._framebuffer.clear()
            print(f"[Display] Pi mode: rendering to /dev/fb1 ({self.width}x{self.height})")
        else:
            print("[Display] ⚠ Framebuffer not available — rendering to offscreen surface only")

        return self.screen

    def _init_desktop(self):
        """Desktop mode: regular windowed pygame display."""
        self.screen = pygame.display.set_mode(
            (self.width, self.height)
        )
        pygame.display.set_caption("♪ Zero2 Music Player")
        return self.screen

    def update(self):
        """
        Push the current frame to the output.
        Pi:      convert to RGB565 → write to /dev/fb1
        Desktop: pygame.display.flip()
        """
        if config.IS_PI:
            if self._framebuffer and self._framebuffer.available:
                self._framebuffer.write(self.screen)
        else:
            # On desktop, the screen IS the display surface, so just flip
            pygame.display.flip()

    def cleanup(self):
        """Clean shutdown."""
        if self._framebuffer:
            self._framebuffer.close()

    @property
    def size(self):
        return (self.width, self.height)
