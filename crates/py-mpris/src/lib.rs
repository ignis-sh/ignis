use pyo3::prelude::*;

#[pymodule]
mod py_mpris {
    use mpris::LoopStatus as RLoopStatus;
    use mpris::Metadata as RMetadata;
    use mpris::MprisService as RMprisService;
    use mpris::PlaybackStatus as RPlaybackStatus;
    use mpris::PlayerHandle as RPlayerHandle;
    use py_shared_ignis_core::ToPy;
    use pyo3::IntoPyObjectExt;
    use pyo3::prelude::*;

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
    }
}
