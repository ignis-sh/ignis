"""
`ignis_mpris` tracks and controls media players on GNU/Linux desktops that implement the
[MPRIS D-Bus Interface Specification](https://specifications.freedesktop.org/mpris/latest/).

[`MprisService`][] watches the session bus for players. Each player is exposed as a
[`Player`][], whose state is kept in sync with the player and exposed as observable
[`Property`][] objects.

# Example
```python
import asyncio
from ignis_mpris import MprisService, Player


def setup_player(player: Player) -> None:
    print("Player:", player.identity.value)
    player.metadata.changed.connect(lambda metadata: print("Now playing:", metadata.title))
    player.removed.connect(lambda _: print("Player closed"))


async def main() -> None:
    service = MprisService()
    await service.run()

    # Players which were already running
    for player in service.players:
        setup_player(player)

    # Players which appear later
    service.player_added.connect(setup_player)

    await asyncio.Event().wait()


asyncio.run(main())
```
"""

from typing import Any, Final, final

@final
class ConnectionHandle:
    """
    A handle returned by [`Event.connect`][], used to disconnect the callback.
    """

@final
class Event:
    """
    An event which invokes connected callbacks when it is emitted.
    """
    def connect(self, /, callback: Any) -> ConnectionHandle:
        """
        Registers a callback to invoke when the event is emitted.
        
        The callback receives the emitted value as its only argument.
        """
    def disconnect(self, /, handle: ConnectionHandle) -> None:
        """
        Unregisters a callback. Disconnecting the same handle twice does nothing.
        """

@final
class LoopStatus:
    """
    The looping behavior of a player.
    """
    None_: Final[LoopStatus]
    """
    The playback will stop when there are no more tracks to play.
    
    Named `None_` because `None` is a reserved keyword in Python.
    """
    Playlist: Final[LoopStatus]
    """
    The playback loops through a list of tracks.
    """
    Track: Final[LoopStatus]
    """
    The current track will start again from the beginning once it has finished playing.
    """
    def __int__(self, /) -> int: ...
    def __repr__(self, /) -> str: ...

@final
class Metadata:
    """
    Metadata of the current track.
    
    Fields are parsed from the
    [MPRIS metadata](https://specifications.freedesktop.org/mpris/latest/Track_List_Interface.html#Mapping:Metadata_Map)
    reported by the player. A field is `None` if the player doesn't provide it.
    """
    @property
    def album(self, /) -> str |None:
        """
        The album name.
        """
    @property
    def album_artist(self, /) -> str |None:
        """
        The album artist(s).
        """
    @property
    def art_url(self, /) -> str |None:
        """
        The location of an image representing the track or album, as a URI.
        
        See also [`Player.cached_cover_art`][], which provides a local copy of the image.
        """
    @property
    def artist(self, /) -> str |None:
        """
        The track artist(s).
        """
    @property
    def as_text(self, /) -> str |None:
        """
        The track lyrics.
        """
    @property
    def audio_bpm(self, /) -> str |None:
        """
        The speed of the music, in beats per minute.
        """
    @property
    def auto_rating(self, /) -> str |None:
        """
        An automatically-generated rating, based on things such as how often it has been played.
        
        It is in the range from 0.0 to 1.0.
        """
    @property
    def comment(self, /) -> str |None:
        """
        A (list of) freeform comment(s).
        """
    @property
    def composer(self, /) -> str |None:
        """
        The composer(s) of the track.
        """
    @property
    def content_created(self, /) -> str |None:
        """
        When the track was created, as an ISO 8601 date.
        """
    @property
    def disc_number(self, /) -> str |None:
        """
        The disc number on the album that this track is from.
        """
    @property
    def first_used(self, /) -> str |None:
        """
        When the track was first played, as an ISO 8601 date.
        """
    @property
    def genre(self, /) -> str |None:
        """
        The genre(s) of the track.
        """
    @property
    def last_used(self, /) -> str |None:
        """
        When the track was last played, as an ISO 8601 date.
        """
    @property
    def length(self, /) -> int |None:
        """
        The duration of the track in microseconds.
        """
    @property
    def lyricist(self, /) -> str |None:
        """
        The lyricist(s) of the track.
        """
    @property
    def title(self, /) -> str |None:
        """
        The track title.
        """
    @property
    def track_id(self, /) -> str |None:
        """
        The unique identifier of the track within the context of the player's track list.
        
        Pass it to [`Player.set_position`][].
        """
    @property
    def track_number(self, /) -> int |None:
        """
        The track number on the album disc.
        """
    @property
    def url(self, /) -> str |None:
        """
        The location of the media file, as a URI.
        """
    @property
    def use_count(self, /) -> int |None:
        """
        The number of times the track has been played.
        """
    @property
    def user_rating(self, /) -> float |None:
        """
        A user-specified rating, in the range from 0.0 to 1.0.
        """

