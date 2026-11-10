use pyo3::prelude::*;

/// `ignis_mpris` tracks and controls media players on GNU/Linux desktops that implement the
/// [MPRIS D-Bus Interface Specification](https://specifications.freedesktop.org/mpris/latest/).
///
/// [`MprisService`][] watches the session bus for players. Each player is exposed as a
/// [`Player`][], whose state is kept in sync with the player and exposed as observable
/// [`Property`][] objects.
///
/// # Example
/// ```python
/// import asyncio
/// from ignis_mpris import MprisService, Player
///
///
/// def setup_player(player: Player) -> None:
///     print("Player:", player.identity.value)
///     player.metadata.changed.connect(lambda metadata: print("Now playing:", metadata.title))
///     player.removed.connect(lambda _: print("Player closed"))
///
///
/// async def main() -> None:
///     service = MprisService()
///     await service.run()
///
///     # Players which were already running
///     for player in service.players:
///         setup_player(player)
///
///     # Players which appear later
///     service.player_added.connect(setup_player)
///
///     await asyncio.Event().wait()
///
///
/// asyncio.run(main())
/// ```
#[pymodule]
mod ignis_mpris {
    use mpris::LoopStatus as RLoopStatus;
    use mpris::Metadata as RMetadata;
    use mpris::MprisService as RMprisService;
    use mpris::PlaybackStatus as RPlaybackStatus;
    use mpris::PlayerHandle as RPlayerHandle;
    use py_shared_ignis_core::ToPy;
    use pyo3::IntoPyObjectExt;
    use pyo3::exceptions::PyIOError;
    use pyo3::exceptions::PyOSError;
    use pyo3::exceptions::PyValueError;
    use pyo3::prelude::*;
    use zbus::zvariant::ObjectPath;

    fn to_py_err(e: mpris::Error) -> PyErr {
        let msg = e.to_string();
        match e {
            mpris::Error::DBusError(_) => PyOSError::new_err(msg),
            mpris::Error::OneshotSyncError(_) => PyIOError::new_err(msg),
            mpris::Error::IOError(_) => PyIOError::new_err(msg),
            mpris::Error::CacheDirRetrieveError => PyOSError::new_err(msg),
            mpris::Error::DBusFdoError(_) => PyOSError::new_err(msg),
        }
    }

    /// Metadata of the current track.
    ///
    /// Fields are parsed from the
    /// [MPRIS metadata](https://specifications.freedesktop.org/mpris/latest/Track_List_Interface.html#Mapping:Metadata_Map)
    /// reported by the player. A field is `None` if the player doesn't provide it.
    #[pyclass]
    pub struct Metadata {
        inner: RMetadata,
    }

    impl Metadata {
        fn from_rust(inner: RMetadata) -> Self {
            Self { inner }
        }
    }

    #[pymethods]
    impl Metadata {
        /// The unique identifier of the track within the context of the player's track list.
        ///
        /// Pass it to [`Player.set_position`][].
        #[getter]
        fn track_id(&self) -> Option<String> {
            self.inner.track_id.clone()
        }

        /// The duration of the track in microseconds.
        #[getter]
        fn length(&self) -> Option<i64> {
            self.inner.length
        }

        /// The location of an image representing the track or album, as a URI.
        ///
        /// See also [`Player.cached_cover_art`][], which provides a local copy of the image.
        #[getter]
        fn art_url(&self) -> Option<String> {
            self.inner.art_url.clone()
        }

        /// The album name.
        #[getter]
        fn album(&self) -> Option<String> {
            self.inner.album.clone()
        }

        /// The track artist(s).
        #[getter]
        fn artist(&self) -> Option<String> {
            self.inner.artist.clone()
        }

        /// The album artist(s).
        #[getter]
        fn album_artist(&self) -> Option<String> {
            self.inner.album_artist.clone()
        }

        /// The track lyrics.
        #[getter]
        fn as_text(&self) -> Option<String> {
            self.inner.as_text.clone()
        }

        /// The speed of the music, in beats per minute.
        #[getter]
        fn audio_bpm(&self) -> Option<String> {
            self.inner.audio_bpm.clone()
        }

        /// An automatically-generated rating, based on things such as how often it has been played.
        ///
        /// It is in the range from 0.0 to 1.0.
        #[getter]
        fn auto_rating(&self) -> Option<String> {
            self.inner.auto_rating.clone()
        }

