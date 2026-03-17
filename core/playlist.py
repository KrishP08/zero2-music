"""
Playlist & Queue — manages the play queue, shuffle, and repeat modes.
"""

import random


class RepeatMode:
    OFF = 0
    ALL = 1
    ONE = 2

    LABELS = {0: "Off", 1: "All", 2: "One"}


class Playlist:
    """Play queue with shuffle and repeat support."""

    def __init__(self):
        self._tracks = []          # original track order
        self._queue = []           # possibly shuffled order
        self._index = -1           # current index in _queue
        self._shuffle = False
        self._repeat = RepeatMode.OFF

    # ── Queue Management ────────────────────────────────────────────
    def set_tracks(self, tracks, start_index=0):
        """Set the queue from a list of Track objects."""
        self._tracks = list(tracks)
        if self._shuffle:
            self._queue = list(tracks)
            # Move start track to index 0, shuffle the rest
            if 0 <= start_index < len(self._queue):
                start_track = self._queue.pop(start_index)
                random.shuffle(self._queue)
                self._queue.insert(0, start_track)
                self._index = 0
            else:
                random.shuffle(self._queue)
                self._index = 0
        else:
            self._queue = list(tracks)
            self._index = start_index if 0 <= start_index < len(self._queue) else 0

    def add_track(self, track):
        """Add a track to the end of the queue."""
        self._tracks.append(track)
        self._queue.append(track)

    def clear(self):
        """Clear the queue."""
        self._tracks.clear()
        self._queue.clear()
        self._index = -1

    # ── Navigation ──────────────────────────────────────────────────
    @property
    def current_track(self):
        """Get the currently selected track."""
        if 0 <= self._index < len(self._queue):
            return self._queue[self._index]
        return None

    @property
    def current_index(self):
        return self._index

    @property
    def total_tracks(self):
        return len(self._queue)

    @property
    def has_tracks(self):
        return len(self._queue) > 0

    def next_track(self):
        """Advance to next track. Returns the track or None if at end."""
        if not self._queue:
            return None

        if self._repeat == RepeatMode.ONE:
            return self.current_track

        self._index += 1

        if self._index >= len(self._queue):
            if self._repeat == RepeatMode.ALL:
                self._index = 0
                if self._shuffle:
                    random.shuffle(self._queue)
            else:
                self._index = len(self._queue) - 1
                return None  # end of queue

        return self.current_track

    def prev_track(self):
        """Go to previous track."""
        if not self._queue:
            return None

        if self._repeat == RepeatMode.ONE:
            return self.current_track

        self._index -= 1
        if self._index < 0:
            if self._repeat == RepeatMode.ALL:
                self._index = len(self._queue) - 1
            else:
                self._index = 0

        return self.current_track

    # ── Shuffle & Repeat ────────────────────────────────────────────
    @property
    def shuffle(self):
        return self._shuffle

    @shuffle.setter
    def shuffle(self, enabled):
        if enabled and not self._shuffle:
            # Enable shuffle — keep current track, shuffle the rest
            current = self.current_track
            self._queue = list(self._tracks)
            random.shuffle(self._queue)
            if current and current in self._queue:
                self._queue.remove(current)
                self._queue.insert(0, current)
                self._index = 0
        elif not enabled and self._shuffle:
            # Disable shuffle — restore original order
            current = self.current_track
            self._queue = list(self._tracks)
            if current:
                try:
                    self._index = self._queue.index(current)
                except ValueError:
                    self._index = 0
        self._shuffle = enabled

    def toggle_shuffle(self):
        self.shuffle = not self._shuffle
        return self._shuffle

    @property
    def repeat(self):
        return self._repeat

    @repeat.setter
    def repeat(self, mode):
        self._repeat = mode

    def cycle_repeat(self):
        """Cycle through repeat modes: OFF → ALL → ONE → OFF."""
        self._repeat = (self._repeat + 1) % 3
        return self._repeat

    @property
    def repeat_label(self):
        return RepeatMode.LABELS[self._repeat]

    # ── Info ────────────────────────────────────────────────────────
    def get_queue_display(self, around=3):
        """Get tracks around current index for display."""
        if not self._queue:
            return [], -1

        start = max(0, self._index - around)
        end = min(len(self._queue), self._index + around + 1)
        return self._queue[start:end], self._index - start
