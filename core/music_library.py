"""
Music Library — scans directories, extracts metadata, builds indexed library.
Uses mutagen for metadata extraction and caches to JSON for fast startup.
"""

import os
import json
import hashlib
from io import BytesIO

from mutagen import File as MutagenFile
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.id3 import ID3

import config


class Track:
    """Represents a single music track with its metadata."""

    def __init__(self, filepath, title=None, artist=None, album=None,
                 duration=0.0, track_num=0, genre=None, album_art_data=None):
        self.filepath = filepath
        self.title = title or os.path.splitext(os.path.basename(filepath))[0]
        self.artist = artist or "Unknown Artist"
        self.album = album or "Unknown Album"
        self.duration = duration
        self.track_num = track_num
        self.genre = genre or "Unknown"
        self._album_art_data = album_art_data  # raw bytes, lazy-loaded

    @property
    def display_title(self):
        return self.title

    @property
    def display_artist(self):
        return self.artist

    @property
    def duration_str(self):
        """Format duration as M:SS."""
        m = int(self.duration) // 60
        s = int(self.duration) % 60
        return f"{m}:{s:02d}"

    def get_album_art_bytes(self):
        """Return raw album art image bytes, or None."""
        return self._album_art_data

    def to_dict(self):
        return {
            "filepath": self.filepath,
            "title": self.title,
            "artist": self.artist,
            "album": self.album,
            "duration": self.duration,
            "track_num": self.track_num,
            "genre": self.genre,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(
            filepath=d["filepath"],
            title=d.get("title"),
            artist=d.get("artist"),
            album=d.get("album"),
            duration=d.get("duration", 0.0),
            track_num=d.get("track_num", 0),
            genre=d.get("genre"),
        )


class MusicLibrary:
    """Scans and indexes a music directory."""

    def __init__(self, music_dir=None):
        self.music_dir = music_dir or config.MUSIC_DIRECTORY
        self.tracks = []           # flat list of all Track objects
        self._artists = {}         # artist -> [Track]
        self._albums = {}          # album -> [Track]
        self._genres = {}          # genre -> [Track]

    def scan(self):
        """Scan music directory and extract metadata for all tracks."""
        self.tracks.clear()
        self._artists.clear()
        self._albums.clear()
        self._genres.clear()

        if not os.path.isdir(self.music_dir):
            print(f"[Library] Music directory not found: {self.music_dir}")
            return

        for root, dirs, files in os.walk(self.music_dir):
            for fname in sorted(files):
                if fname.lower().endswith(config.SUPPORTED_FORMATS):
                    filepath = os.path.join(root, fname)
                    track = self._extract_metadata(filepath)
                    if track:
                        self.tracks.append(track)

        # Build indices
        for track in self.tracks:
            self._artists.setdefault(track.artist, []).append(track)
            self._albums.setdefault(track.album, []).append(track)
            self._genres.setdefault(track.genre, []).append(track)

        # Sort albums by track number
        for album_tracks in self._albums.values():
            album_tracks.sort(key=lambda t: t.track_num)

        print(f"[Library] Scanned {len(self.tracks)} tracks, "
              f"{len(self._artists)} artists, {len(self._albums)} albums")

    def _extract_metadata(self, filepath):
        """Extract metadata from a single file using mutagen."""
        try:
            audio = MutagenFile(filepath, easy=True)
            if audio is None:
                return Track(filepath)

            title = _first(audio.get("title"))
            artist = _first(audio.get("artist"))
            album = _first(audio.get("album"))
            genre = _first(audio.get("genre"))
            track_num = 0
            try:
                tn = _first(audio.get("tracknumber", ["0"]))
                track_num = int(tn.split("/")[0]) if tn else 0
            except (ValueError, IndexError):
                pass

            duration = 0.0
            if audio.info:
                duration = audio.info.length

            # Get album art (need to reopen without easy=True)
            art_data = self._extract_album_art(filepath)

            return Track(
                filepath=filepath,
                title=title,
                artist=artist,
                album=album,
                duration=duration,
                track_num=track_num,
                genre=genre,
                album_art_data=art_data,
            )
        except Exception as e:
            print(f"[Library] Error reading {filepath}: {e}")
            return Track(filepath)

    def _extract_album_art(self, filepath):
        """Extract album art bytes from an audio file."""
        try:
            audio = MutagenFile(filepath)
            if audio is None:
                return None

            # MP3 with ID3 tags
            if hasattr(audio, "tags") and audio.tags:
                for key in audio.tags:
                    if key.startswith("APIC"):
                        return audio.tags[key].data

            # FLAC
            if hasattr(audio, "pictures") and audio.pictures:
                return audio.pictures[0].data

            # MP4/M4A
            if hasattr(audio, "tags") and audio.tags and "covr" in audio.tags:
                covers = audio.tags["covr"]
                if covers:
                    return bytes(covers[0])

        except Exception:
            pass
        return None

    # ── Getters ─────────────────────────────────────────────────────
    @property
    def artists(self):
        return sorted(self._artists.keys())

    @property
    def albums(self):
        return sorted(self._albums.keys())

    @property
    def genres(self):
        return sorted(self._genres.keys())

    def get_tracks_by_artist(self, artist):
        return self._artists.get(artist, [])

    def get_tracks_by_album(self, album):
        return self._albums.get(album, [])

    def get_tracks_by_genre(self, genre):
        return self._genres.get(genre, [])

    def get_albums_by_artist(self, artist):
        """Return list of unique albums for an artist."""
        tracks = self._artists.get(artist, [])
        albums = []
        seen = set()
        for t in tracks:
            if t.album not in seen:
                seen.add(t.album)
                albums.append(t.album)
        return sorted(albums)

    def get_all_tracks_sorted(self):
        """Return all tracks sorted by artist, then album, then track num."""
        return sorted(
            self.tracks,
            key=lambda t: (t.artist.lower(), t.album.lower(), t.track_num)
        )

    # ── Cache ───────────────────────────────────────────────────────
    def save_cache(self):
        """Save library index to JSON (without album art)."""
        data = [t.to_dict() for t in self.tracks]
        try:
            with open(config.LIBRARY_CACHE_FILE, "w") as f:
                json.dump(data, f, indent=2)
            print(f"[Library] Cache saved: {len(data)} tracks")
        except Exception as e:
            print(f"[Library] Cache save error: {e}")

    def load_cache(self):
        """Load library from cache. Returns True if loaded successfully."""
        if not os.path.exists(config.LIBRARY_CACHE_FILE):
            return False
        try:
            with open(config.LIBRARY_CACHE_FILE, "r") as f:
                data = json.load(f)
            self.tracks = [Track.from_dict(d) for d in data]
            # Rebuild indices
            self._artists.clear()
            self._albums.clear()
            self._genres.clear()
            for track in self.tracks:
                self._artists.setdefault(track.artist, []).append(track)
                self._albums.setdefault(track.album, []).append(track)
                self._genres.setdefault(track.genre, []).append(track)
            print(f"[Library] Loaded {len(self.tracks)} tracks from cache")
            return True
        except Exception as e:
            print(f"[Library] Cache load error: {e}")
            return False


def _first(val):
    """Get first element if list, else return val."""
    if isinstance(val, (list, tuple)):
        return val[0] if val else None
    return val
