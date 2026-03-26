#!/usr/bin/env python3
"""
Framebuffer Color Test — run this on the Pi to find the correct
RGB565 encoding for your ST7789 TFT.

Draws 4 horizontal stripes using different encodings.
Look at the screen and report which stripe shows the correct colors:
  Stripe 1 (top):     RGB565, no byte-swap
  Stripe 2:           RGB565, byte-swapped
  Stripe 3:           BGR565, no byte-swap
  Stripe 4 (bottom):  BGR565, byte-swapped

Each stripe draws: RED | GREEN | BLUE | WHITE

Usage: python3 test_fb_colors.py
"""

import numpy as np
import sys

WIDTH = 320
HEIGHT = 240
FB_DEVICE = "/dev/fb1"

# Each stripe is HEIGHT/4 = 60 pixels tall
STRIPE_H = HEIGHT // 4
# Each color block is WIDTH/4 = 80 pixels wide
BLOCK_W = WIDTH // 4

# Target colors: Red, Green, Blue, White
COLORS = [
    (255, 0, 0),    # Red
    (0, 255, 0),    # Green
    (0, 0, 255),    # Blue
    (255, 255, 255),# White
]


def encode_rgb565(r, g, b):
    """Standard RGB565, no byte-swap."""
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | ((b & 0xF8) >> 3)

def encode_rgb565_swapped(r, g, b):
    """Standard RGB565, byte-swapped."""
    v = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | ((b & 0xF8) >> 3)
    return ((v & 0xFF) << 8) | ((v >> 8) & 0xFF)

def encode_bgr565(r, g, b):
    """BGR565 (swap R and B), no byte-swap."""
    return ((b & 0xF8) << 8) | ((g & 0xFC) << 3) | ((r & 0xF8) >> 3)

def encode_bgr565_swapped(r, g, b):
    """BGR565 (swap R and B), byte-swapped."""
    v = ((b & 0xF8) << 8) | ((g & 0xFC) << 3) | ((r & 0xF8) >> 3)
    return ((v & 0xFF) << 8) | ((v >> 8) & 0xFF)


ENCODERS = [
    ("RGB565 no-swap", encode_rgb565),
    ("RGB565 byte-swapped", encode_rgb565_swapped),
    ("BGR565 no-swap", encode_bgr565),
    ("BGR565 byte-swapped", encode_bgr565_swapped),
]


def main():
    frame = np.zeros((HEIGHT, WIDTH), dtype=np.uint16)

    for stripe_idx, (name, encoder) in enumerate(ENCODERS):
        y_start = stripe_idx * STRIPE_H
        y_end = y_start + STRIPE_H

        for col_idx, (r, g, b) in enumerate(COLORS):
            x_start = col_idx * BLOCK_W
            x_end = x_start + BLOCK_W
            pixel = encoder(r, g, b)
            frame[y_start:y_end, x_start:x_end] = pixel

    try:
        with open(FB_DEVICE, "wb") as fb:
            fb.write(frame.tobytes())
        print("Test pattern written to", FB_DEVICE)
        print()
        print("Look at your screen — you should see 4 horizontal stripes.")
        print("Each stripe has 4 color blocks: RED | GREEN | BLUE | WHITE")
        print()
        for i, (name, _) in enumerate(ENCODERS):
            print(f"  Stripe {i+1}: {name}")
        print()
        print("Which stripe shows the correct colors (RED GREEN BLUE WHITE)?")
        print("Tell me the stripe number (1, 2, 3, or 4).")
    except PermissionError:
        print(f"Permission denied! Run: sudo chmod 666 {FB_DEVICE}")
    except FileNotFoundError:
        print(f"{FB_DEVICE} not found — is your TFT configured?")


if __name__ == "__main__":
    main()
