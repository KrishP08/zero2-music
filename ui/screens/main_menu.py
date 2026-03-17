"""
Main Menu Screen — Y1-style vertical menu with icons.
"""

import pygame
from ui.screen_manager import Screen
from ui.theme import Colors, Fonts, draw_gradient_bg_cached, render_text, draw_rounded_rect, load_icon
from ui.widgets import StatusBar, ScrollList
from hardware.input_handler import InputAction
import config


class MainMenuScreen(Screen):
    """Root menu screen with iPod/Y1-style navigation."""

    MENU_ITEMS = [
        {"label": "Music",       "icon_name": "music",       "action": "music"},
        {"label": "Now Playing", "icon_name": "now_playing",  "action": "now_playing"},
        {"label": "Artists",     "icon_name": "artist",      "action": "artists"},
        {"label": "Albums",      "icon_name": "album",       "action": "albums"},
        {"label": "Bluetooth",   "icon_name": "bluetooth",   "action": "bluetooth"},
        {"label": "WiFi",        "icon_name": "wifi",        "action": "wifi"},
        {"label": "Settings",    "icon_name": "settings",    "action": "settings"},
    ]

    def __init__(self, app):
        super().__init__(app)
        self.status_bar = StatusBar()
        self._icons = {}
        self._load_icons()
        self.menu_list = ScrollList(
            self.MENU_ITEMS,
            header="Zero2 Music",
            item_renderer=self._render_menu_item
        )

    def _load_icons(self):
        """Pre-load all menu icons."""
        for item in self.MENU_ITEMS:
            name = item.get("icon_name", "")
            if name:
                icon = load_icon(name, size=(22, 22))
                if icon:
                    self._icons[name] = icon

    def handle_input(self, action):
        if action == InputAction.SCROLL_UP:
            self.menu_list.scroll_up()
        elif action == InputAction.SCROLL_DOWN:
            self.menu_list.scroll_down()
        elif action == InputAction.SELECT:
            self._select_item()
        elif action == InputAction.PLAY_PAUSE:
            self.app.audio.toggle_pause()

    def _select_item(self):
        item = self.menu_list.selected_item
        if not item:
            return

        action = item["action"]
        if action == "music":
            from ui.screens.library import LibraryScreen
            screen = LibraryScreen(self.app, mode="songs")
            self.app.screen_manager.push(screen)
        elif action == "now_playing":
            if self.app.audio.current_file:
                from ui.screens.now_playing import NowPlayingScreen
                screen = NowPlayingScreen(self.app)
                self.app.screen_manager.push(screen)
        elif action == "artists":
            from ui.screens.library import LibraryScreen
            screen = LibraryScreen(self.app, mode="artists")
            self.app.screen_manager.push(screen)
        elif action == "albums":
            from ui.screens.library import LibraryScreen
            screen = LibraryScreen(self.app, mode="albums")
            self.app.screen_manager.push(screen)
        elif action == "bluetooth":
            from ui.screens.bluetooth import BluetoothScreen
            screen = BluetoothScreen(self.app)
            self.app.screen_manager.push(screen)
        elif action == "wifi":
            from ui.screens.wifi import WiFiScreen
            screen = WiFiScreen(self.app)
            self.app.screen_manager.push(screen)
        elif action == "settings":
            from ui.screens.settings import SettingsScreen
            screen = SettingsScreen(self.app)
            self.app.screen_manager.push(screen)

    def update(self, dt):
        self.menu_list.update(dt)

    def render(self, surface, x_offset=0):
        draw_gradient_bg_cached(surface)
        self.status_bar.render(surface, x_offset)
        self.menu_list.render(surface, x_offset)

    def _render_menu_item(self, surface, item, rect, selected, x_offset):
        """Custom renderer with PNG icons."""
        x, y, w, h = rect
        icon_name = item.get("icon_name", "")
        label = item.get("label", "")

        # Icon (PNG)
        icon_surf = self._icons.get(icon_name)
        if icon_surf:
            # Tint icon: cyan when selected, muted otherwise
            tinted = icon_surf.copy()
            if selected:
                tint_color = Colors.ACCENT
            else:
                tint_color = Colors.TEXT_MUTED
            tint_overlay = pygame.Surface(tinted.get_size(), pygame.SRCALPHA)
            tint_overlay.fill((*tint_color[:3], 0))
            # Use the icon alpha channel with desired color
            for px in range(tinted.get_width()):
                for py in range(tinted.get_height()):
                    r, g, b, a = tinted.get_at((px, py))
                    if a > 0:
                        tinted.set_at((px, py), (*tint_color[:3], a))
            icon_y = y + (h - 22) // 2
            surface.blit(tinted, (x + 12, icon_y))
        else:
            # Fallback: no icon
            pass

        # Label
        label_color = Colors.TEXT_PRIMARY if selected else Colors.TEXT_SECONDARY
        render_text(surface, label, (x + 42, y + (h - 16) // 2),
                    font=Fonts.body(), color=label_color)

        # Right arrow for selected
        if selected:
            render_text(surface, "›", (x + w - 20, y + (h - 18) // 2),
                        font=Fonts.title(), color=Colors.ACCENT)
