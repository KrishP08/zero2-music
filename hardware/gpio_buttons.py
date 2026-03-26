"""
GPIO Button Driver — interrupt-based button input for Raspberry Pi.
Uses gpiozero for better compatibility on Bookworm/Zero 2.
"""

import config
import threading

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

class GpioButtons:
    """
    GPIO button handler using gpiozero.
    """
    def __init__(self):
        self._events = []
        self._buttons = {}
        self._gpio_available = False

        if config.IS_PI:
            self._setup_gpio()

    def _setup_gpio(self):
        try:
            from gpiozero import Button
            
            # Map name to pin
            pins = config.GPIO_BUTTONS
            
            # Helper to create callback
            def make_callback(evt_name):
                return lambda: self._events.append(evt_name)

            # Define button mapping
            btn_map = {
                "DPAD_UP":   ButtonEvent.DPAD_UP,
                "DPAD_DOWN": ButtonEvent.DPAD_DOWN,
                "DPAD_LEFT": ButtonEvent.DPAD_LEFT,
                "DPAD_RIGHT": ButtonEvent.DPAD_RIGHT,
                "A":         ButtonEvent.BTN_A,
                "B":         ButtonEvent.BTN_B,
                "X":         ButtonEvent.BTN_X,
                "Y":         ButtonEvent.BTN_Y,
                "L":         ButtonEvent.BTN_L,
                "R":         ButtonEvent.BTN_R,
                "L2":        ButtonEvent.BTN_L2,
                "R2":        ButtonEvent.BTN_R2,
                "START":     ButtonEvent.BTN_START,
                "SELECT":    ButtonEvent.BTN_SELECT,
            }

            for name, pin in pins.items():
                if name in btn_map:
                    evt = btn_map[name]
                    # pull_up=True is default for Button
                    try:
                        btn = Button(pin, pull_up=True, bounce_time=0.05)
                        btn.when_pressed = make_callback(evt)
                        self._buttons[name] = btn
                    except Exception as e:
                        print(f"[GpioButtons] ⚠ Could not init pin {pin} ({name}): {e}")

            self._gpio_available = True
            print(f"[GpioButtons] Initialized {len(self._buttons)} buttons via gpiozero")
        except Exception as e:
            print(f"[GpioButtons] ⚠ GPIO not available (Bookworm may need lgpio): {e}")

    def get_events(self):
        events = list(self._events)
        self._events.clear()
        return events

    def cleanup(self):
        # gpiozero handles cleanup usually, but we can close explicitly
        for btn in self._buttons.values():
            try:
                btn.close()
            except:
                pass
