"""
Now Playing Screen — album art, progress bar, controls.
The centerpiece of the player, Y1-inspired.
"""

import pygame
from io import BytesIO

from ui.screen_manager import Screen
from ui.theme import (
    Colors, Fonts, draw_gradient_bg_cached, draw_rounded_rect,
    draw_glass_panel, draw_progress_bar, render_text, draw_glow_circle
)
from ui.widgets import StatusBar, PlaybackControls, VolumeOverlay
from hardware.input_handler import InputAction
import config


class NowPlayingScreen(Screen):
    """Displays current track with album art and playback controls."""

    def __init__(self, app):
        super().__init__(app)
        self.status_bar = StatusBar()
        self.controls = PlaybackControls()
        self.volume_overlay = VolumeOverlay()
        self._album_art_surface = None
        self._current_art_file = None
        self._art_size = 140
        self._mode = "info"  # "info" or "controls"

    def on_enter(self):
        self._load_album_art()

    def _load_album_art(self):
        """Load album art from current track metadata."""
        track = self.app.playlist.current_track
        if not track:
            self._album_art_surface = None
            return

        # Avoid reloading for same track
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

        # Placeholder — gradient square
        self._album_art_surface = self._create_placeholder_art()

    def _create_placeholder_art(self):
        """Create a stylish placeholder album art."""
        size = self._art_size
        surf = pygame.Surface((size, size))
        for y in range(size):
            t = y / size
            r = int(30 * (1 - t) + 60 * t)
            g = int(40 * (1 - t) + 20 * t)
            b = int(80 * (1 - t) + 120 * t)
            pygame.draw.line(surf, (r, g, b), (0, y), (size, y))

        # Music note icon
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
        # If we're past 3 seconds, restart instead of going back
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
        self.status_bar.render(surface, x_offset)

        track = self.app.playlist.current_track
        cx = x_offset + config.SCREEN_WIDTH // 2

        # ── "Now Playing" header ────────────────────────────────
        render_text(surface, "Now Playing",
                    (cx, StatusBar.HEIGHT + 12),
                    font=Fonts.small(), color=Colors.TEXT_MUTED, center=True)

        # ── Album Art ───────────────────────────────────────────
        art_y = StatusBar.HEIGHT + 30
        art_x = cx - self._art_size // 2

        # Glow behind art
        glow_surf = pygame.Surface(
            (self._art_size + 40, self._art_size + 40), pygame.SRCALPHA
        )
        pygame.draw.rect(
            glow_surf, (*Colors.ACCENT[:3], 15),
            (0, 0, self._art_size + 40, self._art_size + 40),
            border_radius=20
        )
        surface.blit(glow_surf, (art_x - 20, art_y - 20))

        if self._album_art_surface:
            # Rounded corners via mask
            art_mask = pygame.Surface(
                (self._art_size, self._art_size), pygame.SRCALPHA
            )
            pygame.draw.rect(
                art_mask, (255, 255, 255, 255),
                (0, 0, self._art_size, self._art_size),
                border_radius=12
            )
            masked_art = self._album_art_surface.copy()
            masked_art.blit(art_mask, (0, 0),
                            special_flags=pygame.BLEND_RGBA_MIN)
            surface.blit(masked_art, (art_x, art_y))
        else:
            draw_rounded_rect(surface, Colors.BG_CARD,
                              (art_x, art_y, self._art_size, self._art_size),
                              radius=12)

        # ── Track Info ──────────────────────────────────────────
        info_y = art_y + self._art_size + 14

        if track:
            render_text(surface, track.display_title,
                        (cx, info_y),
                        font=Fonts.title(), color=Colors.TEXT_PRIMARY,
                        center=True, max_width=config.SCREEN_WIDTH - 30)
            render_text(surface, track.display_artist,
                        (cx, info_y + 22),
                        font=Fonts.body(), color=Colors.TEXT_SECONDARY,
                        center=True, max_width=config.SCREEN_WIDTH - 30)
        else:
            render_text(surface, "No track",
                        (cx, info_y),
                        font=Fonts.title(), color=Colors.TEXT_MUTED,
                        center=True)

        # ── Progress Bar ────────────────────────────────────────
        prog_y = info_y + 48
        bar_x = x_offset + 20
        bar_w = config.SCREEN_WIDTH - 40

        progress = self.app.audio.progress
        draw_progress_bar(surface, (bar_x, prog_y, bar_w, 4), progress)

        # Time labels
        if track:
            elapsed = self._format_time(self.app.audio.position)
            total = track.duration_str
        else:
            elapsed = "0:00"
            total = "0:00"

        render_text(surface, elapsed,
                    (bar_x, prog_y + 8),
                    font=Fonts.small(), color=Colors.TEXT_MUTED)
        total_w = Fonts.small().size(total)[0]
        render_text(surface, total,
                    (bar_x + bar_w - total_w, prog_y + 8),
                    font=Fonts.small(), color=Colors.TEXT_MUTED)

        # ── Playback Controls ───────────────────────────────────
        controls_y = prog_y + 34
        self.controls.render(surface, controls_y,
                             is_playing=self.app.audio.is_playing,
                             x_offset=x_offset)

        # ── Volume Overlay ──────────────────────────────────────
        self.volume_overlay.render(surface)

    def _format_time(self, seconds):
        m = int(seconds) // 60
        s = int(seconds) % 60
        return f"{m}:{s:02d}"
