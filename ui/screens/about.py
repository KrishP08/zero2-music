"""
About Screen — Tack UI landscape layout.
Shows device info: hostname, IP, storage, uptime, version.
"""

import subprocess
import os

from ui.screen_manager import Screen
from ui.theme import Colors, Fonts, draw_gradient_bg_cached, render_text, draw_rounded_rect
from ui.widgets import StatusBar, BottomNavBar, ScrollList
from hardware.input_handler import InputAction


class AboutScreen(Screen):
    """About device info screen."""

    def __init__(self, app):
        super().__init__(app)
        self.status_bar = StatusBar()
        self.bottom_nav = BottomNavBar()
        self.bottom_nav.active_tab = 3
        self.scroll_list = None

    def on_enter(self):
        self._build_info()

    def on_resume(self):
        pass

    def _build_info(self):
        items = [
            {"label": "Device", "value": self._get_hostname()},
            {"label": "IP Address", "value": self.app.wifi.get_ip_address() if self.app.wifi.available else "N/A"},
            {"label": "Bluetooth", "value": "Available" if self.app.bluetooth.available else "Not found"},
            {"label": "WiFi", "value": "Available" if self.app.wifi.available else "Not found"},
            {"label": "Tracks", "value": str(len(self.app.library.tracks))},
            {"label": "Storage", "value": self._get_storage()},
            {"label": "Uptime", "value": self._get_uptime()},
            {"label": "Version", "value": "Zero2 Music v1.0"},
        ]

        self.scroll_list = ScrollList(
            items, header="About",
            item_renderer=self._render_item,
            bottom_margin=BottomNavBar.HEIGHT,
        )

    def _get_hostname(self):
        try:
            import socket
            return socket.gethostname()
        except Exception:
            return "Unknown"

    def _get_storage(self):
        try:
            st = os.statvfs(os.path.expanduser("~"))
            free_gb = (st.f_bavail * st.f_frsize) / (1024 ** 3)
            total_gb = (st.f_blocks * st.f_frsize) / (1024 ** 3)
            return f"{free_gb:.1f}G / {total_gb:.1f}G"
        except Exception:
            return "N/A"

    def _get_uptime(self):
        try:
            result = subprocess.run(
                ["uptime", "-p"], capture_output=True, text=True, timeout=3
            )
            if result.returncode == 0:
                return result.stdout.strip().replace("up ", "")
        except Exception:
            pass
        return "N/A"

    def handle_input(self, action):
        if action == InputAction.SCROLL_UP:
            self.scroll_list.scroll_up()
        elif action == InputAction.SCROLL_DOWN:
            self.scroll_list.scroll_down()
        elif action == InputAction.BACK:
            self.app.screen_manager.pop()

    def update(self, dt):
        if self.scroll_list:
            self.scroll_list.update(dt)

    def render(self, surface, x_offset=0):
        draw_gradient_bg_cached(surface)
        self.status_bar.render(surface, x_offset)
        if self.scroll_list:
            self.scroll_list.render(surface, x_offset)
        self.bottom_nav.render(surface, x_offset)

    def _render_item(self, surface, item, rect, selected, x_offset):
        x, y, w, h = rect
        label = item.get("label", "")
        value = item.get("value", "")

        label_color = Colors.TEXT_PRIMARY if selected else Colors.TEXT_SECONDARY
        render_text(surface, label, (x + 12, y + (h - 14) // 2),
                    font=Fonts.body(), color=label_color)

        if value:
            val_color = Colors.ACCENT if selected else Colors.TEXT_MUTED
            val_w = Fonts.small().size(value)[0]
            render_text(surface, value,
                        (x + w - val_w - 8, y + (h - 10) // 2),
                        font=Fonts.small(), color=val_color)