@final
class MprisService:
    """
    A service which tracks media players on the session bus.
    
    A player is any D-Bus client which owns a name starting with `org.mpris.MediaPlayer2`.
    
    Cover arts are cached in `$XDG_CACHE_HOME/ignis-mpris/images`.
    """
    def __new__(cls, /) -> MprisService: ...
    @property
    def player_added(self, /) -> Event:
        """
        Emitted with the new player when a player appears on the bus.
        
        It is not emitted for players that are already running when the service starts. Use
        `players` to get them.
        """
    @property
    def player_removed(self, /) -> Event:
        """
        Emitted with the player when a player disappears from the bus, e.g. when it is closed.
        """
    @property
    def players(self, /) -> list[Player]:
        """
        The currently running players.
        """
    def run(self, /) -> Any:
        """
        Runs the service.
        
        Connects to the session bus, adds players which are already running and starts watching for
        players appearing and disappearing in the background. Must be called only once.
        
        Players that fail to initialize are skipped.
        
        Raises `OSError` if connecting to the session bus fails.
        """

@final
class PlaybackStatus:
    """
    The playback state of a player.
    """
    Paused: Final[PlaybackStatus]
    """
    A track is currently paused.
    """
    Playing: Final[PlaybackStatus]
    """
    A track is currently playing.
    """
    Stopped: Final[PlaybackStatus]
    """
    There is no track currently playing.
    """
    def __int__(self, /) -> int: ...
    def __repr__(self, /) -> str: ...

