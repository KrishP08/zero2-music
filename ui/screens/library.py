"""
Library Browser — Tack UI landscape file browser.
Browse by Artists, Albums, or Songs with folder/file grouping.
"""

import os
from ui.screen_manager import Screen
from ui.theme import Colors, Fonts, draw_gradient_bg_cached, render_text, draw_rounded_rect
from ui.widgets import StatusBar, BottomNavBar, ScrollList
from hardware.input_handler import InputAction
import config


class LibraryScreen(Screen):
    """Hierarchical music library browser with Tack UI styling."""

    def __init__(self, app, mode="songs", filter_key=None):
        super().__init__(app)
        self.mode = mode
        self.filter_key = filter_key
        self.status_bar = StatusBar()
        self.bottom_nav = BottomNavBar()
        self.bottom_nav.active_tab = 1  # Files tab
        self.scroll_list = None
        self._tracks = []

    def on_enter(self):
        if self.scroll_list is None:
            self._build_list()

    def on_resume(self):
        # Don't rebuild — preserve scroll position
        pass

    def _build_list(self):
        library = self.app.library
        items = []

        if self.mode == "songs":
            self._tracks = library.get_all_tracks_sorted()
            for t in self._tracks:
                ext = os.path.splitext(t.filepath)[1].upper().replace(".", "")
                items.append({
                    "label": t.display_title,
                    "subtitle": t.display_artist,
                    "badge": ext,
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
                    "is_folder": True,
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
                    "is_folder": True,
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
                    "is_folder": True,
                })
            header = self.filter_key

        elif self.mode == "album_songs":
            self._tracks = library.get_tracks_by_album(self.filter_key)
            for t in self._tracks:
                num = f"{t.track_num}. " if t.track_num else ""
                ext = os.path.splitext(t.filepath)[1].upper().replace(".", "")
                items.append({
                    "label": f"{num}{t.display_title}",
                    "subtitle": t.duration_str,
                    "badge": ext,
                    "track": t,
                })
            header = self.filter_key
        else:
            header = "Library"

        if not items:
            items = [{"label": "No music found", "subtitle": "Add files to ~/Music"}]

        self.scroll_list = ScrollList(
            items, header=header,
            item_renderer=self._render_item,
            bottom_margin=BottomNavBar.HEIGHT,
        )

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
            screen = LibraryScreen(self.app, mode="artist_albums", filter_key=item["key"])
            self.app.screen_manager.push(screen)
        elif self.mode == "albums":
            screen = LibraryScreen(self.app, mode="album_songs", filter_key=item["key"])
            self.app.screen_manager.push(screen)
        elif self.mode == "artist_albums":
            screen = LibraryScreen(self.app, mode="album_songs", filter_key=item["key"])
            self.app.screen_manager.push(screen)
        elif self.mode in ("songs", "album_songs"):
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
        self.status_bar.render(surface, x_offset, title="MUSIC EXPLORER")
        if self.scroll_list:
            self.scroll_list.render(surface, x_offset)
        self.bottom_nav.render(surface, x_offset)

    def _render_item(self, surface, item, rect, selected, x_offset):
        x, y, w, h = rect
        label = item.get("label", "")
        subtitle = item.get("subtitle", "")
        badge = item.get("badge", "")
        is_folder = item.get("is_folder", False)

        # Icon square
        icon_size = 28
        icon_x = x + 8
        icon_y = y + (h - icon_size) // 2

        if is_folder:
            bg_color = (*Colors.ACCENT[:3], 40)
        else:
            bg_color = (*Colors.BG_CARD[:3], 200)

        draw_rounded_rect(surface, bg_color,
                          (icon_x, icon_y, icon_size, icon_size), radius=5)

        # Icon character
        if is_folder:
            render_text(surface, "📁", (icon_x + 4, icon_y + 4),
                        font=Fonts.body(), color=Colors.ACCENT)
        else:
            render_text(surface, "♪", (icon_x + 7, icon_y + 5),
                        font=Fonts.body(), color=Colors.TEXT_MUTED)

        # Text
        text_x = icon_x + icon_size + 8
        label_color = Colors.TEXT_PRIMARY if selected else Colors.TEXT_SECONDARY
        max_w = w - icon_size - 30

        if badge:
            max_w -= 36

        render_text(surface, label, (text_x, y + 4),
                    font=Fonts.body(), color=label_color, max_width=max_w)

        if subtitle:
            # Badge + subtitle
            sub_x = text_x
            if badge:
                badge_color = Colors.BADGE_FLAC if badge in ("FLAC", "WAV") else Colors.BADGE_MP3
                badge_w = Fonts.tiny().size(badge)[0] + 6
                draw_rounded_rect(surface, (*badge_color[:3], 50),
                                  (sub_x, y + 21, badge_w, 12), radius=3)
                render_text(surface, badge, (sub_x + 3, y + 22),
                            font=Fonts.tiny(), color=badge_color)
                sub_x += badge_w + 4

            render_text(surface, subtitle, (sub_x, y + 22),
                        font=Fonts.small(), color=Colors.TEXT_MUTED,
                        max_width=max_w - (sub_x - text_x))

        # Chevron for folders
        if is_folder and selected:
            render_text(surface, "›", (x + w - 14, y + (h - 14) // 2),
                        font=Fonts.body(), color=Colors.ACCENT)
