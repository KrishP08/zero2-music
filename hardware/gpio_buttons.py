"""
GPIO Button Driver — polling-based button input for Raspberry Pi.
Uses GPIO.input() polling (like pyjoy.py) instead of edge detection,
which is broken on Bookworm's kernel.
"""

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


# Pin → event mapping
_PIN_MAP = {
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
    Polling-based GPIO button handler.
    Call poll() once per frame — it reads pin states and detects
    press transitions (HIGH→LOW = button pressed).
    """

    def __init__(self):
        self._events = []
        self._gpio_available = False
        self._GPIO = None
        self._prev_state = {}  # pin → previous state (1=released, 0=pressed)

        if config.IS_PI:
            self._setup_gpio()

    def _setup_gpio(self):
        """Set up all GPIO pins with pull-up resistors."""
        try:
            import RPi.GPIO as GPIO
            self._GPIO = GPIO

            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BCM)

            for pin in _PIN_MAP:
                GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                self._prev_state[pin] = 1  # released

            self._gpio_available = True
            print(f"[GpioButtons] Initialized {len(_PIN_MAP)} buttons (polling)")

        except ImportError:
            print("[GpioButtons] ⚠ RPi.GPIO not found")
            print("[GpioButtons]   Install: sudo apt install python3-rpi.gpio")
        except Exception as e:
            print(f"[GpioButtons] ⚠ GPIO init failed: {e}")

    def poll(self):
        """
        Read all button states. Call once per frame.
        Returns list of ButtonEvent for buttons that were JUST pressed.
        """
        self._events.clear()

        if not self._gpio_available:
            return self._events

        GPIO = self._GPIO
        for pin, evt in _PIN_MAP.items():
            state = GPIO.input(pin)  # 0 = pressed (pull-up), 1 = released

            # Detect press transition: was released (1), now pressed (0)
            if state == 0 and self._prev_state[pin] == 1:
                self._events.append(evt)

            self._prev_state[pin] = state

        return self._events

    def get_events(self):
        """Compatibility — same as poll()."""
        return self.poll()

    def cleanup(self):
        """Release GPIO resources."""
        if self._gpio_available and self._GPIO:
            try:
                self._GPIO.cleanup(list(_PIN_MAP.keys()))
            except Exception:
                pass