        /// A (list of) freeform comment(s).
        #[getter]
        fn comment(&self) -> Option<String> {
            self.inner.comment.clone()
        }

        /// The composer(s) of the track.
        #[getter]
        fn composer(&self) -> Option<String> {
            self.inner.composer.clone()
        }

        /// When the track was created, as an ISO 8601 date.
        #[getter]
        fn content_created(&self) -> Option<String> {
            self.inner.content_created.clone()
        }

        /// The disc number on the album that this track is from.
        #[getter]
        fn disc_number(&self) -> Option<String> {
            self.inner.disc_number.clone()
        }

        /// When the track was first played, as an ISO 8601 date.
        #[getter]
        fn first_used(&self) -> Option<String> {
            self.inner.first_used.clone()
        }

        /// The genre(s) of the track.
        #[getter]
        fn genre(&self) -> Option<String> {
            self.inner.genre.clone()
        }

        /// When the track was last played, as an ISO 8601 date.
        #[getter]
        fn last_used(&self) -> Option<String> {
            self.inner.last_used.clone()
        }

        /// The lyricist(s) of the track.
        #[getter]
        fn lyricist(&self) -> Option<String> {
            self.inner.lyricist.clone()
        }

        /// The track title.
        #[getter]
        fn title(&self) -> Option<String> {
            self.inner.title.clone()
        }

        /// The track number on the album disc.
        #[getter]
        fn track_number(&self) -> Option<u32> {
            self.inner.track_number
        }

        /// The location of the media file, as a URI.
        #[getter]
        fn url(&self) -> Option<String> {
            self.inner.url.clone()
        }

        /// The number of times the track has been played.
        #[getter]
        fn use_count(&self) -> Option<u32> {
            self.inner.use_count
        }

        /// A user-specified rating, in the range from 0.0 to 1.0.
        #[getter]
        fn user_rating(&self) -> Option<f32> {
            self.inner.user_rating
        }
    }

    /// The looping behavior of a player.
    #[pyclass(from_py_object)]
    #[derive(Clone, Copy, PartialEq, Eq)]
    pub enum LoopStatus {
        /// The playback will stop when there are no more tracks to play.
        ///
        /// Named `None_` because `None` is a reserved keyword in Python.
        #[pyo3(name = "None_")]
        None,

        /// The current track will start again from the beginning once it has finished playing.
        Track,

        /// The playback loops through a list of tracks.
        Playlist,
    }

    /// The playback state of a player.
    #[pyclass(from_py_object)]
    #[derive(Clone, Copy, PartialEq, Eq)]
    pub enum PlaybackStatus {
        /// A track is currently playing.
        Playing,

        /// A track is currently paused.
        Paused,

        /// There is no track currently playing.
        Stopped,
    }

    impl From<&RLoopStatus> for LoopStatus {
        fn from(value: &RLoopStatus) -> Self {
            match value {
                RLoopStatus::None => Self::None,
                RLoopStatus::Track => Self::Track,
                RLoopStatus::Playlist => Self::Playlist,
            }
        }
    }

    impl From<LoopStatus> for RLoopStatus {
        fn from(value: LoopStatus) -> Self {
            match value {
                LoopStatus::None => Self::None,
                LoopStatus::Track => Self::Track,
                LoopStatus::Playlist => Self::Playlist,
            }
        }
    }

    impl From<&RPlaybackStatus> for PlaybackStatus {
        fn from(value: &RPlaybackStatus) -> Self {
            match value {
                RPlaybackStatus::Playing => Self::Playing,
                RPlaybackStatus::Paused => Self::Paused,
                RPlaybackStatus::Stopped => Self::Stopped,
            }
        }
    }

    #[pymodule_export]
    use py_shared_ignis_core::{PyConnectionHandle, PyEvent, PyProperty};

    /// Marker for implementing [`ToPy`] on types from the `mpris` crate.
    struct Marker;

    impl ToPy<Marker> for RLoopStatus {
        fn to_py(&self, py: Python<'_>) -> PyResult<Py<PyAny>> {
            LoopStatus::from(self).into_py_any(py)
        }
    }

    impl ToPy<Marker> for RPlaybackStatus {
        fn to_py(&self, py: Python<'_>) -> PyResult<Py<PyAny>> {
            PlaybackStatus::from(self).into_py_any(py)
        }
    }

    impl ToPy<Marker> for RMetadata {
        fn to_py(&self, py: Python<'_>) -> PyResult<Py<PyAny>> {
            Metadata::from_rust(self.clone()).into_py_any(py)
        }
    }

