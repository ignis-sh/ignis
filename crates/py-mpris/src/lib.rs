use pyo3::prelude::*;

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
        #[getter]
        fn track_id(&self) -> Option<String> {
            self.inner.track_id.clone()
        }

        #[getter]
        fn length(&self) -> Option<i64> {
            self.inner.length
        }

        #[getter]
        fn art_url(&self) -> Option<String> {
            self.inner.art_url.clone()
        }

        #[getter]
        fn album(&self) -> Option<String> {
            self.inner.album.clone()
        }

        #[getter]
        fn artist(&self) -> Option<String> {
            self.inner.artist.clone()
        }

        #[getter]
        fn album_artist(&self) -> Option<String> {
            self.inner.album_artist.clone()
        }

        #[getter]
        fn as_text(&self) -> Option<String> {
            self.inner.as_text.clone()
        }

        #[getter]
        fn audio_bpm(&self) -> Option<String> {
            self.inner.audio_bpm.clone()
        }

        #[getter]
        fn auto_rating(&self) -> Option<String> {
            self.inner.auto_rating.clone()
        }

        #[getter]
        fn comment(&self) -> Option<String> {
            self.inner.comment.clone()
        }

        #[getter]
        fn composer(&self) -> Option<String> {
            self.inner.composer.clone()
        }

        #[getter]
        fn content_created(&self) -> Option<String> {
            self.inner.content_created.clone()
        }

        #[getter]
        fn disc_number(&self) -> Option<String> {
            self.inner.disc_number.clone()
        }

        #[getter]
        fn first_used(&self) -> Option<String> {
            self.inner.first_used.clone()
        }

        #[getter]
        fn genre(&self) -> Option<String> {
            self.inner.genre.clone()
        }

        #[getter]
        fn last_used(&self) -> Option<String> {
            self.inner.last_used.clone()
        }

        #[getter]
        fn lyricist(&self) -> Option<String> {
            self.inner.lyricist.clone()
        }

        #[getter]
        fn title(&self) -> Option<String> {
            self.inner.title.clone()
        }

        #[getter]
        fn track_number(&self) -> Option<u32> {
            self.inner.track_number
        }

        #[getter]
        fn url(&self) -> Option<String> {
            self.inner.url.clone()
        }

        #[getter]
        fn use_count(&self) -> Option<u32> {
            self.inner.use_count
        }

        #[getter]
        fn user_rating(&self) -> Option<f32> {
            self.inner.user_rating
        }
    }

    #[pyclass(from_py_object)]
    #[derive(Clone, Copy, PartialEq, Eq)]
    pub enum LoopStatus {
        None,
        Track,
        Playlist,
    }

    #[pyclass(from_py_object)]
    #[derive(Clone, Copy, PartialEq, Eq)]
    pub enum PlaybackStatus {
        Playing,
        Paused,
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

    impl Player {
        fn from_rust(inner: RPlayerHandle) -> Self {
            Self { inner }
        }
    }

    #[pymethods]
    impl Player {
        fn quit<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
            let inner = self.inner.clone();
            pyo3_async_runtimes::tokio::future_into_py(py, async move {
                inner.quit().await.map_err(to_py_err)
            })
        }

        fn raise<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
            let inner = self.inner.clone();
            pyo3_async_runtimes::tokio::future_into_py(py, async move {
                inner.raise().await.map_err(to_py_err)
            })
        }

        //
        // MediaPlayer2.Player
        //

        fn next<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
            let inner = self.inner.clone();
            pyo3_async_runtimes::tokio::future_into_py(py, async move {
                inner.next().await.map_err(to_py_err)
            })
        }

        fn open_uri<'py>(&self, py: Python<'py>, uri: String) -> PyResult<Bound<'py, PyAny>> {
            let inner = self.inner.clone();
            pyo3_async_runtimes::tokio::future_into_py(py, async move {
                inner.open_uri(&uri).await.map_err(to_py_err)
            })
        }

        fn pause<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
            let inner = self.inner.clone();
            pyo3_async_runtimes::tokio::future_into_py(py, async move {
                inner.pause().await.map_err(to_py_err)
            })
        }

        fn play<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
            let inner = self.inner.clone();
            pyo3_async_runtimes::tokio::future_into_py(py, async move {
                inner.play().await.map_err(to_py_err)
            })
        }

        fn play_pause<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
            let inner = self.inner.clone();
            pyo3_async_runtimes::tokio::future_into_py(py, async move {
                inner.play_pause().await.map_err(to_py_err)
            })
        }

        fn previous<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
            let inner = self.inner.clone();
            pyo3_async_runtimes::tokio::future_into_py(py, async move {
                inner.previous().await.map_err(to_py_err)
            })
        }

        fn seek<'py>(&self, py: Python<'py>, offset: i64) -> PyResult<Bound<'py, PyAny>> {
            let inner = self.inner.clone();
            pyo3_async_runtimes::tokio::future_into_py(py, async move {
                inner.seek(offset).await.map_err(to_py_err)
            })
        }

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

        fn stop<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
            let inner = self.inner.clone();
            pyo3_async_runtimes::tokio::future_into_py(py, async move {
                inner.stop().await.map_err(to_py_err)
            })
        }

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

        fn set_rate<'py>(&self, py: Python<'py>, value: f64) -> PyResult<Bound<'py, PyAny>> {
            let inner = self.inner.clone();
            pyo3_async_runtimes::tokio::future_into_py(py, async move {
                inner.set_rate(value).await.map_err(to_py_err)
            })
        }

        fn set_shuffle<'py>(&self, py: Python<'py>, value: bool) -> PyResult<Bound<'py, PyAny>> {
            let inner = self.inner.clone();
            pyo3_async_runtimes::tokio::future_into_py(py, async move {
                inner.set_shuffle(value).await.map_err(to_py_err)
            })
        }

        fn set_volume<'py>(&self, py: Python<'py>, value: f64) -> PyResult<Bound<'py, PyAny>> {
            let inner = self.inner.clone();
            pyo3_async_runtimes::tokio::future_into_py(py, async move {
                inner.set_volume(value).await.map_err(to_py_err)
            })
        }
    }

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

        #[getter]
        fn players(&self) -> Vec<Player> {
            self.inner
                .players()
                .into_iter()
                .map(Player::from_rust)
                .collect()
        }

        fn run<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
            let inner = self.inner.clone();
            pyo3_async_runtimes::tokio::future_into_py(py, async move {
                inner.run().await.map_err(to_py_err)
            })
        }
    }
}
