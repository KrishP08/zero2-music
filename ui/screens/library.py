"""
Library Browser Screen — browse by Artists, Albums, or Songs.
Supports hierarchical navigation: Artists → Albums → Songs.
"""

from ui.screen_manager import Screen
from ui.theme import Colors, Fonts, draw_gradient_bg_cached, render_text
from ui.widgets import StatusBar, ScrollList
from hardware.input_handler import InputAction
import config


class LibraryScreen(Screen):
    """
    Hierarchical music library browser.
    mode: "songs", "artists", "albums", "artist_albums", "album_songs"
    """

    def __init__(self, app, mode="songs", filter_key=None):
        super().__init__(app)
        self.mode = mode
        self.filter_key = filter_key  # e.g. artist name or album name
        self.status_bar = StatusBar()
        self.scroll_list = None
        self._tracks = []

    def on_enter(self):
        self._build_list()

    def _build_list(self):
        """Build the list items based on current mode."""
        library = self.app.library
        items = []

        if self.mode == "songs":
            self._tracks = library.get_all_tracks_sorted()
            for t in self._tracks:
                items.append({
                    "label": t.display_title,
                    "subtitle": f"{t.display_artist} · {t.duration_str}",
                    "track": t,
                })
            header = f"All Songs ({len(self._tracks)})"

        elif self.mode == "artists":
            for artist in library.artists:
                count = len(library.get_tracks_by_artist(artist))
                items.append({
                    "label": artist,
                    "subtitle": f"{count} track{'s' if count != 1 else ''}",
                    "key": artist,
                })
            header = f"Artists ({len(items)})"

        elif self.mode == "albums":
            for album in library.albums:
                tracks = library.get_tracks_by_album(album)
                artist = tracks[0].display_artist if tracks else "Unknown"
                items.append({
                    "label": album,
                    "subtitle": f"{artist} · {len(tracks)} tracks",
                    "key": album,
                })
            header = f"Albums ({len(items)})"

        elif self.mode == "artist_albums":
            albums = library.get_albums_by_artist(self.filter_key)
            for album in albums:
                count = len(library.get_tracks_by_album(album))
                items.append({
                    "label": album,
                    "subtitle": f"{count} tracks",
                    "key": album,
                })
            header = self.filter_key

        elif self.mode == "album_songs":
            self._tracks = library.get_tracks_by_album(self.filter_key)
            for t in self._tracks:
                num = f"{t.track_num}. " if t.track_num else ""
                items.append({
                    "label": f"{num}{t.display_title}",
                    "subtitle": t.duration_str,
                    "track": t,
                })
            header = self.filter_key

        else:
            header = "Library"

        if not items:
            items = [{"label": "No music found", "subtitle": "Add files to ~/Music"}]

        self.scroll_list = ScrollList(items, header=header)

    def handle_input(self, action):
        if action == InputAction.SCROLL_UP:
            self.scroll_list.scroll_up()
        elif action == InputAction.SCROLL_DOWN:
            self.scroll_list.scroll_down()
        elif action == InputAction.SELECT:
            self._select_item()
        elif action == InputAction.BACK:
            self.app.screen_manager.pop()
        elif action == InputAction.PLAY_PAUSE:
            self.app.audio.toggle_pause()

    def _select_item(self):
        item = self.scroll_list.selected_item
        if not item:
            return

        if self.mode == "artists":
            # Drill into artist's albums
            screen = LibraryScreen(
                self.app, mode="artist_albums", filter_key=item["key"]
            )
            self.app.screen_manager.push(screen)

        elif self.mode == "albums":
            # Drill into album's songs
            screen = LibraryScreen(
                self.app, mode="album_songs", filter_key=item["key"]
            )
            self.app.screen_manager.push(screen)

        elif self.mode == "artist_albums":
            screen = LibraryScreen(
                self.app, mode="album_songs", filter_key=item["key"]
            )
            self.app.screen_manager.push(screen)

        elif self.mode in ("songs", "album_songs"):
            # Play the selected track and set up queue
            track = item.get("track")
            if track:
                idx = self.scroll_list.selected_index
                self.app.playlist.set_tracks(self._tracks, start_index=idx)
                self.app.audio.play(track.filepath)

                from ui.screens.now_playing import NowPlayingScreen
                screen = NowPlayingScreen(self.app)
                self.app.screen_manager.push(screen)

    def update(self, dt):
        if self.scroll_list:
            self.scroll_list.update(dt)

    def render(self, surface, x_offset=0):
        draw_gradient_bg_cached(surface)
        self.status_bar.render(surface, x_offset)
        if self.scroll_list:
            self.scroll_list.render(surface, x_offset)
