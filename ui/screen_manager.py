"""
Screen Manager — navigation stack with slide transitions.
Manages which screen is active, handles push/pop, and renders transitions.
"""

import pygame
import config


class ScreenManager:
    """Manages a stack of screens with animated transitions."""

    def __init__(self, display_surface):
        self.surface = display_surface
        self._stack = []
        self._transition = None
        self._transition_progress = 0.0
        self._transition_speed = 8.0  # in units per frame (0→1 scale)
        self._transition_from_surface = None
        self._transition_to_surface = None

    @property
    def current_screen(self):
        if self._stack:
            return self._stack[-1]
        return None

    def push(self, screen, animate=True):
        """Push a new screen onto the stack with a slide-left transition."""
        if animate and self._stack:
            self._start_transition("slide_left", screen)
        self._stack.append(screen)
        screen.on_enter()

    def pop(self, animate=True):
        """Pop the top screen with a slide-right transition."""
        if len(self._stack) <= 1:
            return  # Don't pop the root screen

        old_screen = self._stack.pop()
        old_screen.on_exit()

        if animate and self._stack:
            self._start_transition("slide_right", None, old_screen)

        if self._stack:
            self._stack[-1].on_enter()

    def replace(self, screen, animate=False):
        """Replace the current screen."""
        if self._stack:
            old = self._stack.pop()
            old.on_exit()
        self._stack.append(screen)
        screen.on_enter()

    def handle_input(self, action):
        """Forward input to the current screen."""
        if self._transition:
            return  # Ignore input during transitions
        if self.current_screen:
            self.current_screen.handle_input(action)

    def update(self, dt):
        """Update transition animations and current screen."""
        if self._transition:
            self._transition_progress += self._transition_speed * dt
            if self._transition_progress >= 1.0:
                self._transition = None
                self._transition_progress = 0.0

        if self.current_screen:
            self.current_screen.update(dt)

    def render(self, surface):
        """Render the current screen, with transition if active."""
        w = config.SCREEN_WIDTH

        if self._transition and self._transition_from_surface:
            # Ease-out cubic
            t = self._transition_progress
            t = 1.0 - (1.0 - t) ** 3

            if self._transition == "slide_left":
                # Old screen slides left, new screen slides in from right
                offset_old = int(-w * t)
                offset_new = int(w * (1.0 - t))

                surface.blit(self._transition_from_surface, (offset_old, 0))
                if self.current_screen:
                    self.current_screen.render(surface, x_offset=offset_new)

            elif self._transition == "slide_right":
                # Old screen slides right, previous screen slides in from left
                offset_old = int(w * t)
                offset_new = int(-w * (1.0 - t))

                surface.blit(self._transition_from_surface, (offset_old, 0))
                if self.current_screen:
                    self.current_screen.render(surface, x_offset=offset_new)
        else:
            if self.current_screen:
                self.current_screen.render(surface)

    def _start_transition(self, direction, new_screen=None, old_screen=None):
        """Capture current screen and start transition animation."""
        self._transition = direction
        self._transition_progress = 0.0

        # Capture current screen to a surface
        self._transition_from_surface = pygame.Surface(
            (config.SCREEN_WIDTH, config.SCREEN_HEIGHT)
        )

        target = old_screen or (self._stack[-1] if self._stack else None)
        if target:
            target.render(self._transition_from_surface)


class Screen:
    """Base class for all screens."""

    def __init__(self, app):
        """
        Args:
            app: reference to the main App for accessing audio, library, etc.
        """
        self.app = app

    def on_enter(self):
        """Called when screen becomes active."""
        pass

    def on_exit(self):
        """Called when screen is removed from view."""
        pass

    def handle_input(self, action):
        """Handle an InputAction."""
        pass

    def update(self, dt):
        """Update logic (called every frame)."""
        pass

    def render(self, surface, x_offset=0):
        """Render the screen content to the surface."""
        pass
