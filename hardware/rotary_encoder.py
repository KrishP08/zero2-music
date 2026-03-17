"""
Rotary Encoder Driver — GPIO-based rotary encoder with interrupt detection.
Falls back to no-op on non-Pi platforms.
"""

import config


class RotaryEvent:
    CLOCKWISE = "cw"
    COUNTER_CLOCKWISE = "ccw"
    BUTTON_PRESS = "press"
    BUTTON_LONG_PRESS = "long_press"


class RotaryEncoder:
    """
    GPIO rotary encoder with debounce and direction detection.
    On non-Pi platforms, this is a no-op stub.
    """

    def __init__(self, clk_pin=None, dt_pin=None, sw_pin=None):
        self.clk_pin = clk_pin or config.ROTARY_CLK_PIN
        self.dt_pin = dt_pin or config.ROTARY_DT_PIN
        self.sw_pin = sw_pin or config.ROTARY_SW_PIN

        self._events = []
        self._last_clk = 0
        self._button_down_time = 0
        self._long_press_ms = 600
        self._gpio_available = False

        if config.IS_PI:
            self._setup_gpio()

    def _setup_gpio(self):
        """Initialize GPIO pins with interrupts."""
        try:
            import RPi.GPIO as GPIO
            self._GPIO = GPIO

            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.clk_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.dt_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.sw_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

            self._last_clk = GPIO.input(self.clk_pin)

            GPIO.add_event_detect(
                self.clk_pin,
                GPIO.BOTH,
                callback=self._rotation_callback,
                bouncetime=2
            )
            GPIO.add_event_detect(
                self.sw_pin,
                GPIO.FALLING,
                callback=self._button_callback,
                bouncetime=200
            )

            self._gpio_available = True
            print("[Rotary] GPIO initialized")

        except (ImportError, RuntimeError) as e:
            print(f"[Rotary] GPIO not available: {e}")
            self._gpio_available = False

    def _rotation_callback(self, channel):
        """Interrupt callback for rotation."""
        import RPi.GPIO as GPIO
        import time

        clk_state = GPIO.input(self.clk_pin)
        dt_state = GPIO.input(self.dt_pin)

        if clk_state != self._last_clk:
            if dt_state != clk_state:
                self._events.append(RotaryEvent.CLOCKWISE)
            else:
                self._events.append(RotaryEvent.COUNTER_CLOCKWISE)
        self._last_clk = clk_state

    def _button_callback(self, channel):
        """Interrupt callback for button press."""
        import time
        self._button_down_time = time.time()
        self._events.append(RotaryEvent.BUTTON_PRESS)

    def get_events(self):
        """Drain and return all pending events."""
        events = list(self._events)
        self._events.clear()
        return events

    def cleanup(self):
        """Cleanup GPIO resources."""
        if self._gpio_available:
            try:
                self._GPIO.cleanup([self.clk_pin, self.dt_pin, self.sw_pin])
            except Exception:
                pass
