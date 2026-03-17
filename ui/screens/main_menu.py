"""
Main Menu Screen — Y1-style vertical menu with icons.
"""

from ui.screen_manager import Screen
from ui.theme import Colors, Fonts, draw_gradient_bg_cached, render_text, draw_rounded_rect
from ui.widgets import StatusBar, ScrollList
from hardware.input_handler import InputAction
import config


class MainMenuScreen(Screen):
    """Root menu screen with iPod/Y1-style navigation."""

    MENU_ITEMS = [
        {"label": "Music", "icon": "🎵", "action": "music"},
        {"label": "Now Playing", "icon": "▶", "action": "now_playing"},
        {"label": "Artists", "icon": "🎤", "action": "artists"},
        {"label": "Albums", "icon": "💿", "action": "albums"},
        {"label": "Settings", "icon": "⚙", "action": "settings"},
    ]

    def __init__(self, app):
        super().__init__(app)
        self.status_bar = StatusBar()
        self.menu_list = ScrollList(
            self.MENU_ITEMS,
            header="Zero2 Music",
            item_renderer=self._render_menu_item
        )

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
        """Custom renderer with emoji icons."""
        x, y, w, h = rect
        icon = item.get("icon", "")
        label = item.get("label", "")

        # Icon
        icon_color = Colors.ACCENT if selected else Colors.TEXT_MUTED
        render_text(surface, icon, (x + 14, y + (h - 20) // 2),
                    font=Fonts.title(), color=icon_color)

        # Label
        label_color = Colors.TEXT_PRIMARY if selected else Colors.TEXT_SECONDARY
        render_text(surface, label, (x + 44, y + (h - 16) // 2),
                    font=Fonts.body(), color=label_color)

        # Right arrow for selected
        if selected:
            render_text(surface, "›", (x + w - 20, y + (h - 18) // 2),
                        font=Fonts.title(), color=Colors.ACCENT)
