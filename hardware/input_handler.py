"""
Input Handler — unified input abstraction.
Maps keyboard events (desktop) or GPIO button events (Pi)
into a common set of actions.
"""

import pygame
import config


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
    """Merges keyboard and GPIO buttons into unified input stream."""

    def __init__(self):
        self._gpio = None
        if config.IS_PI:
            try:
                from hardware.gpio_buttons import GpioButtons, ButtonEvent
                self._gpio = GpioButtons()
                self._ButtonEvent = ButtonEvent
            except Exception as e:
                print(f"[Input] GPIO buttons not available: {e}")

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

        # ── GPIO Buttons (Pi mode) ──────────────────────────────
        if self._gpio:
            BE = self._ButtonEvent
            _MAP = {
                BE.DPAD_UP:    InputAction.SCROLL_UP,
                BE.DPAD_DOWN:  InputAction.SCROLL_DOWN,
                BE.DPAD_LEFT:  InputAction.PREV_TRACK,
                BE.DPAD_RIGHT: InputAction.NEXT_TRACK,
                BE.BTN_A:      InputAction.SELECT,
                BE.BTN_B:      InputAction.BACK,
                BE.BTN_X:      InputAction.PLAY_PAUSE,
                BE.BTN_L:      InputAction.VOLUME_DOWN,
                BE.BTN_R:      InputAction.VOLUME_UP,
                BE.BTN_START:  InputAction.PLAY_PAUSE,
                BE.BTN_SELECT: InputAction.BACK,
            }
            for evt in self._gpio.get_events():
                action = _MAP.get(evt)
                if action:
                    self._actions.append(action)

        return self._actions

    def cleanup(self):
        """Release resources."""
        if self._gpio:
            self._gpio.cleanup()
