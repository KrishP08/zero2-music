#!/usr/bin/env python3
import uinput
import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

BUTTON_PINS = {
    'A':      4,
    'B':      3,
    'X':      2,
    'Y':      18,
    'L':      5,
    'R':      6,
    'START':  20,
    'SELECT': 21,
}

DPAD_PINS = {
    'UP':    17,
    'DOWN':  27,
    'LEFT':  22,
    'RIGHT': 23,
}

all_pins = list(BUTTON_PINS.values()) + list(DPAD_PINS.values())
for pin in all_pins:
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

events = (
    uinput.BTN_SOUTH,
    uinput.BTN_EAST,
    uinput.BTN_NORTH,
    uinput.BTN_WEST,
    uinput.BTN_TL,
    uinput.BTN_TR,
    uinput.BTN_START,
    uinput.BTN_SELECT,
    uinput.ABS_X + (-1, 1, 0, 0),
    uinput.ABS_Y + (-1, 1, 0, 0),
)

device = uinput.Device(events, name="GPIO Joystick")
print("GPIO Joystick running! Press Ctrl+C to stop.")

BUTTON_EVENTS = {
    'A':      uinput.BTN_SOUTH,
    'B':      uinput.BTN_EAST,
    'X':      uinput.BTN_NORTH,
    'Y':      uinput.BTN_WEST,
    'L':      uinput.BTN_TL,
    'R':      uinput.BTN_TR,
    'START':  uinput.BTN_START,
    'SELECT': uinput.BTN_SELECT,
}

prev = {pin: 1 for pin in all_pins}

try:
    while True:
        # Handle buttons
        for name, pin in BUTTON_PINS.items():
            state = GPIO.input(pin)
            if state != prev[pin]:
                device.emit(BUTTON_EVENTS[name], 1 if state == 0 else 0)
                print(f"{'PRESSED' if state==0 else 'RELEASED'} {name}")
                prev[pin] = state

        # Handle dpad
        up    = GPIO.input(DPAD_PINS['UP'])
        down  = GPIO.input(DPAD_PINS['DOWN'])
        left  = GPIO.input(DPAD_PINS['LEFT'])
        right = GPIO.input(DPAD_PINS['RIGHT'])

        if up == 0:
            device.emit(uinput.ABS_Y, -1)
        elif down == 0:
            device.emit(uinput.ABS_Y, 1)
        else:
            device.emit(uinput.ABS_Y, 0)

        if left == 0:
            device.emit(uinput.ABS_X, -1)
        elif right == 0:
            device.emit(uinput.ABS_X, 1)
        else:
            device.emit(uinput.ABS_X, 0)

        time.sleep(0.01)

except KeyboardInterrupt:
    print("\nStopped!")
    GPIO.cleanup()
pi@retropie:~/bluez-alsa/build$
