"""
Audio Engine — wraps pygame.mixer for music playback.
Handles play, pause, stop, skip, seek, and volume control.
Emits callbacks for UI updates.

Gracefully degrades to a no-op stub when pygame.mixer is
unavailable (e.g. pre-built wheel missing SDL2_mixer).
"""

import pygame
import time
import threading

# ── Check mixer availability ────────────────────────────────────────
_MIXER_AVAILABLE = False
try:
    import pygame.mixer
    _MIXER_AVAILABLE = True
except (ImportError, NotImplementedError):
    pass


class AudioEngine:
    """Core audio playback engine using pygame.mixer."""

    def __init__(self, frequency=44100, size=-16, channels=2, buffer=2048):
        self._mixer_ok = False
        self._volume = 0.7
        self._is_playing = False
        self._is_paused = False
        self._current_file = None
        self._track_length = 0.0
        self._start_pos = 0.0  # offset when seeking
        self._init_params = (frequency, size, channels, buffer)
        self._callbacks = {
            "on_track_end": [],
            "on_state_change": [],
        }

        self._try_init_mixer()

    def _try_init_mixer(self):
        """Attempt to initialize the pygame mixer."""
        if self._mixer_ok:
            return True
        if not _MIXER_AVAILABLE:
            return False
        try:
            freq, size, channels, buf = self._init_params
            if pygame.mixer.get_init():
                pygame.mixer.quit()
            pygame.mixer.pre_init(freq, size, channels, buf)
            pygame.mixer.init()
            pygame.mixer.music.set_endevent(pygame.USEREVENT + 1)
            pygame.mixer.music.set_volume(self._volume)
            self._mixer_ok = True
            print("[AudioEngine] ✓ Mixer initialized (audio ready)")
            return True
        except Exception as e:
            print(f"[AudioEngine] ⚠ Mixer init failed: {e}")
            self._mixer_ok = False
            return False

    def retry_init(self):
        """Retry mixer initialization (call after BT headphones connect)."""
        if not self._mixer_ok:
            return self._try_init_mixer()
        return True

    # ── Playback Controls ───────────────────────────────────────────
    def play(self, filepath):
        """Load and play an audio file."""
        # Auto-retry mixer init if it wasn't ready at startup
        if not self._mixer_ok:
            self._try_init_mixer()

        if not self._mixer_ok:
            self._current_file = filepath
            self._track_length = self._get_track_length(filepath)
            print(f"[AudioEngine] (no-op) Would play: {filepath}")
            print(f"[AudioEngine]   Connect Bluetooth headphones first!")
            return
        try:
            pygame.mixer.music.load(filepath)
            pygame.mixer.music.play()
            self._current_file = filepath
            self._is_playing = True
            self._is_paused = False
            self._start_pos = 0.0
            self._track_length = self._get_track_length(filepath)
            self._emit("on_state_change", "playing")
        except pygame.error as e:
            print(f"[AudioEngine] Error playing {filepath}: {e}")

    def pause(self):
        """Pause playback."""
        if not self._mixer_ok:
            return
        if self._is_playing and not self._is_paused:
            pygame.mixer.music.pause()
            self._is_paused = True
            self._emit("on_state_change", "paused")

    def unpause(self):
        """Resume playback."""
        if not self._mixer_ok:
            return
        if self._is_paused:
            pygame.mixer.music.unpause()
            self._is_paused = False
            self._emit("on_state_change", "playing")

    def toggle_pause(self):
        """Toggle between pause and play."""
        if self._is_paused:
            self.unpause()
        elif self._is_playing:
            self.pause()

    def stop(self):
        """Stop playback completely."""
        if self._mixer_ok:
            pygame.mixer.music.stop()
        self._is_playing = False
        self._is_paused = False
        self._start_pos = 0.0
        self._emit("on_state_change", "stopped")

    def seek(self, position_seconds):
        """Seek to a position in the current track (seconds)."""
        if not self._mixer_ok:
            return
        if self._current_file and self._is_playing:
            try:
                pygame.mixer.music.play(start=position_seconds)
                self._start_pos = position_seconds
                if self._is_paused:
                    pygame.mixer.music.pause()
            except pygame.error:
                pass

    # ── Volume ──────────────────────────────────────────────────────
    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, value):
        self._volume = max(0.0, min(1.0, value))
        if self._mixer_ok:
            pygame.mixer.music.set_volume(self._volume)

    def volume_up(self, step=0.05):
        self.volume = self._volume + step

    def volume_down(self, step=0.05):
        self.volume = self._volume - step

    # ── State Properties ────────────────────────────────────────────
    @property
    def is_playing(self):
        return self._is_playing and not self._is_paused

    @property
    def is_paused(self):
        return self._is_paused

    @property
    def current_file(self):
        return self._current_file

    @property
    def track_length(self):
        return self._track_length

    @property
    def position(self):
        """Current playback position in seconds."""
        if self._is_playing and self._mixer_ok:
            return self._start_pos + pygame.mixer.music.get_pos() / 1000.0
        return 0.0

    @property
    def progress(self):
        """Current playback progress as 0.0 – 1.0."""
        if self._track_length > 0:
            return min(1.0, self.position / self._track_length)
        return 0.0

    # ── Event Handling ──────────────────────────────────────────────
    def handle_event(self, event):
        """Call from main loop to handle pygame events."""
        if event.type == pygame.USEREVENT + 1:
            self._is_playing = False
            self._is_paused = False
            self._emit("on_track_end")

    def on(self, event_name, callback):
        """Register a callback for an event."""
        if event_name in self._callbacks:
            self._callbacks[event_name].append(callback)

    def _emit(self, event_name, *args):
        for cb in self._callbacks.get(event_name, []):
            try:
                cb(*args)
            except Exception as e:
                print(f"[AudioEngine] Callback error: {e}")

    # ── Helpers ─────────────────────────────────────────────────────
    def _get_track_length(self, filepath):
        """Get track duration in seconds using mutagen."""
        try:
            from mutagen import File as MutagenFile
            audio = MutagenFile(filepath)
            if audio and audio.info:
                return audio.info.length
        except Exception:
            pass
        return 0.0

    def cleanup(self):
        """Clean shutdown."""
        if self._mixer_ok:
            pygame.mixer.music.stop()
            pygame.mixer.quit()
