"""
Input Handler — unified input abstraction.
Maps keyboard events (desktop) or rotary encoder events (Pi)
into a common set of actions.
"""

import pygame
import config
from hardware.rotary_encoder import RotaryEncoder, RotaryEvent


class InputAction:
    """Unified input actions consumed by the UI."""
    SCROLL_UP = "scroll_up"
    SCROLL_DOWN = "scroll_down"
    SELECT = "select"
    BACK = "back"
    PLAY_PAUSE = "play_pause"
    NEXT_TRACK = "next_track"
    PREV_TRACK = "prev_track"
    VOLUME_UP = "volume_up"
    VOLUME_DOWN = "volume_down"
    NONE = None


class InputHandler:
    """Merges keyboard and rotary encoder into unified input stream."""

    def __init__(self):
        self._rotary = RotaryEncoder() if config.IS_PI else None
        self._actions = []

    def poll(self):
        """
        Poll for input events. Call once per frame.
        Returns list of InputAction values.
        """
        self._actions.clear()

        # ── Keyboard (desktop mode) ─────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._actions.append("__QUIT__")

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self._actions.append(InputAction.SCROLL_UP)
                elif event.key == pygame.K_DOWN:
                    self._actions.append(InputAction.SCROLL_DOWN)
                elif event.key == pygame.K_RETURN:
                    self._actions.append(InputAction.SELECT)
                elif event.key == pygame.K_ESCAPE:
                    self._actions.append(InputAction.BACK)
                elif event.key == pygame.K_SPACE:
                    self._actions.append(InputAction.PLAY_PAUSE)
                elif event.key == pygame.K_RIGHT:
                    self._actions.append(InputAction.NEXT_TRACK)
                elif event.key == pygame.K_LEFT:
                    self._actions.append(InputAction.PREV_TRACK)
                elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                    self._actions.append(InputAction.VOLUME_UP)
                elif event.key == pygame.K_MINUS:
                    self._actions.append(InputAction.VOLUME_DOWN)

            # Pass pygame events through for audio engine
            elif event.type == pygame.USEREVENT + 1:
                self._actions.append(("__PYGAME_EVENT__", event))

        # ── Rotary encoder (Pi mode) ────────────────────────────
        if self._rotary:
            for evt in self._rotary.get_events():
                if evt == RotaryEvent.CLOCKWISE:
                    self._actions.append(InputAction.SCROLL_DOWN)
                elif evt == RotaryEvent.COUNTER_CLOCKWISE:
                    self._actions.append(InputAction.SCROLL_UP)
                elif evt == RotaryEvent.BUTTON_PRESS:
                    self._actions.append(InputAction.SELECT)
                elif evt == RotaryEvent.BUTTON_LONG_PRESS:
                    self._actions.append(InputAction.BACK)

        return self._actions

    def cleanup(self):
        """Release resources."""
        if self._rotary:
            self._rotary.cleanup()
