import os
import asyncio
from ignis.dbus import DBusProxy
from gi.repository import GLib  # type: ignore
from ignis.gobject import IgnisGObject, IgnisProperty, IgnisSignal
from ignis import utils
from ignis.connection_manager import ConnectionManager
from collections.abc import Callable
from .constants import ART_URL_CACHE_DIR
from .util import uri_to_unix_path


class MprisPlayer(IgnisGObject):
    """
    A media player object.
    """

    def __init__(self, mpris_proxy: DBusProxy, player_proxy: DBusProxy):
        super().__init__()

        self.__mpris_proxy = mpris_proxy
        self.__player_proxy = player_proxy
        self._conn_mgr = ConnectionManager()

        self._can_control: bool = False
        self._can_go_next: bool = False
        self._can_go_previous: bool = False
        self._can_pause: bool = False
        self._can_play: bool = False
        self._can_seek: bool = False
        self._loop_status: str | None = None
        self._metadata: dict = {}
        self._playback_status: str | None = None
        self._position: int = -1
        self._shuffle: bool = False
        self._volume: int = -1
        self._identity: str | None = None
        self._desktop_entry: str | None = None

        # depend on metadata
        self._track_id: str | None = None
        self._length: int = -1
        self._art_url: str | None = None
        self._album: str | None = None
        self._artist: str | None = None
        self._title: str | None = None
        self._url: str | None = None

        self._previous_art_url: str | None = None

        os.makedirs(ART_URL_CACHE_DIR, exist_ok=True)

        self.__mpris_proxy.watch_name(on_name_vanished=lambda *_: self.__close())

        self._conn_mgr.connect(
            self.__player_proxy.gproxy,
            "g-properties-changed",
            lambda *_: asyncio.create_task(self.__sync_all()),
        )
        self._conn_mgr.connect(
            self,
            "notify::metadata",
            lambda *_: asyncio.create_task(self.__sync_metadata()),
        )

    @classmethod
    async def new_async(cls, name: str) -> "MprisPlayer":
        mpris_proxy = await DBusProxy.new_async(
            name=name,
            object_path="/org/mpris/MediaPlayer2",
            interface_name="org.mpris.MediaPlayer2",
            info=utils.load_interface_xml("org.mpris.MediaPlayer2"),
        )

        player_proxy = await DBusProxy.new_async(
            name=name,
            object_path="/org/mpris/MediaPlayer2",
            interface_name="org.mpris.MediaPlayer2.Player",
            info=utils.load_interface_xml("org.mpris.MediaPlayer2.Player"),
        )

        obj = cls(mpris_proxy=mpris_proxy, player_proxy=player_proxy)
        await obj._initial_sync()
        return obj

    async def _initial_sync(self) -> None:
        self._sync_pos_task = asyncio.create_task(self.__sync_position())
        await self.__sync_all()
        await self.__sync_metadata()
        await self.__update_position()

    def __close(self) -> None:
        self.__mpris_proxy.unwatch_name()
        self._conn_mgr.disconnect_all()
        self._sync_pos_task.cancel()
        self.emit("closed")

    async def __sync_property(self, proxy: DBusProxy, py_name: str) -> None:
        try:
            value = await proxy.get_dbus_property_async(utils.snake_to_pascal(py_name))
        except GLib.Error:
            return

        if value == getattr(self, f"_{py_name}"):
            return

        setattr(self, f"_{py_name}", value)
        self.notify(py_name.replace("_", "-"))

    async def __sync_all(self) -> None:
        for prop_name in (
            "can_control",
            "can_go_next",
            "can_go_previous",
            "can_pause",
            "can_play",
            "can_seek",
            "loop_status",
            "metadata",
            "playback_status",
            "shuffle",
            "volume",
        ):
            await self.__sync_property(self.__player_proxy, prop_name)

        for prop_name in (
            "identity",
            "desktop_entry",
        ):
            await self.__sync_property(self.__mpris_proxy, prop_name)

    def __sync_metadata_property(
        self, key: str, py_name: str, custom_func: Callable | None = None
    ) -> None:
        prop = self.metadata.get(key, None)
        private_name = f"_{py_name}"
        if prop != getattr(self, private_name):
            if custom_func:
                setattr(self, private_name, custom_func(prop))
            else:
                setattr(self, private_name, prop)
            self.notify(py_name.replace("_", "-"))

    async def __sync_metadata(self) -> None:
        # sync all properties that depend on metadata
        self.__sync_metadata_property("mpris:trackid", "track_id")
        self.__sync_metadata_property(
            "mpris:length",
            "length",
            lambda length: length // 1_000_000 if length else -1,
        )
        self.__sync_metadata_property("xesam:album", "album")
        self.__sync_metadata_property(
            "xesam:artist",
            "artist",
            lambda artist: "".join(artist) if isinstance(artist, list) else artist,
        )
        self.__sync_metadata_property("xesam:title", "title")
        self.__sync_metadata_property("xesam:url", "url")
        await self.__cache_art_url()

    async def __cache_art_url(self) -> None:
        art_url = self.metadata.get("mpris:artUrl", None)
        result = None

        if art_url == self._previous_art_url:
            return

        self._previous_art_url = art_url

        if art_url:
            result = await self.__load_art_url(art_url)

        self._art_url = result
        self.notify("art_url")

    async def __load_art_url(self, art_url: str) -> str:
        path = ART_URL_CACHE_DIR + "/" + uri_to_unix_path(art_url)
        if os.path.exists(path):
            return path

        contents = await utils.read_file_async(uri=art_url, decode=False)
        await utils.write_file_async(path=path, contents=contents)
        return path

    async def __update_position(self) -> None:
        try:
            position = await self.__player_proxy.get_dbus_property_async("Position")
        except GLib.Error:
            return
        if position:
            self._position = position // 1_000_000
            self.notify("position")

    async def __sync_position(self) -> None:
        while True:
            if self.playback_status != "Paused":
                await self.__update_position()
            await asyncio.sleep(1)

    @IgnisSignal
    def ready(self): ...  # user shouldn't connect to this signal

    @IgnisSignal
    def closed(self):
        """
        Emitted when a player has been closed or removed.
        """

    @IgnisProperty
    def can_control(self) -> bool:
        """
        Whether the player can be controlled.
        """
        return self._can_control

    @IgnisProperty
    def can_go_next(self) -> bool:
        """
        Whether the player can go to the next track.
        """
        return self._can_go_next

    @IgnisProperty
    def can_go_previous(self) -> bool:
        """
        Whether the player can go to the previous track.
        """
        return self._can_go_previous

    @IgnisProperty
    def can_pause(self) -> bool:
        """
        Whether the player can pause.
        """
        return self._can_pause

    @IgnisProperty
    def can_play(self) -> bool:
        """
        Whether the player can play.
        """
        return self._can_play

    @IgnisProperty
    def can_seek(self) -> bool:
        """
        Whether the player can seek (change position on track in seconds).
        """
        return self._can_seek

    @IgnisProperty
    def loop_status(self) -> str | None:
        """
        The current loop status.
        """
        return self._loop_status

    @IgnisProperty
    def metadata(self) -> dict:
        """
        A dictionary containing metadata.
        """
        return self._metadata

    @IgnisProperty
    def track_id(self) -> str | None:
        """
        The ID of the current track.
        """
        return self._track_id

    @IgnisProperty
    def length(self) -> int:
        """
        The length of the current track,
        ``-1`` if not supported by the player.
        """
        return self._length

    @IgnisProperty
    def art_url(self) -> str | None:
        """
        The path to the cached art image of the track.
        """
        return self._art_url

    @IgnisProperty
    def album(self) -> str | None:
        """
        The current album name.
        """
        return self._album

    @IgnisProperty
    def artist(self) -> str | None:
        """
        The current artist name.
        """
        return self._artist

    @IgnisProperty
    def title(self) -> str | None:
        """
        The current title of the track.
        """
        return self._title

    @IgnisProperty
    def url(self) -> str | None:
        """
        The URL address of the track.
        """
        return self._url

    @IgnisProperty
    def playback_status(self) -> str | None:
        """
        The current playback status. Can be "Playing" or "Paused".
        """
        return self._playback_status

    @IgnisProperty
    def position(self) -> int:
        """
        The current position in the track in seconds.
        """
        return self._position

    @position.setter
    def position(self, value: int) -> None:
        self.__player_proxy.SetPosition("(ox)", self.track_id, value * 1_000_000)
        asyncio.create_task(self.__update_position())

    async def set_position_async(self, value: int) -> None:
        """
        Asynchronously set position.

        Args:
            value: The value to set.
        """
        await self.__player_proxy.SetPositionAsync(
            "(ox)", self.track_id, value * 1_000_000
        )
        await self.__update_position()

    @IgnisProperty
    def shuffle(self) -> bool:
        """
        The shuffle status.
        """
        return self._shuffle

    @IgnisProperty
    def volume(self) -> float:
        """
        The volume of the player.
        """
        return self._volume

    @IgnisProperty
    def identity(self) -> str | None:
        """
        The name of the player (e.g. "Spotify", "firefox").
        """
        return self._identity

    @IgnisProperty
    def desktop_entry(self) -> str | None:
        """
        The .desktop file of the player.
        """
        return self._desktop_entry

    def next(self) -> None:
        """
        Go to the next track.
        """
        self.__player_proxy.Next()

    async def next_async(self) -> None:
        """
        Asynchronous version of :func:`next`.
        """
        await self.__player_proxy.NextAsync()

    def previous(self) -> None:
        """
        Go to the previous track.
        """
        self.__player_proxy.Previous()

    async def previous_async(self) -> None:
        """
        Asynchronous version of :func:`previous`.
        """
        await self.__player_proxy.PreviousAsync()

    def pause(self) -> None:
        """
        Pause playback.
        """
        self.__player_proxy.Pause()

    async def pause_async(self) -> None:
        """
        Asynchronous version of :func:`pause`.
        """
        await self.__player_proxy.PauseAsync()

    def play(self) -> None:
        """
        Start playback.
        """
        self.__player_proxy.Play()

    async def play_async(self) -> None:
        """
        Asynchronous version of :func:`play`.
        """
        await self.__player_proxy.PlayAsync()

    def play_pause(self) -> None:
        """
        Toggle between playing and pausing.
        """
        self.__player_proxy.PlayPause()

    async def play_pause_async(self) -> None:
        """
        Asynchronous version of :func:`play_pause`.
        """
        await self.__player_proxy.PlayPauseAsync()

    def stop(self) -> None:
        """
        Stop playback and remove the MPRIS interface if supported by the player.
        """
        self.__player_proxy.Stop()

    async def stop_async(self) -> None:
        """
        Asynchronous version of :func:`stop`.
        """
        await self.__player_proxy.StopAsync()

    def seek(self, offset: int) -> None:
        """
        Seek to a specific position in the track.
        Positive values move forward, and negative values move backward.
        The offset is in milliseconds.
        """
        self.__player_proxy.Seek("(x)", offset * 1_000_100)

    async def seek_async(self, offset: int) -> None:
        """
        Asynchronous version of :func:`seek`.
        """
        await self.__player_proxy.SeekAsync("(x)", offset * 1_000_100)