@final
class Player:
    """
    A media player.
    
    Its properties are [`Property`][] objects which are kept in sync with the player: read the
    current value with `value` and observe changes with `changed`. A property the player doesn't
    provide has a default value (e.g. `False` or an empty string).
    
    ```python
    print(player.volume.value)
    player.volume.changed.connect(lambda volume: print("New volume:", volume))
    ```
    
    Methods return awaitables and raise `OSError` if the D-Bus call fails.
    """
    @property
    def cached_cover_art(self, /) -> Property:
        """
        The path to a local copy of the current track's cover art (`art_url` of `metadata`).
        
        The image is downloaded (`http` and `https` URIs) or copied (`file` URIs) into the cache
        directory. `None` if the cover art can't be cached.
        """
    @property
    def can_control(self, /) -> Property:
        """
        Whether the player can be controlled.
        
        If not, calling any method or setting any property will likely fail.
        """
    @property
    def can_go_next(self, /) -> Property:
        """
        Whether `next` is expected to skip to the next track.
        """
    @property
    def can_go_previous(self, /) -> Property:
        """
        Whether `previous` is expected to skip to the previous track.
        """
    @property
    def can_pause(self, /) -> Property:
        """
        Whether playback can be paused using `pause` or `play_pause`.
        """
    @property
    def can_play(self, /) -> Property:
        """
        Whether playback can be started using `play` or `play_pause`.
        """
    @property
    def can_quit(self, /) -> Property:
        """
        Whether the player can be closed with `quit`.
        """
    @property
    def can_raise(self, /) -> Property:
        """
        Whether the player can be brought to the front with `raise`.
        """
    @property
    def can_seek(self, /) -> Property:
        """
        Whether the position can be changed using `seek` and `set_position`.
        """
    @property
    def can_set_fullscreen(self, /) -> Property:
        """
        Whether the player's fullscreen state can be changed.
        """
    @property
    def desktop_entry(self, /) -> Property:
        """
        The basename of the player's desktop entry, e.g. `"vlc"` for `vlc.desktop`.
        
        Empty if the player doesn't provide it.
        """
    @property
    def fullscreen(self, /) -> Property:
        """
        Whether the player is occupying the fullscreen.
        """
    @property
    def has_track_list(self, /) -> Property:
        """
        Whether the player has a track list.
        """
    @property
    def identity(self, /) -> Property:
        """
        A friendly name to identify the player to users, e.g. `"VLC media player"`.
        """
    @property
    def loop_status(self, /) -> Property:
        """
        The current loop status. Change it with `set_loop_status`.
        """
    @property
    def maximum_rate(self, /) -> Property:
        """
        The maximum value which `rate` can take.
        """
    @property
    def metadata(self, /) -> Property:
        """
        The metadata of the current track.
        """
    @property
    def minimum_rate(self, /) -> Property:
        """
        The minimum value which `rate` can take.
        """
    def next(self, /) -> Any:
        """
        Skips to the next track in the tracklist.
        
        If there is no next track (and endless playback and track repeat are both off), stops
        playback. See [`can_go_next`][].
        """
    def open_uri(self, /, uri: str) -> Any:
        """
        Opens the URI and starts playing it.
        
        The URI scheme should be one of [`supported_uri_schemes`][] and the media type should be one
        of [`supported_mime_types`][].
        """
    def pause(self, /) -> Any:
        """
        Pauses playback.
        
        If playback is already paused, this has no effect. See [`can_pause`][].
        """
    def play(self, /) -> Any:
        """
        Starts or resumes playback.
        
        If already playing, this has no effect. See [`can_play`][].
        """
    def play_pause(self, /) -> Any:
        """
        Pauses playback if it's playing, otherwise starts or resumes it.
        """
    @property
    def playback_status(self, /) -> Property:
        """
        The current playback status.
        """
    @property
    def position(self, /) -> Property:
        """
        The current track position in microseconds.
        
        The position is computed locally from the last position reported by the player, the
        playback status and the rate. Its `changed` event is emitted every 200 milliseconds.
        """
    def previous(self, /) -> Any:
        """
        Skips to the previous track in the tracklist.
        
        If there is no previous track (and endless playback and track repeat are both off), stops
        playback. See [`can_go_previous`][].
        """
    def quit(self, /) -> Any:
        """
        Asks the player to quit.
        
        The player may ignore this. See [`can_quit`][].
        """
    def raise_(self, /) -> Any:
        """
        Asks the player to bring its user interface to the front.
        
        The player may ignore this. See [`can_raise`][].
        
        Named `raise_` because `raise` is a reserved keyword in Python.
        """
    @property
    def rate(self, /) -> Property:
        """
        The current playback rate, where `1.0` is the normal speed. Change it with `set_rate`.
        """
    @property
    def removed(self, /) -> Event:
        """
        Emitted when the player disappears from the bus, e.g. when it is closed.
        """
    def seek(self, /, offset: int) -> Any:
        """
        Seeks forward in the current track by `offset` microseconds.
        
        A negative value seeks back. Seeking past the end of the track skips to the next track.
        See [`can_seek`][].
        """
    def set_loop_status(self, /, value: LoopStatus) -> Any:
        """
        Sets the loop status.
        
        Updates [`loop_status`][] if the call succeeds.
        """
    def set_position(self, /, track_id: str, position: int) -> Any:
        """
        Sets the position of the current track to `position` microseconds.
        
        `track_id` must be [`Metadata.track_id`][] of the current track, otherwise the call is
        ignored. This prevents seeking in the wrong track if it has changed in the meantime.
        See [`can_seek`][].
        
        Raises `ValueError` if `track_id` is not a valid D-Bus object path.
        """
    def set_rate(self, /, value: float) -> Any:
        """
        Sets the playback rate.
        
        The value must be in the range from [`minimum_rate`][] to [`maximum_rate`][]. Updates
        [`rate`][] if the call succeeds.
        """
    def set_shuffle(self, /, value: bool) -> Any:
        """
        Enables or disables shuffle.
        
        Updates [`shuffle`][] if the call succeeds.
        """
    def set_volume(self, /, value: float) -> Any:
        """
        Sets the volume level.
        
        Negative values are treated as `0.0`. Updates [`volume`][] if the call succeeds.
        """
    @property
    def shuffle(self, /) -> Property:
        """
        Whether tracks are played in a random order. Change it with `set_shuffle`.
        """
    def stop(self, /) -> Any:
        """
        Stops playback.
        """
    @property
    def supported_mime_types(self, /) -> Property:
        """
        The MIME types supported by the player, e.g. `"audio/mpeg"`.
        """
    @property
    def supported_uri_schemes(self, /) -> Property:
        """
        The URI schemes supported by the player, e.g. `"file"` or `"http"`.
        
        A URI passed to `open_uri` should use one of them.
        """
    @property
    def volume(self, /) -> Property:
        """
        The volume level, where `0.0` is muted and `1.0` is a sensible maximum. Change it with
        `set_volume`.
        """

@final
class Property:
    """
    A value which can change over time.
    
    Read the current value with [`value`][] and observe changes with [`changed`][].
    """
    @property
    def changed(self, /) -> Event:
        """
        Emitted with the new value when the property changes.
        """
    @property
    def value(self, /) -> Any:
        """
        The current value.
        """
