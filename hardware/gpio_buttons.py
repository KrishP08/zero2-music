"""
GPIO Button Driver — interrupt-based button input for Raspberry Pi.
Tries gpiozero first, falls back to RPi.GPIO.
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

# Name → ButtonEvent (for gpiozero path)
_NAME_TO_EVENT = {
    "DPAD_UP":    ButtonEvent.DPAD_UP,
    "DPAD_DOWN":  ButtonEvent.DPAD_DOWN,
    "DPAD_LEFT":  ButtonEvent.DPAD_LEFT,
    "DPAD_RIGHT": ButtonEvent.DPAD_RIGHT,
    "A":          ButtonEvent.BTN_A,
    "B":          ButtonEvent.BTN_B,
    "X":          ButtonEvent.BTN_X,
    "Y":          ButtonEvent.BTN_Y,
    "L":          ButtonEvent.BTN_L,
    "R":          ButtonEvent.BTN_R,
    "L2":         ButtonEvent.BTN_L2,
    "R2":         ButtonEvent.BTN_R2,
    "START":      ButtonEvent.BTN_START,
    "SELECT":     ButtonEvent.BTN_SELECT,
}


class GpioButtons:
    """
    GPIO button handler with interrupt-based detection.
    Tries gpiozero first, falls back to RPi.GPIO.
    """

    DEBOUNCE_MS = 150

    def __init__(self):
        self._events = []
        self._gpio_available = False
        self._buttons = {}
        self._GPIO = None

        if config.IS_PI:
            # Try gpiozero first (preferred on Bookworm)
            if self._try_gpiozero():
                return
            # Fall back to RPi.GPIO
            if self._try_rpi_gpio():
                return
            print("[GpioButtons] ⚠ No GPIO library available!")
            print("[GpioButtons]   Install: sudo apt install python3-gpiozero python3-rpi.gpio")

    def _try_gpiozero(self):
        """Try to set up buttons using gpiozero."""
        try:
            from gpiozero import Button

            def make_callback(evt):
                return lambda: self._events.append(evt)

            pins = config.GPIO_BUTTONS
            for name, pin in pins.items():
                evt = _NAME_TO_EVENT.get(name)
                if evt:
                    try:
                        btn = Button(pin, pull_up=True, bounce_time=0.05)
                        btn.when_pressed = make_callback(evt)
                        self._buttons[name] = btn
                    except Exception as e:
                        print(f"[GpioButtons] ⚠ Pin {pin} ({name}): {e}")

            self._gpio_available = True
            print(f"[GpioButtons] Initialized {len(self._buttons)} buttons (gpiozero)")
            return True
        except ImportError:
            return False
        except Exception as e:
            print(f"[GpioButtons] gpiozero failed: {e}")
            return False

    def _try_rpi_gpio(self):
        """Fall back to RPi.GPIO."""
        try:
            import RPi.GPIO as GPIO
            self._GPIO = GPIO

            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BCM)

            for pin, evt in GPIO_BUTTON_MAP.items():
                try:
                    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                    GPIO.add_event_detect(
                        pin,
                        GPIO.FALLING,
                        callback=self._rpi_callback,
                        bouncetime=self.DEBOUNCE_MS,
                    )
                except Exception as e:
                    print(f"[GpioButtons] ⚠ Pin {pin}: {e}")

            self._gpio_available = True
            print(f"[GpioButtons] Initialized {len(GPIO_BUTTON_MAP)} buttons (RPi.GPIO)")
            return True
        except ImportError:
            return False
        except Exception as e:
            print(f"[GpioButtons] RPi.GPIO failed: {e}")
            return False

    def _rpi_callback(self, channel):
        """RPi.GPIO interrupt callback."""
        evt = GPIO_BUTTON_MAP.get(channel)
        if evt:
            self._events.append(evt)

    def get_events(self):
        """Drain and return all pending button events."""
        events = list(self._events)
        self._events.clear()
        return events

    def cleanup(self):
        """Release GPIO resources."""
        # gpiozero cleanup
        for btn in self._buttons.values():
            try:
                btn.close()
            except Exception:
                pass
        # RPi.GPIO cleanup
        if self._GPIO:
            try:
                self._GPIO.cleanup(list(GPIO_BUTTON_MAP.keys()))
            except Exception:
                pass
