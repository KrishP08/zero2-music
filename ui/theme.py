"""
Theme — Tack UI inspired dark theme with blue accent.
Defines colors, fonts, and rendering helpers for the player UI.
Landscape 320×240 optimized.
"""

import pygame
import os
import config


# ════════════════════════════════════════════════════════════════════
#  COLOR PALETTE  — deep dark with blue accent (#257BF4)
# ════════════════════════════════════════════════════════════════════
class Colors:
    # Backgrounds
    BG_DARK = (10, 15, 22)           # #0A0F16
    BG_GRADIENT_TOP = (12, 17, 26)
    BG_GRADIENT_BOTTOM = (8, 12, 18)
    BG_CARD = (22, 30, 41)           # #161E29
    BG_CARD_HIGHLIGHT = (30, 40, 56)

    # Accent — Blue
    ACCENT = (37, 123, 244)          # #257BF4
    ACCENT_DIM = (25, 90, 180)
    ACCENT_GLOW = (37, 123, 244, 60)
    ACCENT_DARK = (18, 60, 120)

    # Text
    TEXT_PRIMARY = (240, 242, 250)
    TEXT_SECONDARY = (140, 150, 175)
    TEXT_MUTED = (80, 90, 110)

    # UI Elements
    HIGHLIGHT_BG = (37, 123, 244, 30)
    DIVIDER = (30, 36, 55)
    PROGRESS_BG = (30, 36, 55)
    PROGRESS_FILL = (37, 123, 244)

    # Glass
    GLASS_BG = (20, 24, 44, 180)
    GLASS_BORDER = (60, 70, 100, 100)

    # Status
    BATTERY_GREEN = (80, 220, 120)
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    TRANSPARENT = (0, 0, 0, 0)

    # Badge colors
    BADGE_FLAC = (37, 123, 244)
    BADGE_MP3 = (80, 90, 110)
    # Retro Theme Constants
    RETRO_PRIMARY = (242, 147, 13)       # #f2930d
    RETRO_BG_LIGHT = (248, 247, 245)     # #f8f7f5
    RETRO_BG_DARK = (34, 27, 16)         # #221b10
    RETRO_ORANGE_DARK = (153, 51, 0)     # active state border/accents

# ════════════════════════════════════════════════════════════════════
#  FONT MANAGER — Space Grotesk
# ════════════════════════════════════════════════════════════════════
class Fonts:
    """Lazy-loading font manager."""

    _cache = {}

    @classmethod
    def get(cls, size, bold=False):
        key = (size, bold)
        if key not in cls._cache:
            font_path = cls._find_font(bold)
            if font_path:
                try:
                    cls._cache[key] = pygame.font.Font(font_path, size)
                except Exception:
                    cls._cache[key] = pygame.font.Font(None, size)
            else:
                # Use pygame default font (guaranteed to work)
                try:
                    f = pygame.font.SysFont("dejavusans,liberationsans,freesans,arial", size, bold=bold)
                    if f is None:
                        f = pygame.font.Font(None, size)
                    cls._cache[key] = f
                except Exception:
                    cls._cache[key] = pygame.font.Font(None, size)
        return cls._cache[key]

    @classmethod
    def _find_font(cls, bold=False):
        """Try to find Space Grotesk or other font files in assets."""
        suffix = "Bold" if bold else "Regular"
        candidates = [
            os.path.join(config.FONT_DIR, f"SpaceGrotesk-{suffix}.ttf"),
            os.path.join(config.FONT_DIR, f"Inter-{suffix}.ttf"),
            os.path.join(config.FONT_DIR, f"Inter-{suffix}.otf"),
        ]
        for path in candidates:
            if os.path.exists(path):
                # Verify it's actually a font file (not corrupted)
                try:
                    with open(path, 'rb') as f:
                        header = f.read(4)
                    if header[:4] in (b'\x00\x01\x00\x00', b'OTTO', b'true', b'typ1'):
                        return path
                except Exception:
                    pass
        return None

    @classmethod
    def title(cls, bold=True):
        return cls.get(16, bold=bold)

    @classmethod
    def body(cls, bold=False):
        return cls.get(13, bold=bold)

    @classmethod
    def small(cls, bold=False):
        return cls.get(10, bold=bold)

    @classmethod
    def tiny(cls, bold=True):
        return cls.get(9, bold=bold)

    @classmethod
    def large(cls, bold=True):
        return cls.get(20, bold=bold)

    @classmethod
    def huge(cls, bold=True):
        return cls.get(28, bold=bold)


# ════════════════════════════════════════════════════════════════════
#  DRAWING HELPERS
# ════════════════════════════════════════════════════════════════════

