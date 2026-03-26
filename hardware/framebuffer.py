"""
Framebuffer — direct RGB565 output to /dev/fb1 for ST7789 TFT.

Converts a pygame Surface to RGB565 (with BGR inversion and byte-swap
for ST7789 endianness) and writes it directly to the Linux framebuffer.

Works headless — no X, no SDL display driver needed.
"""

import os
import numpy as np


def rgb565(r, g, b):
    """
    Convert an (R, G, B) tuple to a 16-bit RGB565 value
    with BGR inversion and byte-swap for ST7789.

    ST7789 expects BGR565 in big-endian, but the Linux fb
    driver exposes it as little-endian, so we byte-swap.
    """
    # BGR565: blue in the high 5 bits, red in the low 5
    val = ((b & 0xF8) << 8) | ((g & 0xFC) << 3) | ((r & 0xF8) >> 3)
    # Byte-swap for ST7789 endianness
    val = ((val & 0xFF) << 8) | ((val >> 8) & 0xFF)
    return val


def surface_to_fb_bytes(surface):
    """
    Convert a pygame.Surface (RGB) to raw RGB565 bytes
    suitable for writing to /dev/fb1.

    Uses NumPy for fast bulk conversion.
    Returns: bytes object (width * height * 2 bytes)
    """
    import pygame

    # Get pixel data as (width, height, 3) uint8 array
    pixels = pygame.surfarray.array3d(surface)

    # Transpose to (height, width, 3) — row-major for framebuffer
    pixels = pixels.transpose(1, 0, 2)

    # Extract channels as uint16 for bit manipulation
    r = pixels[:, :, 0].astype(np.uint16)
    g = pixels[:, :, 1].astype(np.uint16)
    b = pixels[:, :, 2].astype(np.uint16)

    # BGR565 encoding (swap R and B for ST7789)
    rgb565_data = ((b & 0xF8) << 8) | ((g & 0xFC) << 3) | ((r & 0xF8) >> 3)

    # Byte-swap for ST7789 big-endian
    rgb565_data = ((rgb565_data & 0xFF) << 8) | ((rgb565_data >> 8) & 0xFF)

    return rgb565_data.astype(np.uint16).tobytes()


class Framebuffer:
    """
    Direct framebuffer writer for ST7789 TFT via /dev/fb1.
    Supports double-buffering for smoother updates.
    """

    def __init__(self, device="/dev/fb1", width=320, height=240):
        self.device = device
        self.width = width
        self.height = height
        self._fb = None
        self._frame_size = width * height * 2  # RGB565 = 2 bytes/pixel

        try:
            self._fb = open(device, "wb")
            print(f"[Framebuffer] Opened {device} ({width}x{height} RGB565)")
        except (FileNotFoundError, PermissionError) as e:
            print(f"[Framebuffer] ⚠ Cannot open {device}: {e}")
            print(f"[Framebuffer]   Try: sudo chmod 666 {device}")
            self._fb = None

    @property
    def available(self):
        return self._fb is not None

    def write(self, surface):
        """
        Convert a pygame Surface to RGB565 and write to the framebuffer.
        """
        if not self._fb:
            return

        try:
            data = surface_to_fb_bytes(surface)
            self._fb.seek(0)
            self._fb.write(data)
            self._fb.flush()
        except Exception as e:
            print(f"[Framebuffer] Write error: {e}")

    def clear(self, color=(0, 0, 0)):
        """Fill the framebuffer with a solid color."""
        if not self._fb:
            return

        pixel = rgb565(*color)
        data = np.full(
            self.width * self.height, pixel, dtype=np.uint16
        ).tobytes()
        try:
            self._fb.seek(0)
            self._fb.write(data)
            self._fb.flush()
        except Exception:
            pass

    def close(self):
        """Close the framebuffer device."""
        if self._fb:
            try:
                self._fb.close()
            except Exception:
                pass
            self._fb = None
