"""
Bluetooth Screen — Tack UI landscape layout.
Scan, pair, and connect to Bluetooth devices.
"""

import threading
from ui.screen_manager import Screen
from ui.theme import Colors, Fonts, draw_gradient_bg_cached, render_text, draw_rounded_rect
from ui.widgets import StatusBar, BottomNavBar, ScrollList
from hardware.input_handler import InputAction
import config


class BluetoothScreen(Screen):
    """Bluetooth device management screen."""

    def __init__(self, app):
        super().__init__(app)
        self.status_bar = StatusBar()
        self.bottom_nav = BottomNavBar()
        self.bottom_nav.active_tab = 3
        self.scroll_list = None
        self._status_msg = ""
        self._action_thread = None

    def on_enter(self):
        bt = self.app.bluetooth
        if not bt.available:
            self._status_msg = "Bluetooth not available"
        elif bt.enabled:
            bt.start_scan()
        self._build_menu()

    def on_resume(self):
        self._build_menu()

    def _build_menu(self):
        bt = self.app.bluetooth
        items = []

        power_state = "On" if bt.enabled else "Off"
        items.append({"label": "Bluetooth", "value": power_state, "action": "toggle_power"})

        if bt.enabled:
            scan_label = "Scanning..." if bt.scanning else "Scan for Devices"
            items.append({"label": scan_label, "value": "", "action": "scan"})

            devices = bt.devices
            if devices:
                for dev in devices:
                    items.append({
                        "label": dev.name, "value": dev.status_text,
                        "action": "device", "mac": dev.mac, "device": dev,
                    })
            elif not bt.scanning:
                paired = bt.get_paired_devices()
                for dev in paired:
                    items.append({
                        "label": dev.name, "value": dev.status_text,
                        "action": "device", "mac": dev.mac, "device": dev,
                    })

        self.scroll_list = ScrollList(
            items, header="Bluetooth",
            item_renderer=self._render_item,
            bottom_margin=BottomNavBar.HEIGHT,
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
        bt = self.app.bluetooth

        if action == "toggle_power":
            bt.toggle_power()
            if bt.enabled:
                bt.start_scan()
            self._build_menu()
        elif action == "scan":
            if not bt.scanning:
                bt.start_scan()
                self._build_menu()
        elif action == "device":
            dev = item.get("device")
            if dev:
                if dev.connected:
                    self._status_msg = f"Disconnecting {dev.name}..."
                    self._async_action(lambda: bt.disconnect(dev.mac))
                else:
                    self._status_msg = f"Connecting to {dev.name}..."
                    self._async_action(lambda: bt.pair_and_connect(dev.mac))

    def _async_action(self, func):
        def worker():
            func()
            self._status_msg = ""
            self._build_menu()
        self._action_thread = threading.Thread(target=worker, daemon=True)
        self._action_thread.start()

    def update(self, dt):
        bt = self.app.bluetooth
        if self.scroll_list:
            if not bt.scanning and any(
                i.get("label") == "Scanning..." for i in self.scroll_list.items
            ):
                self._build_menu()
            self.scroll_list.update(dt)

    def render(self, surface, x_offset=0):
        draw_gradient_bg_cached(surface)
        self.status_bar.render(surface, x_offset)
        if self.scroll_list:
            self.scroll_list.render(surface, x_offset)
        self.bottom_nav.render(surface, x_offset)

        if self._status_msg:
            y = config.SCREEN_HEIGHT - BottomNavBar.HEIGHT - 28
            draw_rounded_rect(surface, (0, 0, 0, 200),
                              (x_offset + 10, y, config.SCREEN_WIDTH - 20, 24), radius=8)
            render_text(surface, self._status_msg,
                        (x_offset + config.SCREEN_WIDTH // 2, y + 12),
                        font=Fonts.small(), color=Colors.ACCENT, center=True)

    def _render_item(self, surface, item, rect, selected, x_offset):
        x, y, w, h = rect
        label = item.get("label", "")
        value = item.get("value", "")

        label_color = Colors.TEXT_PRIMARY if selected else Colors.TEXT_SECONDARY
        render_text(surface, label, (x + 12, y + (h - 14) // 2),
                    font=Fonts.body(), color=label_color, max_width=w - 80)

        if value:
            val_color = Colors.ACCENT if value == "Connected" else (
                Colors.BATTERY_GREEN if value == "On" else Colors.TEXT_MUTED
            )
            val_w = Fonts.small().size(value)[0]
            render_text(surface, value,
                        (x + w - val_w - 8, y + (h - 10) // 2),
                        font=Fonts.small(), color=val_color)
