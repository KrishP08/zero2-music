"""
Widgets — Tack UI components for the landscape 320×240 interface.
StatusBar, BottomNavBar, ScrollList, VolumeOverlay, PlaybackControls.
"""

import pygame
import time
import math
import config
from ui.theme import (
    Colors, Fonts, draw_rounded_rect, draw_glass_panel,
    draw_progress_bar, render_text, draw_gradient_bg_cached,
    load_icon, tint_icon,
)


# ════════════════════════════════════════════════════════════════════
#  STATUS BAR  — compact top bar (time, BT, WiFi, battery)
# ════════════════════════════════════════════════════════════════════
class StatusBar:
    """Compact top status bar — 24px tall."""

    HEIGHT = 24

    def __init__(self):
        self._bt_icon = load_icon("bluetooth", size=(12, 12))
        self._wifi_icon = load_icon("wifi", size=(12, 12))
        self._battery_icon = load_icon("battery", size=(14, 14))

    def render(self, surface, x_offset=0, title=None, show_back=False):
        # Bar background
        bar_rect = (x_offset, 0, config.SCREEN_WIDTH, self.HEIGHT)
        draw_rounded_rect(surface, (10, 14, 22, 220), bar_rect, radius=0)

        # Left side: title or time
        if title:
            render_text(surface, title,
                        (x_offset + (28 if show_back else 8), 4),
                        font=Fonts.tiny(), color=Colors.TEXT_MUTED)
        else:
            now = time.strftime("%H:%M")
            render_text(surface, now,
                        (x_offset + 8, 4),
                        font=Fonts.tiny(), color=Colors.TEXT_MUTED)

        # Right side icons
        ix = x_offset + config.SCREEN_WIDTH - 8

        # Battery
        if self._battery_icon:
            ix -= 14
            tinted = tint_icon(self._battery_icon, Colors.BATTERY_GREEN)
            surface.blit(tinted, (ix, 5))

        # WiFi
        if self._wifi_icon:
            ix -= 16
            tinted = tint_icon(self._wifi_icon, Colors.TEXT_MUTED)
            surface.blit(tinted, (ix, 6))

        # Bluetooth
        if self._bt_icon:
            ix -= 16
            tinted = tint_icon(self._bt_icon, Colors.TEXT_MUTED)
            surface.blit(tinted, (ix, 6))


# ════════════════════════════════════════════════════════════════════
#  BOTTOM NAV BAR  — 4 tabs
# ════════════════════════════════════════════════════════════════════
class BottomNavBar:
    """Persistent bottom navigation — Home, Files, Music, Settings."""

    HEIGHT = 36

    TABS = [
        {"label": "Home", "icon": "music"},
        {"label": "Files", "icon": "album"},
        {"label": "Playing", "icon": "now_playing"},
        {"label": "Settings", "icon": "settings"},
    ]

    def __init__(self):
        self.active_tab = 0
        self._icons = {}
        for tab in self.TABS:
            icon = load_icon(tab["icon"], size=(18, 18))
            if icon:
                self._icons[tab["icon"]] = icon

    def render(self, surface, x_offset=0):
        y = config.SCREEN_HEIGHT - self.HEIGHT
        w = config.SCREEN_WIDTH

        # Background
        bg_rect = (x_offset, y, w, self.HEIGHT)
        draw_rounded_rect(surface, (10, 15, 22, 230), bg_rect, radius=0)

        # Top border
        pygame.draw.line(surface, Colors.DIVIDER,
                         (x_offset, y), (x_offset + w, y))

        # Tabs
        tab_w = w // len(self.TABS)
        for i, tab in enumerate(self.TABS):
            tx = x_offset + i * tab_w + tab_w // 2
            ty = y + 8
            is_active = (i == self.active_tab)

            # Icon
            icon_surf = self._icons.get(tab["icon"])
            if icon_surf:
                color = Colors.ACCENT if is_active else Colors.TEXT_MUTED
                tinted = tint_icon(icon_surf, color)
                surface.blit(tinted, (tx - 9, ty))
            
            # Active dot
            if is_active:
                pygame.draw.circle(surface, Colors.ACCENT,
                                   (tx, ty + 24), 2)


