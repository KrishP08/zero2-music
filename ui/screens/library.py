"""
Library Browser — Tack UI landscape file browser.
Browse by Artists, Albums, or Songs with folder/file grouping.
"""

import os
import pygame
from ui.screen_manager import Screen
from ui.theme import Colors, Fonts, draw_gradient_bg_cached, render_text, draw_rounded_rect, load_icon, tint_icon
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
        self.sort_mode = "name"
        self._thumbnails = {}
        
        self._icons = {
            "music": load_icon("music", size=(16, 16)),
            "artist": load_icon("artist", size=(16, 16)),
            "album": load_icon("album", size=(16, 16)),
        }

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
            
            if self.sort_mode == "date":
                self._tracks.sort(key=lambda t: os.path.getmtime(t.filepath) if os.path.exists(t.filepath) else 0, reverse=True)
            else:
                self._tracks.sort(key=lambda t: t.display_title.lower())
                
            items.append({
                "label": f"CURRENT SORT: {self.sort_mode.upper()}",
                "subtitle": "Click to toggle order",
                "action": "toggle_sort",
                "is_action": True,
            })
            
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
                tracks = library.get_tracks_by_artist(artist)
                count = len(tracks)
                items.append({
                    "label": artist,
                    "subtitle": f"{count} track{'s' if count != 1 else ''}",
                    "key": artist,
                    "is_folder": True,
                    "track": tracks[0] if tracks else None
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
                    "track": tracks[0] if tracks else None
                })
            header = f"Albums ({len(items)})"

        elif self.mode == "artist_albums":
            albums = library.get_albums_by_artist(self.filter_key)
            for album in albums:
                tracks = library.get_tracks_by_album(album)
                count = len(tracks)
                items.append({
                    "label": album,
                    "subtitle": f"{count} tracks",
                    "key": album,
                    "is_folder": True,
                    "track": tracks[0] if tracks else None
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

        is_retro = getattr(config, "THEME", "modern") == "retro"
        
        self.scroll_list = ScrollList(
            items, header=header if not is_retro else None,
            item_renderer=self._render_retro_item if is_retro else self._render_item,
            bottom_margin=BottomNavBar.HEIGHT,
        )
        if is_retro:
            self.scroll_list._top_offset = 48

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
            
        action = item.get("action")
        if action == "toggle_sort":
            self.sort_mode = "date" if self.sort_mode == "name" else "name"
            idx = self.scroll_list.selected_index
            self._build_list()
            self.scroll_list.selected_index = idx
            return

        if self.mode == "artists":
            screen = LibraryScreen(self.app, mode="artist_albums", filter_key=item.get("key"))
            self.app.screen_manager.push(screen)
        elif self.mode == "albums":
            screen = LibraryScreen(self.app, mode="album_songs", filter_key=item.get("key"))
            self.app.screen_manager.push(screen)
        elif self.mode == "artist_albums":
            screen = LibraryScreen(self.app, mode="album_songs", filter_key=item.get("key"))
            self.app.screen_manager.push(screen)
        elif self.mode in ("songs", "album_songs"):
            track = item.get("track")
            if track:
                if track in self._tracks:
                    idx = self._tracks.index(track)
                    self.app.playlist.set_tracks(self._tracks, start_index=idx)
                    self.app.audio.play(track.filepath)
                    from ui.screens.now_playing import NowPlayingScreen
                    screen = NowPlayingScreen(self.app)
                    self.app.screen_manager.push(screen)

    def update(self, dt):
        if self.scroll_list:
            self.scroll_list.update(dt)

    def render(self, surface, x_offset=0):
        is_retro = getattr(config, "THEME", "modern") == "retro"
        
        if is_retro:
            surface.fill(Colors.RETRO_BG_DARK)
            self.status_bar.render(surface, x_offset, title="MUSIC EXPLORER")
            
            # Retro Sorting Tabs
            tab_y = 24 # Adjusted from 20 to 24 to account for status bar height
            pygame.draw.rect(surface, (*Colors.RETRO_PRIMARY[:3], 10), (x_offset, tab_y, config.SCREEN_WIDTH, 28))
            pygame.draw.rect(surface, (*Colors.RETRO_PRIMARY[:3], 40), (x_offset, tab_y+27, config.SCREEN_WIDTH, 1))
            
            is_name_sort = self.sort_mode == "name"
            # Tab 1: Name
            pygame.draw.rect(surface, (*Colors.RETRO_PRIMARY[:3], 40) if is_name_sort else (0,0,0,0), (x_offset, tab_y, 100, 28))
            pygame.draw.rect(surface, Colors.RETRO_PRIMARY if is_name_sort else Colors.TRANSPARENT, (x_offset, tab_y+26, 100, 2))
            render_text(surface, "NAME", (x_offset + 32, tab_y + 6), font=Fonts.tiny(bold=True), color=Colors.RETRO_PRIMARY if is_name_sort else (*Colors.RETRO_PRIMARY[:3], 150))
            
            # Tab 2: Date
            is_date_sort = not is_name_sort
            pygame.draw.rect(surface, (*Colors.RETRO_PRIMARY[:3], 40) if is_date_sort else (0,0,0,0), (x_offset + 100, tab_y, 100, 28))
            pygame.draw.rect(surface, Colors.RETRO_PRIMARY if is_date_sort else Colors.TRANSPARENT, (x_offset + 100, tab_y+26, 100, 2))
            render_text(surface, "DATE", (x_offset + 132, tab_y + 6), font=Fonts.tiny(bold=True), color=Colors.RETRO_PRIMARY if is_date_sort else (*Colors.RETRO_PRIMARY[:3], 150))
            
            if self.scroll_list:
                self.scroll_list.render(surface, x_offset)
                
            self.bottom_nav.render(surface, x_offset)

        else:
            draw_gradient_bg_cached(surface)
            self.status_bar.render(surface, x_offset, title="MUSIC EXPLORER")
            if self.scroll_list:
                self.scroll_list.render(surface, x_offset)
            self.bottom_nav.render(surface, x_offset)

    def _render_retro_item(self, surface, item, rect, selected, x_offset):
        x, y, w, h = rect
        label = item.get("label", "")
        subtitle = item.get("subtitle", "")
        is_folder = item.get("is_folder", False)
        is_action = item.get("is_action", False)
        
        icon_size = 28
        icon_x = x + 8
        icon_y = y + (h - icon_size) // 2
        
        if selected:
            # Active Row BG
            pygame.draw.rect(surface, (80, 50, 20), (x, y, w, h))
            pygame.draw.rect(surface, Colors.RETRO_PRIMARY, (x, y+h-1, w, 1))
        else:
            pygame.draw.rect(surface, (80, 50, 20), (x, y+h-1, w, 1))
            
        # Check for music thumbnail
        track = item.get("track")
        thumb = self._get_thumbnail(track) if track else None

        if selected:
            pygame.draw.circle(surface, (*Colors.RETRO_PRIMARY[:3], 60), (icon_x + 14, icon_y + 14), 14)
            pygame.draw.circle(surface, Colors.RETRO_PRIMARY, (icon_x + 14, icon_y + 14), 14, 1)
            char = "»" if not is_folder else "📁"
            if not thumb:
                render_text(surface, char, (icon_x + 10, icon_y + 4), font=Fonts.body(), color=Colors.RETRO_PRIMARY)
        else:
            draw_rounded_rect(surface, (40, 30, 15), (icon_x, icon_y, icon_size, icon_size), radius=6)
            pygame.draw.rect(surface, (120, 80, 30), (icon_x, icon_y, icon_size, icon_size), 1, border_radius=6)
            char = "»" if not is_folder else "📁"
            if is_action: char = "↕"
            if not thumb:
                render_text(surface, char, (icon_x + 10, icon_y + 4), font=Fonts.body(), color=Colors.RETRO_PRIMARY)
                
        if thumb:
            surface.blit(thumb, (icon_x, icon_y))
            pygame.draw.rect(surface, Colors.RETRO_PRIMARY if selected else (120, 80, 30), (icon_x, icon_y, icon_size, icon_size), 1, border_radius=5)

        text_x = icon_x + icon_size + 12
        text_color = Colors.RETRO_PRIMARY if selected else (240, 240, 240)
        sub_color = (180, 120, 60) if selected else (150, 150, 150)
        
        render_text(surface, label[:24].upper(), (text_x, y + 6), font=Fonts.tiny(bold=True), color=text_color)
        if subtitle:
            render_text(surface, subtitle[:28].upper(), (text_x, y + 20), font=Fonts.tiny(), color=sub_color)
            
        # Right action icon
        right_char = ">>" if not is_folder else "›"
        if selected: right_char = "[›]"
        render_text(surface, right_char, (x + w - 30, y + 10), font=Fonts.tiny(bold=True), color=Colors.RETRO_PRIMARY)

    def _render_item(self, surface, item, rect, selected, x_offset):
        x, y, w, h = rect
        label = item.get("label", "")
        subtitle = item.get("subtitle", "")
        badge = item.get("badge", "")
        is_folder = item.get("is_folder", False)
        is_action = item.get("is_action", False)

        # Icon square
        icon_size = 28
        icon_x = x + 8
        icon_y = y + (h - icon_size) // 2

        if is_folder or is_action:
            bg_color = (*Colors.ACCENT[:3], 40)
        else:
            bg_color = (*Colors.BG_CARD[:3], 200)

        draw_rounded_rect(surface, bg_color,
                          (icon_x, icon_y, icon_size, icon_size), radius=5)

        # Icon
        if is_action:
            render_text(surface, "↕", (icon_x + 8, icon_y + 4),
                        font=Fonts.body(), color=Colors.ACCENT)
        else:
            # Check for music thumbnail
            track = item.get("track")
            thumb = self._get_thumbnail(track) if track else None
            
            if thumb:
                surface.blit(thumb, (icon_x, icon_y))
            else:
                # Determine which png to use
                if is_folder and self.mode == "artists":
                    icon_name = "artist"
                elif is_folder and self.mode in ("albums", "artist_albums"):
                    icon_name = "album"
                else:
                    icon_name = "music"
                
                icon_surf = self._icons.get(icon_name)
                if icon_surf:
                    color = Colors.ACCENT if is_folder else Colors.TEXT_MUTED
                    tinted = tint_icon(icon_surf, color)
                    surface.blit(tinted, (icon_x + 6, icon_y + 6))
                else:
                    # Fallback
                    char = "📁" if is_folder else "♪"
                    color = Colors.ACCENT if is_folder else Colors.TEXT_MUTED
                    render_text(surface, char, (icon_x + (4 if is_folder else 7), icon_y + 4),
                                font=Fonts.body(), color=color)

        # Text
        text_x = icon_x + icon_size + 8
        text_w = w - text_x - 10
        if badge:
            text_w -= 32

        render_text(surface, label,
                    (text_x, y + 4 + (4 if not subtitle else 0)),
                    font=Fonts.body(), color=Colors.TEXT_PRIMARY,
                    max_width=text_w)

        if subtitle:
            render_text(surface, subtitle,
                        (text_x, y + 22),
                        font=Fonts.small(), color=Colors.TEXT_SECONDARY,
                        max_width=text_w)

        # Format Badge
        if badge:
            badge_w = 26
            badge_h = 14
            badge_x = x + w - badge_w - 6
            badge_y = y + (h - badge_h) // 2
            draw_rounded_rect(surface, (*Colors.ACCENT[:3], 30),
                              (badge_x, badge_y, badge_w, badge_h), radius=3)
            render_text(surface, badge[:4],
                        (badge_x + 2, badge_y + 1),
                        font=Fonts.tiny(), color=Colors.ACCENT)

        # Chevron for folders
        if is_folder and selected:
            render_text(surface, "›", (x + w - 14, y + (h - 14) // 2),
                        font=Fonts.body(), color=Colors.ACCENT)

    def _get_thumbnail(self, track):
        if not track:
            return None
            
        if track.filepath not in self._thumbnails:
            self._thumbnails[track.filepath] = "LOADING"
            
            def load_thumb():
                art_bytes = track.get_album_art_bytes()
                if art_bytes:
                    try:
                        import pygame
                        from io import BytesIO
                        img = pygame.image.load(BytesIO(art_bytes))
                        thumb = pygame.transform.smoothscale(img, (28, 28))
                        
                        # Apply rounded mask
                        mask = pygame.Surface((28, 28), pygame.SRCALPHA)
                        pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, 28, 28), border_radius=5)
                        thumb_masked = thumb.convert_alpha()
                        thumb_masked.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
                        
                        self._thumbnails[track.filepath] = thumb_masked
                    except Exception:
                        self._thumbnails[track.filepath] = None
                else:
                    self._thumbnails[track.filepath] = None
                    
            import threading
            threading.Thread(target=load_thumb, daemon=True).start()
            
        val = self._thumbnails.get(track.filepath)
        return val if val != "LOADING" else None
