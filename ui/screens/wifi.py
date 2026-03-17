"""
WiFi Screen — scan and connect to WiFi networks.
"""

import threading
from ui.screen_manager import Screen
from ui.theme import Colors, Fonts, draw_gradient_bg_cached, render_text, draw_rounded_rect
from ui.widgets import StatusBar, ScrollList
from hardware.input_handler import InputAction
import config


class WiFiScreen(Screen):
    """WiFi network management screen."""

    def __init__(self, app):
        super().__init__(app)
        self.status_bar = StatusBar()
        self.scroll_list = None
        self._status_msg = ""
        self._action_thread = None

    def on_enter(self):
        wifi = self.app.wifi
        if not wifi.available:
            self._status_msg = "WiFi not available"
        elif wifi.enabled:
            wifi.start_scan()
        self._build_menu()

    def _build_menu(self):
        wifi = self.app.wifi
        items = []

        # Power toggle
        power_state = "On" if wifi.enabled else "Off"
        items.append({
            "label": "WiFi",
            "value": power_state,
            "action": "toggle_power",
        })

        if wifi.enabled:
            # Current connection
            current = wifi.get_current_network()
            if current:
                items.append({
                    "label": f"Connected: {current}",
                    "value": "Disconnect",
                    "action": "disconnect",
                })
                # IP address
                ip = wifi.get_ip_address()
                items.append({
                    "label": f"IP: {ip}",
                    "value": "",
                    "action": "none",
                })

            # Scan button
            scan_label = "Scanning..." if wifi.scanning else "Scan Networks"
            items.append({
                "label": scan_label,
                "value": "",
                "action": "scan",
            })

            # Network list
            networks = wifi.networks
            for net in networks:
                if net.connected:
                    continue  # Already shown above
                items.append({
                    "label": net.ssid,
                    "value": net.signal_bars,
                    "action": "connect",
                    "network": net,
                    "status": net.status_text,
                })

        self.scroll_list = ScrollList(
            items, header="WiFi",
            item_renderer=self._render_item
        )

    def handle_input(self, action):
        if action == InputAction.SCROLL_UP:
            self.scroll_list.scroll_up()
        elif action == InputAction.SCROLL_DOWN:
            self.scroll_list.scroll_down()
        elif action == InputAction.SELECT:
            self._handle_select()
        elif action == InputAction.BACK:
            self.app.screen_manager.pop()

    def _handle_select(self):
        item = self.scroll_list.selected_item
        if not item:
            return

        action = item.get("action")
        wifi = self.app.wifi

        if action == "toggle_power":
            wifi.toggle_power()
            if wifi.enabled:
                wifi.start_scan()
            self._build_menu()

        elif action == "scan":
            if not wifi.scanning:
                wifi.start_scan()
                self._build_menu()

        elif action == "disconnect":
            self._status_msg = "Disconnecting..."
            self._async_action(lambda: wifi.disconnect())

        elif action == "connect":
            net = item.get("network")
            if net:
                if net.saved:
                    self._status_msg = f"Connecting to {net.ssid}..."
                    self._async_action(lambda: wifi.connect(net.ssid))
                else:
                    self._status_msg = f"Not saved. Connect via terminal first"

    def _async_action(self, func):
        def worker():
            func()
            self._status_msg = ""
            self._build_menu()
        self._action_thread = threading.Thread(target=worker, daemon=True)
        self._action_thread.start()

    def update(self, dt):
        wifi = self.app.wifi
        if self.scroll_list:
            if not wifi.scanning and any(
                i.get("label") == "Scanning..." for i in self.scroll_list.items
            ):
                self._build_menu()
            self.scroll_list.update(dt)

    def render(self, surface, x_offset=0):
        draw_gradient_bg_cached(surface)
        self.status_bar.render(surface, x_offset)
        if self.scroll_list:
            self.scroll_list.render(surface, x_offset)

        # Status overlay
        if self._status_msg:
            y = config.SCREEN_HEIGHT - 40
            draw_rounded_rect(surface, (0, 0, 0, 180),
                              (x_offset + 10, y, config.SCREEN_WIDTH - 20, 30), radius=8)
            render_text(surface, self._status_msg,
                        (x_offset + config.SCREEN_WIDTH // 2, y + 15),
                        font=Fonts.small(), color=Colors.ACCENT, center=True)

    def _render_item(self, surface, item, rect, selected, x_offset):
        x, y, w, h = rect
        label = item.get("label", "")
        value = item.get("value", "")
        status = item.get("status", "")

        # Label
        label_color = Colors.TEXT_PRIMARY if selected else Colors.TEXT_SECONDARY
        max_w = w - 90 if value else w - 30
        render_text(surface, label, (x + 14, y + (h - 16) // 2),
                    font=Fonts.body(), color=label_color,
                    max_width=max_w)

        # Status text (Saved, WPA2, etc.)
        if status and not value:
            st_w = Fonts.small().size(status)[0]
            render_text(surface, status,
                        (x + w - st_w - 10, y + (h - 13) // 2),
                        font=Fonts.small(), color=Colors.TEXT_MUTED)

        # Value (signal bars, On/Off, Disconnect)
        if value:
            if value in ("On", "Connected", "Disconnect"):
                val_color = Colors.BATTERY_GREEN if value == "On" else Colors.ACCENT
            else:
                val_color = Colors.ACCENT if selected else Colors.TEXT_MUTED
            val_w = Fonts.small().size(value)[0]
            render_text(surface, value,
                        (x + w - val_w - 10, y + (h - 13) // 2),
                        font=Fonts.small(), color=val_color)