    impl ToPy<Marker> for RPlayerHandle {
        fn to_py(&self, py: Python<'_>) -> PyResult<Py<PyAny>> {
            Player::from_rust(self.clone()).into_py_any(py)
        }
    }

    /// A media player.
    ///
    /// Its properties are [`Property`][] objects which are kept in sync with the player: read the
    /// current value with `value` and observe changes with `changed`. A property the player doesn't
    /// provide has a default value (e.g. `False` or an empty string).
    ///
    /// ```python
    /// print(player.volume.value)
    /// player.volume.changed.connect(lambda volume: print("New volume:", volume))
    /// ```
    ///
    /// Methods return awaitables and raise `OSError` if the D-Bus call fails.
    #[pyclass]
    struct Player {
        inner: RPlayerHandle,
    }

    mpris::player_properties!(
        py_shared_ignis_core::py_properties,
        Player,
        inner.properties,
        Marker
    );

    mpris::player_events!(py_shared_ignis_core::py_events, Player, inner.events);

    impl Player {
        fn from_rust(inner: RPlayerHandle) -> Self {
            Self { inner }
        }
    }

    #[pymethods]
    impl Player {
        /// Asks the player to quit.
        ///
        /// The player may ignore this. See [`can_quit`][].
        fn quit<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
            let inner = self.inner.clone();
            pyo3_async_runtimes::tokio::future_into_py(py, async move {
                inner.quit().await.map_err(to_py_err)
            })
        }

