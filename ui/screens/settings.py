"""
Settings Screen — shuffle, repeat, and player settings.
"""

from ui.screen_manager import Screen
from ui.theme import Colors, Fonts, draw_gradient_bg_cached, render_text, draw_rounded_rect
from ui.widgets import StatusBar, ScrollList
from hardware.input_handler import InputAction
from core.playlist import RepeatMode
import config


class SettingsScreen(Screen):
    """Settings menu with toggle controls."""

    def __init__(self, app):
        super().__init__(app)
        self.status_bar = StatusBar()
        self.scroll_list = None

    def on_enter(self):
        self._build_menu()

    def _build_menu(self):
        """Build settings items with current values."""
        shuffle_state = "On" if self.app.playlist.shuffle else "Off"
        repeat_state = self.app.playlist.repeat_label

        items = [
            {"label": "Shuffle", "value": shuffle_state, "action": "shuffle"},
            {"label": "Repeat", "value": repeat_state, "action": "repeat"},
            {"label": "Rescan Library", "value": f"{len(self.app.library.tracks)} tracks", "action": "rescan"},
            {"label": "About", "value": "Zero2 Music v1.0", "action": "about"},
        ]

        self.scroll_list = ScrollList(
            items, header="Settings",
            item_renderer=self._render_setting_item
        )

    def handle_input(self, action):
        if action == InputAction.SCROLL_UP:
            self.scroll_list.scroll_up()
        elif action == InputAction.SCROLL_DOWN:
            self.scroll_list.scroll_down()
        elif action == InputAction.SELECT:
            self._toggle_setting()
        elif action == InputAction.BACK:
            self.app.screen_manager.pop()

    def _toggle_setting(self):
        item = self.scroll_list.selected_item
        if not item:
            return

        action = item.get("action")
        if action == "shuffle":
            self.app.playlist.toggle_shuffle()
            self._build_menu()  # Refresh display
        elif action == "repeat":
            self.app.playlist.cycle_repeat()
            self._build_menu()
        elif action == "rescan":
            self.app.library.scan()
            self.app.library.save_cache()
            self._build_menu()

    def update(self, dt):
        if self.scroll_list:
            self.scroll_list.update(dt)

    def render(self, surface, x_offset=0):
        draw_gradient_bg_cached(surface)
        self.status_bar.render(surface, x_offset)
        if self.scroll_list:
            self.scroll_list.render(surface, x_offset)

    def _render_setting_item(self, surface, item, rect, selected, x_offset):
        """Custom renderer showing label + current value."""
        x, y, w, h = rect
        label = item.get("label", "")
        value = item.get("value", "")

        # Label
        label_color = Colors.TEXT_PRIMARY if selected else Colors.TEXT_SECONDARY
        render_text(surface, label, (x + 14, y + (h - 16) // 2),
                    font=Fonts.body(), color=label_color)

        # Value on right side
        val_color = Colors.ACCENT if selected else Colors.TEXT_MUTED
        val_w = Fonts.small().size(value)[0]
        render_text(surface, value,
                    (x + w - val_w - 10, y + (h - 13) // 2),
                    font=Fonts.small(), color=val_color)