# ════════════════════════════════════════════════════════════════════
#  SCROLL LIST  — smooth scrolling vertical list
# ════════════════════════════════════════════════════════════════════
class ScrollList:
    """Smooth-scrolling vertical list with Tack-style highlight."""

    ITEM_HEIGHT = 40
    PADDING_X = 12

    def __init__(self, items, header="", item_renderer=None,
                 top_offset=None, bottom_margin=0):
        self.items = items
        self.header = header
        self.selected_index = 0
        self._scroll_offset = 0.0
        self._target_scroll = 0.0
        self._item_renderer = item_renderer
        self._top_offset = top_offset or (StatusBar.HEIGHT + 28)
        self._bottom_margin = bottom_margin

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
        visible_h = config.SCREEN_HEIGHT - self._top_offset - self._bottom_margin - 10
        item_top = self.selected_index * self.ITEM_HEIGHT
        item_bottom = item_top + self.ITEM_HEIGHT

        if item_top < self._target_scroll:
            self._target_scroll = item_top
        elif item_bottom > self._target_scroll + visible_h:
            self._target_scroll = item_bottom - visible_h

    def update(self, dt):
        diff = self._target_scroll - self._scroll_offset
        self._scroll_offset += diff * min(1.0, dt * 12.0)

    def render(self, surface, x_offset=0):
        top = self._top_offset

        # Header
        if self.header:
            render_text(
                surface, self.header,
                (x_offset + self.PADDING_X, StatusBar.HEIGHT + 4),
                font=Fonts.title(),
                color=Colors.TEXT_PRIMARY
            )

        # Clip area
        clip_bottom = config.SCREEN_HEIGHT - self._bottom_margin
        clip_rect = pygame.Rect(x_offset, top, config.SCREEN_WIDTH, clip_bottom - top)
        surface.set_clip(clip_rect)

        for i, item in enumerate(self.items):
            y = top + i * self.ITEM_HEIGHT - int(self._scroll_offset)

            if y + self.ITEM_HEIGHT < top or y > clip_bottom:
                continue

            item_rect = (
                x_offset + 6, y + 2,
                config.SCREEN_WIDTH - 12, self.ITEM_HEIGHT - 4
            )
            selected = (i == self.selected_index)

            if selected:
                draw_rounded_rect(surface, (*Colors.ACCENT[:3], 20),
                                  item_rect, radius=8)
                # Left accent bar
                pygame.draw.rect(
                    surface, Colors.ACCENT,
                    (x_offset + 6, y + 8, 3, self.ITEM_HEIGHT - 16),
                    border_radius=2
                )

            if self._item_renderer:
                self._item_renderer(surface, item, item_rect, selected, x_offset)
            else:
                self._default_render(surface, item, item_rect, selected, x_offset)

        surface.set_clip(None)
        self._render_scrollbar(surface, top, x_offset, clip_bottom)

    def _default_render(self, surface, item, rect, selected, x_offset):
        x, y, w, h = rect
        label_color = Colors.TEXT_PRIMARY if selected else Colors.TEXT_SECONDARY
        render_text(
            surface, item.get("label", ""),
            (x + self.PADDING_X + 6, y + 5),
            font=Fonts.body(), color=label_color,
            max_width=config.SCREEN_WIDTH - 50
        )
        if "subtitle" in item:
            render_text(
                surface, item["subtitle"],
                (x + self.PADDING_X + 6, y + 21),
                font=Fonts.small(), color=Colors.TEXT_MUTED,
                max_width=config.SCREEN_WIDTH - 50
            )

    def _render_scrollbar(self, surface, top, x_offset, bottom):
        if len(self.items) <= 0:
            return
        total_h = len(self.items) * self.ITEM_HEIGHT
        visible_h = bottom - top
        if total_h <= visible_h:
            return
        bar_h = max(16, int(visible_h * visible_h / total_h))
        bar_y = top + int(self._scroll_offset / total_h * visible_h)
        bar_y = min(bar_y, bottom - bar_h)
        draw_rounded_rect(
            surface, (*Colors.ACCENT[:3], 50),
            (x_offset + config.SCREEN_WIDTH - 4, bar_y, 3, bar_h),
            radius=2
        )


