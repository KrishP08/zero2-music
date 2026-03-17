"""
Display — initializes the display surface.
On desktop: regular Pygame window.
On Pi: Could use SPI framebuffer or Pygame window via fbdev.
"""

import pygame
import config


class Display:
    """Manages the display surface for the music player."""

    def __init__(self):
        self.width = config.SCREEN_WIDTH
        self.height = config.SCREEN_HEIGHT
        self.screen = None

    def init(self):
        """Initialize the display. Call AFTER pygame.init()."""
        if config.IS_PI:
            # On Pi, use framebuffer. Pygame can render directly
            # to the Linux framebuffer via SDL.
            import os
            os.environ.setdefault("SDL_FBDEV", "/dev/fb1")
            os.environ.setdefault("SDL_VIDEODRIVER", "fbcon")

            try:
                self.screen = pygame.display.set_mode(
                    (self.width, self.height),
                    pygame.FULLSCREEN | pygame.NOFRAME
                )
                pygame.mouse.set_visible(False)
            except pygame.error:
                # Fallback to regular window if framebuffer not available
                print("[Display] Framebuffer not available, using window")
                self.screen = pygame.display.set_mode(
                    (self.width, self.height)
                )
        else:
            # Desktop mode — windowed
            self.screen = pygame.display.set_mode(
                (self.width, self.height)
            )
            pygame.display.set_caption("♪ Zero2 Music Player")

        return self.screen

    def update(self):
        """Flip the display buffer."""
        pygame.display.flip()

    @property
    def size(self):
        return (self.width, self.height)
