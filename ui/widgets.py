"""
Widgets — reusable UI components for the Y1-inspired interface.
ScrollList, ProgressBar, StatusBar, GlassPanel, etc.
"""

import pygame
import time
import math
import config
from ui.theme import (
    Colors, Fonts, draw_rounded_rect, draw_glass_panel,
    draw_progress_bar, render_text, draw_gradient_bg_cached,
)


class StatusBar:
    """Top status bar showing time and status icons."""

    HEIGHT = 28

    def render(self, surface, x_offset=0):
        # Semi-transparent bar
        bar_rect = (x_offset, 0, config.SCREEN_WIDTH, self.HEIGHT)
        draw_rounded_rect(surface, (10, 14, 28, 200), bar_rect, radius=0)

        # Time
        now = time.strftime("%H:%M")
        render_text(
            surface, now,
            (x_offset + config.SCREEN_WIDTH // 2, self.HEIGHT // 2),
            font=Fonts.small(),
            color=Colors.TEXT_PRIMARY,
            center=True
        )

        # "♪" indicator on left
        render_text(
            surface, "♪",
            (x_offset + 10, 6),
            font=Fonts.small(),
            color=Colors.ACCENT
        )

        # Subtle bottom divider
        pygame.draw.line(
            surface, Colors.DIVIDER,
            (x_offset, self.HEIGHT - 1),
            (x_offset + config.SCREEN_WIDTH, self.HEIGHT - 1)
        )


class ScrollList:
    """
    A smooth-scrolling vertical list with Y1-style highlight.
    Used for menus, song lists, etc.
    """

    ITEM_HEIGHT = 44
    PADDING_X = 16
    VISIBLE_AREA_TOP = StatusBar.HEIGHT + 36  # after status bar + header

    def __init__(self, items, header="", item_renderer=None):
        """
        Args:
            items: list of dicts with at least 'label' key
            header: section header text
            item_renderer: optional custom render function(surface, item, rect, selected)
        """
        self.items = items
        self.header = header
        self.selected_index = 0
        self._scroll_offset = 0.0          # smooth scroll pixel offset
        self._target_scroll = 0.0
        self._item_renderer = item_renderer

    @property
    def selected_item(self):
        if 0 <= self.selected_index < len(self.items):
            return self.items[self.selected_index]
        return None

    def scroll_up(self):
        if self.selected_index > 0:
            self.selected_index -= 1
            self._ensure_visible()

    def scroll_down(self):
        if self.selected_index < len(self.items) - 1:
            self.selected_index += 1
            self._ensure_visible()

    def _ensure_visible(self):
        """Adjust scroll target so selected item is visible."""
        visible_h = config.SCREEN_HEIGHT - self.VISIBLE_AREA_TOP - 10
        item_top = self.selected_index * self.ITEM_HEIGHT
        item_bottom = item_top + self.ITEM_HEIGHT

        if item_top < self._target_scroll:
            self._target_scroll = item_top
        elif item_bottom > self._target_scroll + visible_h:
            self._target_scroll = item_bottom - visible_h

    def update(self, dt):
        """Smooth scroll animation."""
        diff = self._target_scroll - self._scroll_offset
        self._scroll_offset += diff * min(1.0, dt * 12.0)

    def render(self, surface, x_offset=0):
        top = self.VISIBLE_AREA_TOP

        # Header
        if self.header:
            render_text(
                surface, self.header,
                (x_offset + self.PADDING_X, StatusBar.HEIGHT + 6),
                font=Fonts.title(),
                color=Colors.TEXT_PRIMARY
            )

        # Clip area for list
        clip_rect = pygame.Rect(
            x_offset, top,
            config.SCREEN_WIDTH, config.SCREEN_HEIGHT - top
        )
        surface.set_clip(clip_rect)

        for i, item in enumerate(self.items):
            y = top + i * self.ITEM_HEIGHT - int(self._scroll_offset)

            # Skip items outside visible area
            if y + self.ITEM_HEIGHT < top or y > config.SCREEN_HEIGHT:
                continue

            item_rect = (
                x_offset + 8, y + 2,
                config.SCREEN_WIDTH - 16, self.ITEM_HEIGHT - 4
            )
            selected = (i == self.selected_index)

            if selected:
                # Highlighted background — cyan glass
                draw_rounded_rect(surface, (*Colors.ACCENT[:3], 25),
                                  item_rect, radius=10)
                # Left accent bar
                pygame.draw.rect(
                    surface, Colors.ACCENT,
                    (x_offset + 8, y + 8, 3, self.ITEM_HEIGHT - 16),
                    border_radius=2
                )

            if self._item_renderer:
                self._item_renderer(surface, item, item_rect, selected, x_offset)
            else:
                # Default renderer — label + optional subtitle
                label_color = Colors.TEXT_PRIMARY if selected else Colors.TEXT_SECONDARY
                render_text(
                    surface, item.get("label", ""),
                    (x_offset + self.PADDING_X + 10, y + 8),
                    font=Fonts.body(),
                    color=label_color,
                    max_width=config.SCREEN_WIDTH - 50
                )
                if "subtitle" in item:
                    render_text(
                        surface, item["subtitle"],
                        (x_offset + self.PADDING_X + 10, y + 25),
                        font=Fonts.small(),
                        color=Colors.TEXT_MUTED,
                        max_width=config.SCREEN_WIDTH - 50
                    )

        surface.set_clip(None)

        # Scroll indicator
        self._render_scrollbar(surface, top, x_offset)

    def _render_scrollbar(self, surface, top, x_offset):
        """Draw a thin scrollbar indicator."""
        if len(self.items) <= 0:
            return

        total_h = len(self.items) * self.ITEM_HEIGHT
        visible_h = config.SCREEN_HEIGHT - top
        if total_h <= visible_h:
            return

        bar_h = max(20, int(visible_h * visible_h / total_h))
        bar_y = top + int(self._scroll_offset / total_h * visible_h)
        bar_y = min(bar_y, config.SCREEN_HEIGHT - bar_h)

        draw_rounded_rect(
            surface, (*Colors.ACCENT[:3], 60),
            (x_offset + config.SCREEN_WIDTH - 4, bar_y, 3, bar_h),
            radius=2
        )


class VolumeOverlay:
    """Semi-transparent volume popup that auto-dismisses."""

    DISPLAY_TIME = 1.8

    def __init__(self):
        self._visible = False
        self._show_time = 0
        self._volume = 0.0

    def show(self, volume):
        self._visible = True
        self._volume = volume
        self._show_time = time.time()

    def update(self, dt):
        if self._visible:
            if time.time() - self._show_time > self.DISPLAY_TIME:
                self._visible = False

    @property
    def is_visible(self):
        return self._visible

    def render(self, surface):
        if not self._visible:
            return

        # Center overlay
        w, h = 180, 50
        x = (config.SCREEN_WIDTH - w) // 2
        y = config.SCREEN_HEIGHT - 80

        draw_glass_panel(surface, (x, y, w, h), radius=14)

        # Volume icon
        icon_text = "🔊" if self._volume > 0.5 else ("🔉" if self._volume > 0 else "🔇")
        render_text(surface, icon_text, (x + 12, y + 14),
                    font=Fonts.body(), color=Colors.TEXT_PRIMARY)

        # Volume bar
        bar_x = x + 42
        bar_y = y + 20
        bar_w = w - 56
        bar_h = 6
        draw_progress_bar(surface, (bar_x, bar_y, bar_w, bar_h),
                          self._volume, glow=True)

        # Percentage
        pct = f"{int(self._volume * 100)}%"
        render_text(surface, pct,
                    (x + w - 8, y + 15),
                    font=Fonts.small(), color=Colors.TEXT_SECONDARY)


class PlaybackControls:
    """
    Playback control icons: prev / play-pause / next.
    Renders as circular icon buttons.
    """

    def __init__(self):
        self.selected = 1  # 0=prev, 1=play/pause, 2=next

    def render(self, surface, y, is_playing=False, x_offset=0):
        center_x = x_offset + config.SCREEN_WIDTH // 2
        spacing = 54
        button_r = 18
        main_r = 24

        buttons = [
            ("⏮", center_x - spacing, button_r),
            ("⏸" if is_playing else "▶", center_x, main_r),
            ("⏭", center_x + spacing, button_r),
        ]

        for i, (icon, bx, br) in enumerate(buttons):
            selected = (i == self.selected)

            if selected:
                # Glow behind selected button
                glow_surf = pygame.Surface((br * 4, br * 4), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (*Colors.ACCENT[:3], 30),
                                   (br * 2, br * 2), br * 2)
                surface.blit(glow_surf, (bx - br * 2, y - br * 2))

            # Button circle
            color = Colors.ACCENT if selected else Colors.BG_CARD_HIGHLIGHT
            pygame.draw.circle(surface, color, (bx, y), br)

            # Border
            if not selected:
                pygame.draw.circle(surface, Colors.DIVIDER, (bx, y), br, width=1)

            # Icon text
            icon_color = Colors.BG_DARK if selected else Colors.TEXT_SECONDARY
            render_text(surface, icon, (bx, y),
                        font=Fonts.body() if i != 1 else Fonts.title(),
                        color=icon_color, center=True)