# ════════════════════════════════════════════════════════════════════
#  VOLUME OVERLAY
# ════════════════════════════════════════════════════════════════════
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

        w, h = 160, 40
        x = (config.SCREEN_WIDTH - w) // 2
        y = config.SCREEN_HEIGHT - 80

        draw_glass_panel(surface, (x, y, w, h), radius=12)

        # Volume bar
        bar_x = x + 12
        bar_y = y + 16
        bar_w = w - 50
        bar_h = 6
        draw_progress_bar(surface, (bar_x, bar_y, bar_w, bar_h),
                          self._volume, glow=True)

        # Percentage
        pct = f"{int(self._volume * 100)}%"
        render_text(surface, pct,
                    (x + w - 34, y + 12),
                    font=Fonts.small(), color=Colors.TEXT_SECONDARY)


# ════════════════════════════════════════════════════════════════════
#  PLAYBACK CONTROLS  — landscape horizontal controls
# ════════════════════════════════════════════════════════════════════
class PlaybackControls:
    """Horizontal playback control row: shuffle, prev, play/pause, next, playlist."""

    def __init__(self):
        self._icons = {
            "play": load_icon("play", size=(16, 16)),
            "pause": load_icon("pause", size=(16, 16)),
            "prev": load_icon("prev", size=(16, 16)),
            "next": load_icon("next", size=(16, 16)),
            "shuffle": load_icon("shuffle", size=(14, 14)),
            "repeat": load_icon("repeat", size=(14, 14)),
        }
        self.selected = 1  # Default focus on play/pause

    def render(self, surface, rect, is_playing=False, shuffle_on=False, repeat_on=False, x_offset=0):
        """Render controls within a given rect area."""
        x, y, w, h = rect
        center_y = y + h // 2
        center_x = x + w // 2 + x_offset

        spacing = 38
        outer_spacing = 76
        main_r = 18

        # Highlight selected
        if 0 <= self.selected <= 4:
            positions = [
                center_x - outer_spacing,
                center_x - spacing,
                center_x,
                center_x + spacing,
                center_x + outer_spacing
            ]
            hx = positions[self.selected]
            hr = main_r + 2 if self.selected == 2 else 14
            pygame.draw.circle(surface, (255, 255, 255, 60), (hx, center_y), hr, width=2)
            
        # Main play button with accent fill
        pygame.draw.circle(surface, Colors.ACCENT, (center_x, center_y), main_r)
        glow_surf = pygame.Surface((main_r * 3, main_r * 3), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*Colors.ACCENT[:3], 40),
                           (main_r * 3 // 2, main_r * 3 // 2), main_r * 3 // 2)
        surface.blit(glow_surf, (center_x - main_r * 3 // 2, center_y - main_r * 3 // 2))

        # Main Play/Pause
        icon_name = "pause" if is_playing else "play"
        if self._icons[icon_name]:
            tinted = tint_icon(self._icons[icon_name], Colors.BG_DARK)
            r = tinted.get_rect(center=(center_x + (2 if icon_name=="play" else 0), center_y))
            surface.blit(tinted, r)

        # Prev
        if self._icons["prev"]:
            tinted = tint_icon(self._icons["prev"], Colors.TEXT_PRIMARY)
            r = tinted.get_rect(center=(center_x - spacing, center_y))
            surface.blit(tinted, r)

        # Next
        if self._icons["next"]:
            tinted = tint_icon(self._icons["next"], Colors.TEXT_PRIMARY)
            r = tinted.get_rect(center=(center_x + spacing, center_y))
            surface.blit(tinted, r)

        # Shuffle
        if self._icons["shuffle"]:
            color = Colors.ACCENT if shuffle_on else Colors.TEXT_MUTED
            tinted = tint_icon(self._icons["shuffle"], color)
            r = tinted.get_rect(center=(center_x - outer_spacing, center_y))
            surface.blit(tinted, r)

        # Repeat
        if self._icons["repeat"]:
            color = Colors.ACCENT if repeat_on else Colors.TEXT_MUTED
            tinted = tint_icon(self._icons["repeat"], color)
            r = tinted.get_rect(center=(center_x + outer_spacing, center_y))
            surface.blit(tinted, r)
