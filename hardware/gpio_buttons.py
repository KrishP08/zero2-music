"""
GPIO Button Driver — interrupt-based button input for Raspberry Pi.
Maps 14 gamepad-style buttons to player actions.
Falls back to no-op on non-Pi platforms.
"""

import time
import config


class ButtonEvent:
    """Possible button events."""
    DPAD_UP = "dpad_up"
    DPAD_DOWN = "dpad_down"
    DPAD_LEFT = "dpad_left"
    DPAD_RIGHT = "dpad_right"
    BTN_A = "btn_a"
    BTN_B = "btn_b"
    BTN_X = "btn_x"
    BTN_Y = "btn_y"
    BTN_L = "btn_l"
    BTN_R = "btn_r"
    BTN_L2 = "btn_l2"
    BTN_R2 = "btn_r2"
    BTN_START = "btn_start"
    BTN_SELECT = "btn_select"


# Map GPIO pin number → ButtonEvent
GPIO_BUTTON_MAP = {
    17: ButtonEvent.DPAD_UP,
    27: ButtonEvent.DPAD_DOWN,
    22: ButtonEvent.DPAD_LEFT,
    23: ButtonEvent.DPAD_RIGHT,
    4:  ButtonEvent.BTN_A,
    3:  ButtonEvent.BTN_B,
    2:  ButtonEvent.BTN_X,
    18: ButtonEvent.BTN_Y,
    5:  ButtonEvent.BTN_L,
    6:  ButtonEvent.BTN_R,
    12: ButtonEvent.BTN_L2,
    16: ButtonEvent.BTN_R2,
    20: ButtonEvent.BTN_START,
    21: ButtonEvent.BTN_SELECT,
}


class GpioButtons:
    """
    GPIO button handler with interrupt-based detection and debounce.
    On non-Pi platforms this is a no-op stub.
    """

    DEBOUNCE_MS = 150  # milliseconds

    def __init__(self):
        self._events = []
        self._gpio_available = False
        self._GPIO = None

        if config.IS_PI:
            self._setup_gpio()

    def _setup_gpio(self):
        """Initialize all GPIO button pins with pull-up and falling-edge interrupts."""
        try:
            import RPi.GPIO as GPIO
            self._GPIO = GPIO

            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BCM)

            for pin in GPIO_BUTTON_MAP:
                GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                GPIO.add_event_detect(
                    pin,
                    GPIO.FALLING,
                    callback=self._button_callback,
                    bouncetime=self.DEBOUNCE_MS,
                )

            self._gpio_available = True
            print(f"[GpioButtons] Initialized {len(GPIO_BUTTON_MAP)} buttons")

        except (ImportError, RuntimeError) as e:
            print(f"[GpioButtons] GPIO not available: {e}")
            self._gpio_available = False

    def _button_callback(self, channel):
        """Interrupt callback — enqueue the corresponding ButtonEvent."""
        event = GPIO_BUTTON_MAP.get(channel)
        if event:
            self._events.append(event)

    def get_events(self):
        """Drain and return all pending button events."""
        events = list(self._events)
        self._events.clear()
        return events

    def cleanup(self):
        """Release GPIO resources."""
        if self._gpio_available and self._GPIO:
            try:
                self._GPIO.cleanup(list(GPIO_BUTTON_MAP.keys()))
            except Exception:
                pass
