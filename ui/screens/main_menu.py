"""
Main Menu Screen — Tack UI Home tab.
"""

import pygame
from ui.screen_manager import Screen
from ui.theme import Colors, Fonts, draw_gradient_bg_cached, render_text, draw_rounded_rect, load_icon, tint_icon
from ui.widgets import StatusBar, BottomNavBar, ScrollList
from hardware.input_handler import InputAction
import config


class MainMenuScreen(Screen):
    """Home screen with vertical menu + bottom nav."""

    MENU_ITEMS = [
        {"label": "All Songs",   "icon_name": "music",       "action": "music"},
        {"label": "Artists",     "icon_name": "artist",      "action": "artists"},
        {"label": "Albums",      "icon_name": "album",       "action": "albums"},
        {"label": "Now Playing", "icon_name": "now_playing", "action": "now_playing"},
        {"label": "Bluetooth",   "icon_name": "bluetooth",   "action": "bluetooth"},
        {"label": "WiFi",        "icon_name": "wifi",        "action": "wifi"},
        {"label": "Settings",    "icon_name": "settings",    "action": "settings"},
    ]

    def __init__(self, app):
        super().__init__(app)
        self.status_bar = StatusBar()
        self.bottom_nav = BottomNavBar()
        self.bottom_nav.active_tab = 0
        self._icons = {}
        self._load_icons()
        self.menu_list = ScrollList(
            self.MENU_ITEMS,
            header="Zero2 Music",
            item_renderer=self._render_menu_item,
            bottom_margin=BottomNavBar.HEIGHT,
        )

    def _load_icons(self):
        for item in self.MENU_ITEMS:
            name = item.get("icon_name", "")
            if name:
                icon = load_icon(name, size=(20, 20))
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
        self.bottom_nav.render(surface, x_offset)

    def _render_menu_item(self, surface, item, rect, selected, x_offset):
        x, y, w, h = rect
        icon_name = item.get("icon_name", "")
        label = item.get("label", "")

        # Icon background square
        icon_bg_size = 28
        icon_bg_x = x + 10
        icon_bg_y = y + (h - icon_bg_size) // 2
        bg_color = (*Colors.ACCENT[:3], 40) if selected else (*Colors.BG_CARD[:3], 180)
        draw_rounded_rect(surface, bg_color,
                          (icon_bg_x, icon_bg_y, icon_bg_size, icon_bg_size), radius=6)

        # Icon
        icon_surf = self._icons.get(icon_name)
        if icon_surf:
            color = Colors.ACCENT if selected else Colors.TEXT_MUTED
            tinted = tint_icon(icon_surf, color)
            surface.blit(tinted, (icon_bg_x + 4, icon_bg_y + 4))

        # Label
        label_color = Colors.TEXT_PRIMARY if selected else Colors.TEXT_SECONDARY
        render_text(surface, label, (x + 46, y + (h - 14) // 2),
                    font=Fonts.body(), color=label_color)

        # Chevron
        if selected:
            render_text(surface, "›", (x + w - 16, y + (h - 14) // 2),
                        font=Fonts.body(), color=Colors.ACCENT)
