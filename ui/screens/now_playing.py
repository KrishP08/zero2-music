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
        if action == InputAction.BACK:
            self.app.screen_manager.pop()
        elif action == InputAction.PLAY_PAUSE:
            self.app.audio.toggle_pause()
        elif action == InputAction.NEXT_TRACK:
            self._next_track()
        elif action == InputAction.PREV_TRACK:
            self._prev_track()
        elif action == InputAction.SCROLL_UP:
            self.app.audio.volume_up()
            self.volume_overlay.show(self.app.audio.volume)
        elif action == InputAction.SCROLL_DOWN:
            self.app.audio.volume_down()
            self.volume_overlay.show(self.app.audio.volume)
        elif action == InputAction.SELECT:
            self.app.audio.toggle_pause()

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

        # ── Left Column: Album Art ──────────────────────────────
        art_x = x_offset + 14
        art_y = StatusBar.HEIGHT + 10

        # Glow behind art
        glow_surf = pygame.Surface(
            (self._art_size + 20, self._art_size + 20), pygame.SRCALPHA
        )
        pygame.draw.rect(
            glow_surf, (*Colors.ACCENT[:3], 12),
            (0, 0, self._art_size + 20, self._art_size + 20),
            border_radius=16
        )
        surface.blit(glow_surf, (art_x - 10, art_y - 10))

        if self._album_art_surface:
            art_mask = pygame.Surface(
                (self._art_size, self._art_size), pygame.SRCALPHA
            )
            pygame.draw.rect(
                art_mask, (255, 255, 255, 255),
                (0, 0, self._art_size, self._art_size),
                border_radius=10
            )
            masked_art = self._album_art_surface.copy()
            masked_art.blit(art_mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
            surface.blit(masked_art, (art_x, art_y))
        else:
            draw_rounded_rect(surface, Colors.BG_CARD,
                              (art_x, art_y, self._art_size, self._art_size), radius=10)

        # Border around art
        border_surf = pygame.Surface((self._art_size, self._art_size), pygame.SRCALPHA)
        pygame.draw.rect(border_surf, (255, 255, 255, 15),
                         (0, 0, self._art_size, self._art_size),
                         width=1, border_radius=10)
        surface.blit(border_surf, (art_x, art_y))

        # ── Right Column: Info + Controls ───────────────────────
        right_x = art_x + self._art_size + 16
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
        controls_y = prog_y + 24
        self.controls.render(surface,
                             (right_x, controls_y, right_w, 36),
                             is_playing=self.app.audio.is_playing,
                             x_offset=0)

        # ── Bottom Visualizer ───────────────────────────────────
        viz_y = config.SCREEN_HEIGHT - 4
        viz_w = config.SCREEN_WIDTH
        bar_count = 24
        bar_spacing = viz_w // bar_count
        import math, time as _time
        t = _time.time()
        for i in range(bar_count):
            bh = int(3 * (0.5 + 0.5 * math.sin(t * 2 + i * 0.5)))
            if bh < 1:
                bh = 1
            bx = x_offset + i * bar_spacing + 2
            pygame.draw.rect(surface, (*Colors.ACCENT[:3], 40),
                             (bx, viz_y - bh, bar_spacing - 2, bh))

        # ── Volume Overlay ──────────────────────────────────────
        self.volume_overlay.render(surface)

    def _format_time(self, seconds):
        m = int(seconds) // 60
        s = int(seconds) % 60
        return f"{m}:{s:02d}"