def draw_gradient_bg(surface):
    """Fill the surface with a vertical dark gradient."""
    w, h = surface.get_size()
    for y in range(h):
        t = y / h
        r = int(Colors.BG_GRADIENT_TOP[0] * (1 - t) + Colors.BG_GRADIENT_BOTTOM[0] * t)
        g = int(Colors.BG_GRADIENT_TOP[1] * (1 - t) + Colors.BG_GRADIENT_BOTTOM[1] * t)
        b = int(Colors.BG_GRADIENT_TOP[2] * (1 - t) + Colors.BG_GRADIENT_BOTTOM[2] * t)
        pygame.draw.line(surface, (r, g, b), (0, y), (w, y))


_gradient_cache = None


def draw_gradient_bg_cached(surface):
    """Cached version of gradient background for performance."""
    global _gradient_cache
    size = surface.get_size()
    if _gradient_cache is None or _gradient_cache.get_size() != size:
        _gradient_cache = pygame.Surface(size)
        draw_gradient_bg(_gradient_cache)
    surface.blit(_gradient_cache, (0, 0))


def draw_rounded_rect(surface, color, rect, radius=8, alpha=255):
    """Draw a rounded rectangle, optionally with alpha."""
    if len(color) == 4:
        alpha = color[3]
        color = color[:3]

    if alpha < 255:
        temp = pygame.Surface((rect[2], rect[3]), pygame.SRCALPHA)
        pygame.draw.rect(temp, (*color, alpha), (0, 0, rect[2], rect[3]),
                         border_radius=radius)
        surface.blit(temp, (rect[0], rect[1]))
    else:
        pygame.draw.rect(surface, color, rect, border_radius=radius)


def draw_glass_panel(surface, rect, radius=12):
    """Draw a frosted glass panel with border."""
    draw_rounded_rect(surface, Colors.GLASS_BG, rect, radius)
    temp = pygame.Surface((rect[2], rect[3]), pygame.SRCALPHA)
    pygame.draw.rect(temp, Colors.GLASS_BORDER,
                     (0, 0, rect[2], rect[3]),
                     width=1, border_radius=radius)
    surface.blit(temp, (rect[0], rect[1]))


def draw_glow_circle(surface, center, radius, color=None, intensity=40):
    """Draw a soft glow circle effect."""
    if color is None:
        color = Colors.ACCENT
    for i in range(5, 0, -1):
        a = intensity // i
        r = radius + i * 3
        temp = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(temp, (*color[:3], a), (r, r), r)
        surface.blit(temp, (center[0] - r, center[1] - r))


def draw_progress_bar(surface, rect, progress, fill_color=None,
                       bg_color=None, glow=True):
    """Draw a progress bar with optional glow effect."""
    if fill_color is None:
        fill_color = Colors.PROGRESS_FILL
    if bg_color is None:
        bg_color = Colors.PROGRESS_BG
    x, y, w, h = rect

    # Background
    draw_rounded_rect(surface, bg_color, (x, y, w, h), radius=h // 2)

    # Filled portion
    fill_w = max(h, int(w * progress))
    if progress > 0:
        draw_rounded_rect(surface, fill_color, (x, y, fill_w, h), radius=h // 2)

        # Glow on the leading edge
        if glow and fill_w > h:
            glow_surf = pygame.Surface((12, h + 6), pygame.SRCALPHA)
            pygame.draw.ellipse(glow_surf, (*fill_color[:3], 50),
                                (0, 0, 12, h + 6))
            surface.blit(glow_surf, (x + fill_w - 8, y - 3))


def render_text(surface, text, pos, font=None, color=None,
                max_width=None, center=False):
    """Render text with optional truncation and centering."""
    if font is None:
        font = Fonts.body()
    if color is None:
        color = Colors.TEXT_PRIMARY

    if max_width:
        while font.size(text)[0] > max_width and len(text) > 3:
            text = text[:-4] + "..."

    rendered = font.render(text, True, color)

    if center:
        text_rect = rendered.get_rect(center=pos)
        surface.blit(rendered, text_rect)
    else:
        surface.blit(rendered, pos)

    return rendered.get_size()


# ════════════════════════════════════════════════════════════════════
#  ICON LOADING
# ════════════════════════════════════════════════════════════════════

_icon_cache = {}


def load_icon(name, size=(24, 24)):
    """Load and scale an icon from assets/icons/ (cached)."""
    key = (name, size)
    if key in _icon_cache:
        return _icon_cache[key]
    path = os.path.join(config.ICON_DIR, f"{name}.png")
    if os.path.exists(path):
        icon = pygame.image.load(path).convert_alpha()
        icon = pygame.transform.smoothscale(icon, size)
        _icon_cache[key] = icon
        return icon
    return None


_tint_cache = {}


def tint_icon(icon_surface, color):
    """Return a copy of icon_surface tinted to the given color, preserving alpha."""
    # Cache by surface id + color
    key = (id(icon_surface), color[:3])
    if key in _tint_cache:
        return _tint_cache[key]
    tinted = icon_surface.copy()
    w, h = tinted.get_size()
    for px in range(w):
        for py in range(h):
            r, g, b, a = tinted.get_at((px, py))
            if a > 0:
                tinted.set_at((px, py), (*color[:3], a))
    _tint_cache[key] = tinted
    return tinted
