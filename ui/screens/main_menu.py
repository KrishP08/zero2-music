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
        self.retro_selected_index = 0
        self.RETRO_ITEMS = ["music", "artists", "albums", "settings"]

    def _load_icons(self):
        for item in self.MENU_ITEMS:
            name = item.get("icon_name", "")
            if name:
                icon = load_icon(name, size=(20, 20))
                if icon:
                    self._icons[name] = icon

    def handle_input(self, action):
        is_retro = getattr(config, "THEME", "modern") == "retro"
        
        if is_retro:
            if action == InputAction.SCROLL_UP:
                self.retro_selected_index = max(0, self.retro_selected_index - 1)
            elif action == InputAction.SCROLL_DOWN:
                self.retro_selected_index = min(len(self.RETRO_ITEMS) - 1, self.retro_selected_index + 1)
            elif action == InputAction.SELECT:
                self._select_retro_item()
            elif action == InputAction.PLAY_PAUSE:
                self.app.audio.toggle_pause()
        else:
            if action == InputAction.SCROLL_UP:
                self.menu_list.scroll_up()
            elif action == InputAction.SCROLL_DOWN:
                self.menu_list.scroll_down()
            elif action == InputAction.SELECT:
                self._select_item()
            elif action == InputAction.PLAY_PAUSE:
                self.app.audio.toggle_pause()

    def _select_retro_item(self):
        action = self.RETRO_ITEMS[self.retro_selected_index]
        if action == "music":
            from ui.screens.library import LibraryScreen
            self.app.screen_manager.push(LibraryScreen(self.app, mode="songs"))
        elif action == "artists":
            from ui.screens.library import LibraryScreen
            self.app.screen_manager.push(LibraryScreen(self.app, mode="artists"))
        elif action == "albums":
            from ui.screens.library import LibraryScreen
            self.app.screen_manager.push(LibraryScreen(self.app, mode="albums"))
        elif action == "settings":
            from ui.screens.settings import SettingsScreen
            self.app.screen_manager.push(SettingsScreen(self.app))

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
        if getattr(config, "THEME", "modern") == "retro":
            self._render_retro(surface, x_offset)
        else:
            draw_gradient_bg_cached(surface)
            self.status_bar.render(surface, x_offset)
            self.menu_list.render(surface, x_offset)

    def _render_retro(self, surface, x_offset):
        surface.fill(Colors.RETRO_BG_DARK)
        
        self.status_bar.render(surface, x_offset, title="TAPE-A")
        
        # ── Header ──
        render_text(surface, "MEDIA LIBRARY", (x_offset + 24, 30), font=Fonts.body(bold=True), color=(240, 240, 240))
        
        # ── 2x2 Grid ──
        grid_y = 56
        gw, gh = 138, 55
        gap = 10
        start_x = x_offset + (config.SCREEN_WIDTH - (gw * 2 + gap)) // 2
        
        labels = ["SONGS", "ARTISTS", "ALBUMS", "SETTINGS"]
        
        for i in range(4):
            col = i % 2
            row = i // 2
            bx = start_x + col * (gw + gap)
            by = grid_y + row * (gh + gap)
            
            selected = (i == self.retro_selected_index)
            
            # Button BG
            bg_color = Colors.RETRO_PRIMARY if i < 2 else (60, 45, 20)
            text_color = Colors.RETRO_BG_DARK if i < 2 else Colors.RETRO_PRIMARY
            
            if selected:
                by += 2  # pressed effect
                draw_rounded_rect(surface, bg_color, (bx, by, gw, gh), radius=8)
            else:
                draw_rounded_rect(surface, bg_color, (bx, by, gw, gh), radius=8)
                # thick border/shadow
                pygame.draw.rect(surface, Colors.RETRO_ORANGE_DARK if i < 2 else (40, 30, 15), 
                                 (bx, by + gh - 4, gw, 4), border_bottom_left_radius=8, border_bottom_right_radius=8)
                
            # Outline for bottom row
            if i >= 2:
                pygame.draw.rect(surface, (*Colors.RETRO_PRIMARY[:3], 100), (bx, by, gw, gh), width=2, border_radius=8)

            label_surf = Fonts.tiny(bold=True).render(labels[i], True, text_color)
            surface.blit(label_surf, (bx + gw//2 - label_surf.get_width()//2, by + gh//2 - label_surf.get_height()//2 - 2))
            
        # ── Bottom Nav / Mini Player ──
        bar_y = config.SCREEN_HEIGHT - 40
        pygame.draw.rect(surface, (40, 30, 20), (x_offset, bar_y, config.SCREEN_WIDTH, 40))
        pygame.draw.rect(surface, (*Colors.RETRO_PRIMARY[:3], 50), (x_offset, bar_y, config.SCREEN_WIDTH, 1))
        
        trk = self.app.playlist.current_track
        track_name = trk.display_title if trk else "Not Playing"
            
        render_text(surface, "NOW PLAYING", (x_offset + 12, bar_y + 6), font=Fonts.tiny(bold=True), color=(150, 100, 30))
        render_text(surface, track_name[:20], (x_offset + 12, bar_y + 20), font=Fonts.body(), color=(240, 240, 240))
        
        is_playing = self.app.audio.is_playing
        state_str = "|| PAUSE" if trk and not is_playing else ">> PLAY"
        if not trk: state_str = "--"
        render_text(surface, state_str, (x_offset + config.SCREEN_WIDTH - 60, bar_y + 14), font=Fonts.tiny(bold=True), color=Colors.RETRO_PRIMARY)
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