        /// Asks the player to bring its user interface to the front.
        ///
        /// The player may ignore this. See [`can_raise`][].
        ///
        /// Named `raise_` because `raise` is a reserved keyword in Python.
        #[pyo3(name = "raise_")]
        fn raise<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
            let inner = self.inner.clone();
            pyo3_async_runtimes::tokio::future_into_py(py, async move {
                inner.raise().await.map_err(to_py_err)
            })
        }

        //
        // MediaPlayer2.Player
        //

        /// Skips to the next track in the tracklist.
        ///
        /// If there is no next track (and endless playback and track repeat are both off), stops
        /// playback. See [`can_go_next`][].
        fn next<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
            let inner = self.inner.clone();
            pyo3_async_runtimes::tokio::future_into_py(py, async move {
                inner.next().await.map_err(to_py_err)
            })
        }

        /// Opens the URI and starts playing it.
        ///
        /// The URI scheme should be one of [`supported_uri_schemes`][] and the media type should be one
        /// of [`supported_mime_types`][].
        fn open_uri<'py>(&self, py: Python<'py>, uri: String) -> PyResult<Bound<'py, PyAny>> {
            let inner = self.inner.clone();
            pyo3_async_runtimes::tokio::future_into_py(py, async move {
                inner.open_uri(&uri).await.map_err(to_py_err)
            })
        }

        /// Pauses playback.
        ///
        /// If playback is already paused, this has no effect. See [`can_pause`][].
        fn pause<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
            let inner = self.inner.clone();
            pyo3_async_runtimes::tokio::future_into_py(py, async move {
                inner.pause().await.map_err(to_py_err)
            })
        }

        /// Starts or resumes playback.
        ///
        /// If already playing, this has no effect. See [`can_play`][].
        fn play<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
            let inner = self.inner.clone();
            pyo3_async_runtimes::tokio::future_into_py(py, async move {
                inner.play().await.map_err(to_py_err)
            })
        }

        /// Pauses playback if it's playing, otherwise starts or resumes it.
        fn play_pause<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
            let inner = self.inner.clone();
            pyo3_async_runtimes::tokio::future_into_py(py, async move {
                inner.play_pause().await.map_err(to_py_err)
            })
        }

        /// Skips to the previous track in the tracklist.
        ///
        /// If there is no previous track (and endless playback and track repeat are both off), stops
        /// playback. See [`can_go_previous`][].
        fn previous<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
            let inner = self.inner.clone();
            pyo3_async_runtimes::tokio::future_into_py(py, async move {
                inner.previous().await.map_err(to_py_err)
            })
        }

        /// Seeks forward in the current track by `offset` microseconds.
        ///
        /// A negative value seeks back. Seeking past the end of the track skips to the next track.
        /// See [`can_seek`][].
        fn seek<'py>(&self, py: Python<'py>, offset: i64) -> PyResult<Bound<'py, PyAny>> {
            let inner = self.inner.clone();
            pyo3_async_runtimes::tokio::future_into_py(py, async move {
                inner.seek(offset).await.map_err(to_py_err)
            })
        }

        /// Sets the position of the current track to `position` microseconds.
        ///
        /// `track_id` must be [`Metadata.track_id`][] of the current track, otherwise the call is
        /// ignored. This prevents seeking in the wrong track if it has changed in the meantime.
        /// See [`can_seek`][].
        ///
        /// Raises `ValueError` if `track_id` is not a valid D-Bus object path.
        fn set_position<'py>(
            &self,
            py: Python<'py>,
            track_id: String,
            position: i64,
        ) -> PyResult<Bound<'py, PyAny>> {
            let track_id = ObjectPath::try_from(track_id)
                .map_err(|e| PyValueError::new_err(format!("Invalid track ID: {e}")))?;
            let inner = self.inner.clone();
            pyo3_async_runtimes::tokio::future_into_py(py, async move {
                inner
                    .set_position(&track_id, position)
                    .await
                    .map_err(to_py_err)
            })
        }

        /// Stops playback.
        fn stop<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
            let inner = self.inner.clone();
            pyo3_async_runtimes::tokio::future_into_py(py, async move {
                inner.stop().await.map_err(to_py_err)
            })
        }

        /// Sets the loop status.
        ///
        /// Updates [`loop_status`][] if the call succeeds.
        fn set_loop_status<'py>(
            &self,
            py: Python<'py>,
            value: LoopStatus,
        ) -> PyResult<Bound<'py, PyAny>> {
            let inner = self.inner.clone();
            pyo3_async_runtimes::tokio::future_into_py(py, async move {
                inner.set_loop_status(value.into()).await.map_err(to_py_err)
            })
        }

        /// Sets the playback rate.
        ///
        /// The value must be in the range from [`minimum_rate`][] to [`maximum_rate`][]. Updates
        /// [`rate`][] if the call succeeds.
        fn set_rate<'py>(&self, py: Python<'py>, value: f64) -> PyResult<Bound<'py, PyAny>> {
            let inner = self.inner.clone();
            pyo3_async_runtimes::tokio::future_into_py(py, async move {
                inner.set_rate(value).await.map_err(to_py_err)
            })
        }

        /// Enables or disables shuffle.
        ///
        /// Updates [`shuffle`][] if the call succeeds.
        fn set_shuffle<'py>(&self, py: Python<'py>, value: bool) -> PyResult<Bound<'py, PyAny>> {
            let inner = self.inner.clone();
            pyo3_async_runtimes::tokio::future_into_py(py, async move {
                inner.set_shuffle(value).await.map_err(to_py_err)
            })
        }

        /// Sets the volume level.
        ///
        /// Negative values are treated as `0.0`. Updates [`volume`][] if the call succeeds.
        fn set_volume<'py>(&self, py: Python<'py>, value: f64) -> PyResult<Bound<'py, PyAny>> {
            let inner = self.inner.clone();
            pyo3_async_runtimes::tokio::future_into_py(py, async move {
                inner.set_volume(value).await.map_err(to_py_err)
            })
        }
    }

    /// A service which tracks media players on the session bus.
    ///
    /// A player is any D-Bus client which owns a name starting with `org.mpris.MediaPlayer2`.
    ///
    /// Cover arts are cached in `$XDG_CACHE_HOME/ignis-mpris/images`.
    #[pyclass]
    struct MprisService {
        inner: RMprisService,
    }

    mpris::mpris_service_events!(
        py_shared_ignis_core::py_events,
        MprisService,
        inner.events,
        Marker
    );

    #[pymethods]
    impl MprisService {
        #[new]
        fn new() -> Self {
            let service = RMprisService::new();
            Self { inner: service }
        }

        /// The currently running players.
        #[getter]
        fn players(&self) -> Vec<Player> {
            self.inner
                .players()
                .into_iter()
                .map(Player::from_rust)
                .collect()
        }

        /// Runs the service.
        ///
        /// Connects to the session bus, adds players which are already running and starts watching for
        /// players appearing and disappearing in the background. Must be called only once.
        ///
        /// Players that fail to initialize are skipped.
        ///
        /// Raises `OSError` if connecting to the session bus fails.
        fn run<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
            let inner = self.inner.clone();
            pyo3_async_runtimes::tokio::future_into_py(py, async move {
                inner.run().await.map_err(to_py_err)
            })
        }
    }
}
