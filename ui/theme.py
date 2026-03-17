"""
Theme — Innioasis Y1–inspired glassmorphic dark theme.
Defines colors, fonts, and rendering helpers for the player UI.
"""

import pygame
import os
import config


# ════════════════════════════════════════════════════════════════════
#  COLOR PALETTE  — deep dark with cyan / teal accents
# ════════════════════════════════════════════════════════════════════
class Colors:
    # Backgrounds
    BG_DARK = (8, 10, 18)
    BG_GRADIENT_TOP = (12, 16, 32)
    BG_GRADIENT_BOTTOM = (4, 6, 12)
    BG_CARD = (18, 22, 40)
    BG_CARD_HIGHLIGHT = (28, 34, 58)

    # Accent
    ACCENT = (0, 212, 255)        # Cyan / teal
    ACCENT_DIM = (0, 140, 180)
    ACCENT_GLOW = (0, 212, 255, 60)
    ACCENT_DARK = (0, 80, 110)

    # Text
    TEXT_PRIMARY = (240, 242, 250)
    TEXT_SECONDARY = (140, 150, 175)
    TEXT_MUTED = (80, 90, 110)

    # UI Elements
    HIGHLIGHT_BG = (0, 212, 255, 30)
    DIVIDER = (30, 36, 55)
    PROGRESS_BG = (30, 36, 55)
    PROGRESS_FILL = (0, 212, 255)

    # Glass
    GLASS_BG = (20, 24, 44, 180)
    GLASS_BORDER = (60, 70, 100, 100)

    # Status
    BATTERY_GREEN = (80, 220, 120)
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    TRANSPARENT = (0, 0, 0, 0)


# ════════════════════════════════════════════════════════════════════
#  FONT MANAGER
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
                cls._cache[key] = pygame.font.Font(font_path, size)
            else:
                cls._cache[key] = pygame.font.SysFont(
                    "Inter, Helvetica, Arial, sans-serif", size, bold=bold
                )
        return cls._cache[key]

    @classmethod
    def _find_font(cls, bold=False):
        """Try to find Inter font files in assets."""
        suffix = "Bold" if bold else "Regular"
        candidates = [
            os.path.join(config.FONT_DIR, f"Inter-{suffix}.ttf"),
            os.path.join(config.FONT_DIR, f"Inter-{suffix}.otf"),
            os.path.join(config.FONT_DIR, f"inter-{suffix.lower()}.ttf"),
        ]
        for path in candidates:
            if os.path.exists(path):
                return path
        return None

    @classmethod
    def title(cls):
        return cls.get(18, bold=True)

    @classmethod
    def body(cls):
        return cls.get(14)

    @classmethod
    def small(cls):
        return cls.get(11)

    @classmethod
    def large(cls):
        return cls.get(24, bold=True)

    @classmethod
    def huge(cls):
        return cls.get(32, bold=True)


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
    # Semi-transparent background
    draw_rounded_rect(surface, Colors.GLASS_BG, rect, radius)
    # Subtle border
    border_rect = (rect[0], rect[1], rect[2], rect[3])
    temp = pygame.Surface((rect[2], rect[3]), pygame.SRCALPHA)
    pygame.draw.rect(temp, Colors.GLASS_BORDER,
                     (0, 0, rect[2], rect[3]),
                     width=1, border_radius=radius)
    surface.blit(temp, (rect[0], rect[1]))


def draw_glow_circle(surface, center, radius, color=Colors.ACCENT, intensity=40):
    """Draw a soft glow circle effect."""
    for i in range(5, 0, -1):
        alpha = intensity // i
        r = radius + i * 3
        temp = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(temp, (*color[:3], alpha), (r, r), r)
        surface.blit(temp, (center[0] - r, center[1] - r))


def draw_progress_bar(surface, rect, progress, fill_color=Colors.PROGRESS_FILL,
                       bg_color=Colors.PROGRESS_BG, glow=True):
    """Draw a progress bar with optional glow effect."""
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


def render_text(surface, text, pos, font=None, color=Colors.TEXT_PRIMARY,
                max_width=None, center=False):
    """Render text with optional truncation and centering."""
    if font is None:
        font = Fonts.body()

    if max_width:
        # Truncate text to fit
        while font.size(text)[0] > max_width and len(text) > 3:
            text = text[:-4] + "..."

    rendered = font.render(text, True, color)

    if center:
        text_rect = rendered.get_rect(center=pos)
        surface.blit(rendered, text_rect)
    else:
        surface.blit(rendered, pos)

    return rendered.get_size()


def load_icon(name, size=(24, 24)):
    """Load and scale an icon from assets/icons/."""
    path = os.path.join(config.ICON_DIR, f"{name}.png")
    if os.path.exists(path):
        icon = pygame.image.load(path).convert_alpha()
        return pygame.transform.smoothscale(icon, size)
    return None
