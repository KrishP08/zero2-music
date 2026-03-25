"""
Settings Screen — Tack UI landscape 2-column card layout.
"""

import pygame
from ui.screen_manager import Screen
from ui.theme import Colors, Fonts, draw_gradient_bg_cached, render_text, draw_rounded_rect, load_icon, tint_icon
from ui.widgets import StatusBar, BottomNavBar
from hardware.input_handler import InputAction
import config


class SettingsScreen(Screen):
    """Settings with 2-column card grid layout."""

    def __init__(self, app):
        super().__init__(app)
        self.status_bar = StatusBar()
        self.bottom_nav = BottomNavBar()
        self.bottom_nav.active_tab = 3  # Settings tab
        self.selected_index = 0
        self._cards = []
        self._icons = {}
        self._load_icons()

    def _load_icons(self):
        for name in ("wifi", "bluetooth", "settings", "album", "repeat"):
            icon = load_icon(name, size=(18, 18))
            if icon:
                self._icons[name] = icon

    def on_enter(self):
        self._build_cards()

    def on_resume(self):
        self._build_cards()

    def _build_cards(self):
        bt = self.app.bluetooth
        wifi = self.app.wifi

        wifi_net = wifi.get_current_network() if wifi.available else None

        self._cards = [
            {
                "label": "Theme",
                "subtitle": getattr(config, "THEME", "modern").title(),
                "icon": "settings",
                "enabled": getattr(config, "THEME", "modern") == "retro",
                "action": "theme",
            },
            {
                "label": "WiFi",
                "subtitle": wifi_net or "Not connected",
                "icon": "wifi",
                "enabled": wifi.enabled,
                "action": "wifi",
            },
            {
                "label": "Bluetooth",
                "subtitle": "Available" if bt.available else "Not found",
                "icon": "bluetooth",
                "enabled": bt.enabled,
                "action": "bluetooth",
            },
            {
                "label": "Shuffle",
                "subtitle": "On" if self.app.playlist.shuffle else "Off",
                "icon": "settings",
                "enabled": self.app.playlist.shuffle,
                "action": "shuffle",
            },
            {
                "label": "Repeat",
                "subtitle": self.app.playlist.repeat_label,
                "icon": "repeat",
                "enabled": self.app.playlist.repeat != 0,
                "action": "repeat",
            },
            {
                "label": "About",
                "subtitle": "Zero2 Music v1.0",
                "icon": "album",
                "enabled": None,  # No toggle
                "action": "about",
            },
        ]

    def handle_input(self, action):
        if action == InputAction.SCROLL_UP:
            if self.selected_index > 1:
                self.selected_index -= 2
        elif action == InputAction.SCROLL_DOWN:
            if self.selected_index + 2 < len(self._cards):
                self.selected_index += 2
        elif action == InputAction.NEXT_TRACK:
            if self.selected_index % 2 == 0 and self.selected_index + 1 < len(self._cards):
                self.selected_index += 1
        elif action == InputAction.PREV_TRACK:
            if self.selected_index % 2 == 1:
                self.selected_index -= 1
        elif action == InputAction.SELECT:
            self._handle_select()
        elif action == InputAction.BACK:
            self.app.screen_manager.pop()

    def _handle_select(self):
        if self.selected_index >= len(self._cards):
            return
        card = self._cards[self.selected_index]
        action = card.get("action")

        if action == "wifi":
            from ui.screens.wifi import WiFiScreen
            self.app.screen_manager.push(WiFiScreen(self.app))
        elif action == "bluetooth":
            from ui.screens.bluetooth import BluetoothScreen
            self.app.screen_manager.push(BluetoothScreen(self.app))
        elif action == "theme":
            current = getattr(config, "THEME", "modern")
            config.THEME = "retro" if current == "modern" else "modern"
            self._build_cards()
        elif action == "shuffle":
            self.app.playlist.toggle_shuffle()
            self._build_cards()
        elif action == "repeat":
            from core.playlist import RepeatMode
            if self.app.playlist.repeat == RepeatMode.OFF:
                self.app.playlist.repeat = RepeatMode.ALL
            elif self.app.playlist.repeat == RepeatMode.ALL:
                self.app.playlist.repeat = RepeatMode.ONE
            else:
                self.app.playlist.repeat = RepeatMode.OFF
            self._build_cards()
        elif action == "about":
            from ui.screens.about import AboutScreen
            self.app.screen_manager.push(AboutScreen(self.app))

    def update(self, dt):
        pass

    def render(self, surface, x_offset=0):
        is_retro = getattr(config, "THEME", "modern") == "retro"
        
        if is_retro:
            self._render_retro(surface, x_offset)
        else:
            draw_gradient_bg_cached(surface)
            self.status_bar.render(surface, x_offset)

            # Title row
            header_y = StatusBar.HEIGHT + 2
            icon = self._icons.get("settings")
            if icon:
                tinted = tint_icon(icon, Colors.ACCENT)
                surface.blit(tinted, (x_offset + 10, header_y + 2))
            render_text(surface, "SETTINGS",
                        (x_offset + 32, header_y + 2),
                        font=Fonts.tiny(), color=Colors.TEXT_PRIMARY)

            # 2-column card grid
            grid_y = header_y + 22
            grid_x = x_offset + 8
            card_w = (config.SCREEN_WIDTH - 24) // 2
            card_h = 72
            gap = 8

            target_row = self.selected_index // 2
            scroll_offset = max(0, (target_row - 1) * (card_h + gap))
            
            clip_rect = pygame.Rect(x_offset, grid_y - 2, config.SCREEN_WIDTH, config.SCREEN_HEIGHT - grid_y - 32)
            surface.set_clip(clip_rect)

            for i, card in enumerate(self._cards):
                col = i % 2
                row = i // 2
                cx = grid_x + col * (card_w + gap)
                cy = grid_y + row * (card_h + gap) - scroll_offset
                selected = (i == self.selected_index)

                self._render_card(surface, card, (cx, cy, card_w, card_h), selected)

            surface.set_clip(None)
            self.bottom_nav.render(surface, x_offset)
            
    def _render_retro(self, surface, x_offset):
        surface.fill(Colors.RETRO_BG_DARK)
        
        self.status_bar.render(surface, x_offset, title="SYSTEM PARAMETERS")
        
        # ── Header ──
        render_text(surface, "SETTINGS", (x_offset + 24, 30), font=Fonts.body(bold=True), color=(240, 240, 240))
        
        # ── 2x2 Grid (matching main menu style) ──
        grid_y = 56
        gw, gh = 138, 55
        gap = 10
        start_x = x_offset + (config.SCREEN_WIDTH - (gw * 2 + gap)) // 2
        
        for i, card in enumerate(self._cards):
            if i >= 6:  # Max 6 cards (3 rows)
                break
            col = i % 2
            row = i // 2
            bx = start_x + col * (gw + gap)
            by = grid_y + row * (gh + gap)
            
            selected = (i == self.selected_index)
            label = card.get("label", "").upper()
            enabled = card.get("enabled")
            
            # Alternating button styles
            if enabled:
                bg_color = Colors.RETRO_PRIMARY
                text_color = Colors.RETRO_BG_DARK
            else:
                bg_color = (60, 45, 20)
                text_color = Colors.RETRO_PRIMARY
            
            if selected:
                by += 2  # pressed effect
                draw_rounded_rect(surface, bg_color, (bx, by, gw, gh), radius=8)
            else:
                draw_rounded_rect(surface, bg_color, (bx, by, gw, gh), radius=8)
                shadow_color = Colors.RETRO_ORANGE_DARK if enabled else (40, 30, 15)
                pygame.draw.rect(surface, shadow_color, 
                                 (bx, by + gh - 4, gw, 4), border_bottom_left_radius=8, border_bottom_right_radius=8)
                 
            # Outline for non-enabled
            if not enabled:
                pygame.draw.rect(surface, (120, 80, 30), (bx, by, gw, gh), width=2, border_radius=8)

            # Label text
            label_surf = Fonts.tiny(bold=True).render(label, True, text_color)
            surface.blit(label_surf, (bx + gw//2 - label_surf.get_width()//2, by + 10))
            
            # Status text below label
            subtitle = str(card.get("subtitle", "")).upper()
            sub_color = Colors.RETRO_BG_DARK if enabled else (150, 100, 40)
            sub_surf = Fonts.tiny().render(subtitle, True, sub_color)
            surface.blit(sub_surf, (bx + gw//2 - sub_surf.get_width()//2, by + gh - 22))

        self.bottom_nav.render(surface, x_offset)

    def _render_card(self, surface, card, rect, selected):
        x, y, w, h = rect
        label = card.get("label", "")
        subtitle = card.get("subtitle", "")
        icon_name = card.get("icon", "")
        enabled = card.get("enabled")

        # Card background
        bg_color = Colors.BG_CARD if not selected else Colors.BG_CARD_HIGHLIGHT
        draw_rounded_rect(surface, bg_color, (x, y, w, h), radius=10)

        # Selection border
        if selected:
            border_surf = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.rect(border_surf, (*Colors.ACCENT[:3], 60),
                             (0, 0, w, h), width=1, border_radius=10)
            surface.blit(border_surf, (x, y))

        # Top row: icon + toggle
        # Icon badge
        icon_surf = self._icons.get(icon_name)
        badge_size = 26
        draw_rounded_rect(surface, (*Colors.ACCENT[:3], 40),
                          (x + 8, y + 8, badge_size, badge_size), radius=6)
        if icon_surf:
            tinted = tint_icon(icon_surf, Colors.ACCENT)
            surface.blit(tinted, (x + 12, y + 12))

        # Toggle switch (if applicable)
        if enabled is not None:
            sw_w, sw_h = 32, 16
            sw_x = x + w - sw_w - 8
            sw_y = y + 12
            if enabled:
                draw_rounded_rect(surface, Colors.ACCENT,
                                  (sw_x, sw_y, sw_w, sw_h), radius=sw_h // 2)
                # Knob
                pygame.draw.circle(surface, Colors.WHITE,
                                   (sw_x + sw_w - sw_h // 2, sw_y + sw_h // 2),
                                   sw_h // 2 - 2)
            else:
                draw_rounded_rect(surface, (60, 70, 90),
                                  (sw_x, sw_y, sw_w, sw_h), radius=sw_h // 2)
                pygame.draw.circle(surface, Colors.TEXT_MUTED,
                                   (sw_x + sw_h // 2, sw_y + sw_h // 2),
                                   sw_h // 2 - 2)
        else:
            # Chevron for navigation cards
            render_text(surface, "›", (x + w - 14, y + 14),
                        font=Fonts.body(), color=Colors.TEXT_MUTED)

        # Labels at bottom
        render_text(surface, label, (x + 8, y + h - 30),
                    font=Fonts.body(), color=Colors.TEXT_PRIMARY)
        render_text(surface, subtitle, (x + 8, y + h - 14),
                    font=Fonts.tiny(), color=Colors.TEXT_MUTED,
                    max_width=w - 16)
