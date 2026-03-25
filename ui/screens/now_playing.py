"""
Now Playing Screen — Tack UI landscape layout.
Album art left, track info + controls right.
"""

import pygame
from io import BytesIO

from ui.screen_manager import Screen
from ui.theme import (
    Colors, Fonts, draw_gradient_bg_cached, draw_rounded_rect,
    draw_glass_panel, draw_progress_bar, render_text, load_icon, tint_icon
)
from ui.widgets import StatusBar, VolumeOverlay, PlaybackControls
from hardware.input_handler import InputAction
import config


class NowPlayingScreen(Screen):
    """Landscape now-playing: album art left, controls right."""

    def __init__(self, app):
        super().__init__(app)
        self.status_bar = StatusBar()
        self.controls = PlaybackControls()
        self.volume_overlay = VolumeOverlay()
        self._album_art_surface = None
        self._current_art_file = None
        self._art_size = 124
        
        # Focus mode for accessing Shuffle/Repeat with clickwheel
        self.controls_focused = False
        self.focus_timer = 0.0
        
    def on_enter(self):
        self._load_album_art()

    def on_resume(self):
        self._load_album_art()

    def _load_album_art(self):
        track = self.app.playlist.current_track
        if not track:
            self._album_art_surface = None
            return

        if track.filepath == self._current_art_file:
            return

        self._current_art_file = track.filepath
        art_bytes = track.get_album_art_bytes()

        if art_bytes:
            try:
                image = pygame.image.load(BytesIO(art_bytes))
                self._album_art_surface = pygame.transform.smoothscale(
                    image, (self._art_size, self._art_size)
                )
                return
            except Exception:
                pass

        self._album_art_surface = self._create_placeholder_art()

    def _create_placeholder_art(self):
        size = self._art_size
        surf = pygame.Surface((size, size))
        for y in range(size):
            t = y / size
            r = int(20 * (1 - t) + 40 * t)
            g = int(28 * (1 - t) + 15 * t)
            b = int(60 * (1 - t) + 100 * t)
            pygame.draw.line(surf, (r, g, b), (0, y), (size, y))
        font = Fonts.huge()
        note = font.render("♪", True, (*Colors.ACCENT[:3],))
        note_rect = note.get_rect(center=(size // 2, size // 2))
        surf.blit(note, note_rect)
        return surf

    def handle_input(self, action):
        # Reset focus timer on any input
        if self.controls_focused:
            self.focus_timer = 3.0
            
        if action == InputAction.BACK:
            self.app.screen_manager.pop()
        elif action == InputAction.PLAY_PAUSE:
            self.app.audio.toggle_pause()
        elif action == InputAction.NEXT_TRACK:
            self._next_track()
        elif action == InputAction.PREV_TRACK:
            self._prev_track()
        elif action == InputAction.SCROLL_UP:
            if self.controls_focused:
                self.controls.selected = min(4, self.controls.selected + 1)
            else:
                self.app.audio.volume_up()
                self.volume_overlay.show(self.app.audio.volume)
        elif action == InputAction.SCROLL_DOWN:
            if self.controls_focused:
                self.controls.selected = max(0, self.controls.selected - 1)
            else:
                self.app.audio.volume_down()
                self.volume_overlay.show(self.app.audio.volume)
        elif action == InputAction.SELECT:
            if not self.controls_focused:
                # Enter focus mode
                self.controls_focused = True
                self.focus_timer = 3.0
                self.controls.selected = 2 # Highlight Play/Pause by default
            else:
                # Actuate focused button
                idx = self.controls.selected
                if idx == 0:
                    self.app.playlist.toggle_shuffle()
                elif idx == 1:
                    self._prev_track()
                elif idx == 2:
                    self.app.audio.toggle_pause()
                elif idx == 3:
                    self._next_track()
                elif idx == 4:
                    from core.playlist import RepeatMode
                    if self.app.playlist.repeat == RepeatMode.OFF:
                        self.app.playlist.repeat = RepeatMode.ALL
                    elif self.app.playlist.repeat == RepeatMode.ALL:
                        self.app.playlist.repeat = RepeatMode.ONE
                    else:
                        self.app.playlist.repeat = RepeatMode.OFF

    def _next_track(self):
        track = self.app.playlist.next_track()
        if track:
            self.app.audio.play(track.filepath)
            self._load_album_art()

    def _prev_track(self):
        if self.app.audio.position > 3.0:
            self.app.audio.seek(0)
        else:
            track = self.app.playlist.prev_track()
            if track:
                self.app.audio.play(track.filepath)
                self._load_album_art()

    def update(self, dt):
        self.volume_overlay.update(dt)
        if self.controls_focused:
            self.focus_timer -= dt
            if self.focus_timer <= 0:
                self.controls_focused = False
                
        # Auto update cover when track changes
        track = self.app.playlist.current_track
        if track and track.filepath != self._current_art_file:
            self._load_album_art()

    def render(self, surface, x_offset=0):
        draw_gradient_bg_cached(surface)

        # Status bar with format info
        track = self.app.playlist.current_track
        fmt_text = ""
        if track:
            ext = track.filepath.rsplit(".", 1)[-1].upper() if "." in track.filepath else ""
            fmt_text = f"{ext} · NOW PLAYING"
        else:
            fmt_text = "NOW PLAYING"

        self.status_bar.render(surface, x_offset, title=fmt_text)

        # Cava visualizer data with smoothing interpolation
        target_levels = self.app.cava.get_levels()
        bar_count = self.app.cava.bars
        
        if not hasattr(self, '_smoothed_levels') or len(self._smoothed_levels) != bar_count:
            self._smoothed_levels = [0.0] * bar_count
            
        for i in range(bar_count):
            t_val = target_levels[i] if i < len(target_levels) else 0.0
            # Easing: fast attack, slower decay
            if t_val > self._smoothed_levels[i]:
                self._smoothed_levels[i] += (t_val - self._smoothed_levels[i]) * 0.6
            else:
                self._smoothed_levels[i] += (t_val - self._smoothed_levels[i]) * 0.2
                
        levels = self._smoothed_levels
        
        if getattr(config, "THEME", "modern") == "retro":
            self._render_retro(surface, x_offset, levels)
            return
        
        # ── Left Column: Album Art ──────────────────────────────
        theme_round = getattr(config, "NOW_PLAYING_THEME", "square") == "round"
        
        if theme_round:
            art_x = x_offset + 24
            art_y = StatusBar.HEIGHT + 24
            
            # Circular Visualizer
            center_x = art_x + self._art_size // 2
            center_y = art_y + self._art_size // 2
            base_radius = self._art_size // 2 + 6
            
            import math
            for i in range(bar_count):
                angle = i * (math.pi * 2 / bar_count) - math.pi / 2
                val = levels[i]
                mag = int(val * 24)  # amplify for circle
                
                x1 = center_x + math.cos(angle) * base_radius
                y1 = center_y + math.sin(angle) * base_radius
                x2 = center_x + math.cos(angle) * (base_radius + 4 + mag)
                y2 = center_y + math.sin(angle) * (base_radius + 4 + mag)
                
                r = min(255, Colors.ACCENT_DIM[0] + int(val * 100))
                g = min(255, Colors.ACCENT_DIM[1] + int(val * 100))
                b = min(255, Colors.ACCENT_DIM[2] + int(val * 100))
                
                pygame.draw.line(surface, (r, g, b), (x1, y1), (x2, y2), 3)

            # Draw album art masked as a circle
            if self._album_art_surface:
                art_mask = pygame.Surface((self._art_size, self._art_size), pygame.SRCALPHA)
                pygame.draw.circle(art_mask, (255, 255, 255, 255), (self._art_size // 2, self._art_size // 2), self._art_size // 2)
                masked_art = self._album_art_surface.copy().convert_alpha()
                masked_art.blit(art_mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
                surface.blit(masked_art, (art_x, art_y))
            else:
                pygame.draw.circle(surface, Colors.BG_CARD, (center_x, center_y), self._art_size // 2)
                
            pygame.draw.circle(surface, (255, 255, 255, 20), (center_x, center_y), self._art_size // 2, width=1)
            right_x = art_x + self._art_size + 24
            
        else:
            # Classic Square Layout
            art_x = x_offset + 14
            art_y = StatusBar.HEIGHT + 10

            # Glow behind art
            glow_surf = pygame.Surface((self._art_size + 20, self._art_size + 20), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (*Colors.ACCENT[:3], 12), (0, 0, self._art_size + 20, self._art_size + 20), border_radius=16)
            surface.blit(glow_surf, (art_x - 10, art_y - 10))

            if self._album_art_surface:
                art_mask = pygame.Surface((self._art_size, self._art_size), pygame.SRCALPHA)
                pygame.draw.rect(art_mask, (255, 255, 255, 255), (0, 0, self._art_size, self._art_size), border_radius=10)
                masked_art = self._album_art_surface.copy().convert_alpha()
                masked_art.blit(art_mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
                surface.blit(masked_art, (art_x, art_y))
            else:
                draw_rounded_rect(surface, Colors.BG_CARD, (art_x, art_y, self._art_size, self._art_size), radius=10)

            # Border around art
            border_surf = pygame.Surface((self._art_size, self._art_size), pygame.SRCALPHA)
            pygame.draw.rect(border_surf, (255, 255, 255, 15), (0, 0, self._art_size, self._art_size), width=1, border_radius=10)
            surface.blit(border_surf, (art_x, art_y))
            
            right_x = art_x + self._art_size + 24
        # ── Right Column: Info + Controls ───────────────────────
        right_w = config.SCREEN_WIDTH - right_x - 10 + x_offset
        info_y = art_y + 4

        if track:
            # Track title
            render_text(surface, track.display_title,
                        (right_x, info_y),
                        font=Fonts.large(), color=Colors.ACCENT,
                        max_width=right_w)

            # Artist
            render_text(surface, track.display_artist,
                        (right_x, info_y + 26),
                        font=Fonts.body(), color=Colors.TEXT_SECONDARY,
                        max_width=right_w)
        else:
            render_text(surface, "No track",
                        (right_x, info_y),
                        font=Fonts.large(), color=Colors.TEXT_MUTED)

        # ── Progress Bar ────────────────────────────────────────
        prog_y = info_y + 52
        bar_w = right_w
        progress = self.app.audio.progress
        draw_progress_bar(surface, (right_x, prog_y, bar_w, 5), progress)

        # Time labels
        if track:
            elapsed = self._format_time(self.app.audio.position)
            total = track.duration_str
        else:
            elapsed = "0:00"
            total = "0:00"

        render_text(surface, elapsed,
                    (right_x, prog_y + 8),
                    font=Fonts.tiny(), color=Colors.TEXT_MUTED)
        total_w = Fonts.tiny().size(total)[0]
        render_text(surface, total,
                    (right_x + bar_w - total_w, prog_y + 8),
                    font=Fonts.tiny(), color=Colors.TEXT_MUTED)

        # ── Playback Controls ───────────────────────────────────
        from core.playlist import RepeatMode
        controls_y = prog_y + 24
        
        # Override PlaybackControls rendering if not focused
        orig_selected = self.controls.selected
        if not self.controls_focused:
            self.controls.selected = -1 # Draw without active highlight circle
            
        self.controls.render(surface,
                             (right_x - 20, controls_y, right_w + 10, 36),
                             is_playing=self.app.audio.is_playing,
                             shuffle_on=self.app.playlist.shuffle,
                             repeat_on=(self.app.playlist.repeat != RepeatMode.OFF),
                             x_offset=0)
                             
        self.controls.selected = orig_selected

        if not theme_round:
            # ── Bottom Linear Visualizer ────────────────────────────
            viz_y = config.SCREEN_HEIGHT - 6
            viz_w = config.SCREEN_WIDTH
            bar_w = viz_w // bar_count
            
            BAR_COLOR_TOP = (130, 100, 220)
            BAR_COLOR_BOT = (200, 160, 255)
            
            for i in range(bar_count):
                val = levels[i]
                bar_h = max(2, int(val * 40)) # max height 40px at bottom
                
                bx = x_offset + i * bar_w + 1
                bw = bar_w - 2
                
                # Dynamic solid color based on height instead of slow per-pixel gradient
                r = int(BAR_COLOR_BOT[0] + (BAR_COLOR_TOP[0] - BAR_COLOR_BOT[0]) * val)
                g = int(BAR_COLOR_BOT[1] + (BAR_COLOR_TOP[1] - BAR_COLOR_BOT[1]) * val)
                b = int(BAR_COLOR_BOT[2] + (BAR_COLOR_TOP[2] - BAR_COLOR_BOT[2]) * val)
                
                pygame.draw.rect(surface, (r, g, b), (bx, viz_y - bar_h, bw, bar_h), border_radius=2)

        # ── Volume Overlay ──────────────────────────────────────
        self.volume_overlay.render(surface)

    def _render_retro(self, surface, x_offset, levels):
        surface.fill(Colors.RETRO_BG_DARK)
        
        # Draw top status bar
        track = self.app.playlist.current_track
        fmt_text = ""
        if track:
            ext = track.filepath.rsplit(".", 1)[-1].upper() if "." in track.filepath else ""
            fmt_text = f"{ext} CASETTE DECK"
        else:
            fmt_text = "NO TAPE DECK"
            
        self.status_bar.render(surface, x_offset, title=fmt_text)
        
        # Tape Cassette Body
        cw, ch = 240, 150
        cx = x_offset + (config.SCREEN_WIDTH - cw) // 2
        cy = 28
        
        # Cassette Outer Shell
        draw_rounded_rect(surface, (*Colors.RETRO_PRIMARY[:3], 30), (cx, cy, cw, ch), radius=12)
        pygame.draw.rect(surface, Colors.RETRO_PRIMARY, (cx, cy, cw, ch), width=2, border_radius=12)
        
        # Top corner screws
        pygame.draw.circle(surface, Colors.RETRO_PRIMARY, (cx + 12, cy + 12), 3, 1)
        pygame.draw.circle(surface, Colors.RETRO_PRIMARY, (cx + cw - 12, cy + 12), 3, 1)
        pygame.draw.circle(surface, Colors.RETRO_PRIMARY, (cx + 12, cy + ch - 12), 3, 1)
        pygame.draw.circle(surface, Colors.RETRO_PRIMARY, (cx + cw - 12, cy + ch - 12), 3, 1)
        
        # Cassette Sticker
        sw, sh = 190, 85
        sx = cx + (cw - sw) // 2
        sy = cy + 16
        pygame.draw.rect(surface, Colors.RETRO_BG_LIGHT, (sx, sy, sw, sh), border_radius=6)
        
        if self._album_art_surface:
            art_scaled = pygame.transform.smoothscale(self._album_art_surface, (sw, sh))
            art_scaled.set_alpha(150)
            surface.blit(art_scaled, (sx, sy))
        
        track = self.app.playlist.current_track
        track_name = track.display_title if track else "NO TAPE IN DECK"
        
        # Sticker Text
        render_text(surface, "A", (sx + 10, sy + 6), font=Fonts.body(bold=True), color=Colors.RETRO_BG_DARK)
        render_text(surface, "MIX TAPE", (sx + sw // 2 - 30, sy + 6), font=Fonts.tiny(bold=True), color=(150, 0, 0))
        render_text(surface, track_name[:24].upper(), (sx + 24, sy + 24), font=Fonts.tiny(bold=True), color=Colors.RETRO_BG_DARK)
        
        # Transparent Window (Dark rectangle in the middle of sticker)
        ww, wh = 130, 36
        wx = sx + (sw - ww) // 2
        wy = sy + 40
        pygame.draw.rect(surface, Colors.RETRO_BG_DARK, (wx, wy, ww, wh), border_radius=4)
        pygame.draw.rect(surface, Colors.RETRO_PRIMARY, (wx, wy, ww, wh), width=1, border_radius=4)

        # Reels inside window
        progress = self.app.audio.progress
        import math, time
        time_sec = self.app.audio.position
        
        left_r = 15 - 8 * progress
        right_r = 7 + 8 * progress
        
        reel_ly = wy + wh // 2
        reel_lx = wx + 28
        reel_ry = wy + wh // 2
        reel_rx = wx + ww - 28
        
        # Draw tape path between reels
        pygame.draw.line(surface, Colors.RETRO_BG_LIGHT, (reel_lx, reel_ly - left_r), (reel_rx, reel_ry - right_r), 1)
        
        # Left Reel
        pygame.draw.circle(surface, Colors.RETRO_BG_LIGHT, (reel_lx, reel_ly), int(left_r))
        pygame.draw.circle(surface, Colors.RETRO_BG_DARK, (reel_lx, reel_ly), 6)
        
        # Right Reel
        pygame.draw.circle(surface, Colors.RETRO_BG_LIGHT, (reel_rx, reel_ry), int(right_r))
        pygame.draw.circle(surface, Colors.RETRO_BG_DARK, (reel_rx, reel_ry), 6)
        
        # Reel rotation
        if self.app.audio.is_playing:
            angle_l = time_sec * 4
            angle_r = time_sec * 4
        else:
            angle_l = 0
            angle_r = 0
            
        for i in range(3):
            a = angle_l + i * (math.pi * 2 / 3)
            x2 = reel_lx + math.cos(a) * 6
            y2 = reel_ly + math.sin(a) * 6
            pygame.draw.line(surface, Colors.RETRO_BG_LIGHT, (reel_lx, reel_ly), (x2, y2), 2)
            
            a2 = angle_r + i * (math.pi * 2 / 3)
            x3 = reel_rx + math.cos(a2) * 6
            y3 = reel_ry + math.sin(a2) * 6
            pygame.draw.line(surface, Colors.RETRO_BG_LIGHT, (reel_rx, reel_ry), (x3, y3), 2)
            
        # Bottom Trapezoid of tape
        bx = cx + 30
        bw = cw - 60
        by = cy + ch - 35
        bh = 35
        pygame.draw.polygon(surface, (*Colors.RETRO_PRIMARY[:3], 30), [
            (bx + 15, by), (bx + bw - 15, by),
            (bx + bw, by + bh), (bx, by + bh)
        ])
        pygame.draw.polygon(surface, Colors.RETRO_PRIMARY, [
            (bx + 15, by), (bx + bw - 15, by),
            (bx + bw, by + bh), (bx, by + bh)
        ], 1)
        
        # Tape holes in trapezoid
        pygame.draw.circle(surface, Colors.RETRO_BG_DARK, (bx + 25, by + 16), 5)
        pygame.draw.circle(surface, Colors.RETRO_BG_DARK, (bx + bw - 25, by + 16), 5)

        # ── LED Level Meters ──
        avg_level = sum(levels) / len(levels) if levels else 0
        
        num_segments = 14
        segment_w = 10
        segment_h = 6
        gap = 3
        meter_w = num_segments * (segment_w + gap)
        mx = x_offset + (config.SCREEN_WIDTH - meter_w) // 2 + 8
        my = cy + ch + 12
        
        render_text(surface, "L", (mx - 18, my - 3), font=Fonts.tiny(bold=True), color=Colors.RETRO_PRIMARY)
        render_text(surface, "R", (mx - 18, my + segment_h + gap - 3), font=Fonts.tiny(bold=True), color=Colors.RETRO_PRIMARY)
        
        import random
        lit_segments_l = min(num_segments, int(avg_level * num_segments * 1.8))
        lit_segments_r = min(num_segments, int(avg_level * num_segments * 1.8 + (random.random() * 2 - 1) if lit_segments_l > 0 else 0))
        
        for chn, lit_count in enumerate([lit_segments_l, lit_segments_r]):
            y = my + chn * (segment_h + gap)
            for i in range(num_segments):
                x = mx + i * (segment_w + gap)
                isOn = i < lit_count
                color = Colors.RETRO_PRIMARY if i < 10 else Colors.RETRO_ORANGE_DARK
                
                if isOn:
                    pygame.draw.rect(surface, color, (x, y, segment_w, segment_h))
                else:
                    pygame.draw.rect(surface, (*color[:3], 30), (x, y, segment_w, segment_h))
                    
        # ── Status and Controls at bottom ──
        elapsed = self._format_time(time_sec)
        total = track.duration_str if track else "0:00"
        render_text(surface, f"{elapsed} / {total}", (x_offset + 12, config.SCREEN_HEIGHT - 24), font=Fonts.tiny(bold=True), color=Colors.RETRO_PRIMARY)
        
        if self.controls_focused:
            opts = ["SHUFFLE", "PREV", "PLAY/PAUSE", "NEXT", "REPEAT"]
            idx = self.controls.selected
            # Pulsing highlight color — clamp to valid 0-255 range
            pulse = int((math.sin(time.time() * 8) + 1) * 60)
            sel_color = (255, min(255, 150 + pulse), min(255, pulse))
            render_text(surface, f"[{opts[idx]}]", (x_offset + config.SCREEN_WIDTH - 90, config.SCREEN_HEIGHT - 24), font=Fonts.tiny(bold=True), color=sel_color)
        else:
            active_str = ""
            if getattr(self.app.playlist, "shuffle", False): active_str += "SHUF "
            if getattr(self.app.playlist, "repeat", 0) != 0: active_str += "RPT"
            render_text(surface, active_str, (x_offset + config.SCREEN_WIDTH - 60, config.SCREEN_HEIGHT - 24), font=Fonts.tiny(bold=True), color=(120, 80, 30))

        self.volume_overlay.render(surface)

    def _format_time(self, seconds):
        m = int(seconds) // 60
        s = int(seconds) % 60
        return f"{m}:{s:02d}"

