use crate::dbus::{MediaPlayer2Proxy, PlayerProxy};
use crate::private_prelude::*;
use futures_util::StreamExt;
use ignis_core::event::EventOwner;
use ignis_core::property::PropertyOwner;
use ignis_core::{Events, Properties};
use std::collections::HashMap;
use std::path::PathBuf;
use std::sync::Arc;
use std::time::Duration;
use tokio::time::MissedTickBehavior;
use url::Url;
use uuid::Uuid;
use zbus::Connection;

async fn media_player_proxy<'a>(
    connection: &zbus::Connection,
    name: &'a str,
) -> Result<MediaPlayer2Proxy<'a>> {
    Ok(MediaPlayer2Proxy::builder(connection)
        .destination(name)
        .unwrap()
        .build()
        .await?)
}

async fn player_proxy<'a>(connection: &zbus::Connection, name: &'a str) -> Result<PlayerProxy<'a>> {
    Ok(PlayerProxy::builder(connection)
        .destination(name)
        .unwrap()
        .build()
        .await?)
}

pub struct PositionTracker {
    position_us: i64,
    updated_at: std::time::Instant,
    rate: f64,
    playing: bool,
}

impl PositionTracker {
    pub fn current(&self) -> i64 {
        let elapsed = self.updated_at.elapsed().as_secs_f64();

        if self.playing {
            self.position_us + (elapsed * self.rate * 1_000_000.0) as i64
        } else {
            self.position_us
        }
    }

    fn sync(&mut self, position_us: i64) {
        self.position_us = position_us;
        self.updated_at = std::time::Instant::now();
    }
}

/// Properties of a [`PlayerHandle`].
///
/// They are kept in sync with the player. A property the player doesn't provide has the default
/// value of its type (e.g. `false` or an empty string).
#[derive(Properties)]
#[properties(handle = PlayerHandleProperties, export = player_properties)]
struct PlayerOwnerProperties {
    /// Whether the player can be closed with `quit`.
    can_quit: PropertyOwner<bool>,

    /// Whether the player can be brought to the front with `raise`.
    can_raise: PropertyOwner<bool>,

    /// Whether the player's fullscreen state can be changed.
    can_set_fullscreen: PropertyOwner<bool>,

    /// The basename of the player's desktop entry, e.g. `"vlc"` for `vlc.desktop`.
    ///
    /// Empty if the player doesn't provide it.
    desktop_entry: PropertyOwner<String>,

    /// Whether the player is occupying the fullscreen.
    fullscreen: PropertyOwner<bool>,

    /// Whether the player has a track list.
    has_track_list: PropertyOwner<bool>,

    /// A friendly name to identify the player to users, e.g. `"VLC media player"`.
    identity: PropertyOwner<String>,

    /// The MIME types supported by the player, e.g. `"audio/mpeg"`.
    supported_mime_types: PropertyOwner<Vec<String>>,

    /// The URI schemes supported by the player, e.g. `"file"` or `"http"`.
    ///
    /// A URI passed to `open_uri` should use one of them.
    supported_uri_schemes: PropertyOwner<Vec<String>>,

    /// Whether the player can be controlled.
    ///
    /// If not, calling any method or setting any property will likely fail.
    can_control: PropertyOwner<bool>,

    /// Whether `next` is expected to skip to the next track.
    can_go_next: PropertyOwner<bool>,

    /// Whether `previous` is expected to skip to the previous track.
    can_go_previous: PropertyOwner<bool>,

    /// Whether playback can be paused using `pause` or `play_pause`.
    can_pause: PropertyOwner<bool>,

    /// Whether playback can be started using `play` or `play_pause`.
    can_play: PropertyOwner<bool>,

    /// Whether the position can be changed using `seek` and `set_position`.
    can_seek: PropertyOwner<bool>,

    /// The current loop status. Change it with `set_loop_status`.
    loop_status: PropertyOwner<LoopStatus>,

    /// The maximum value which `rate` can take.
    maximum_rate: PropertyOwner<f64>,

    /// The minimum value which `rate` can take.
    minimum_rate: PropertyOwner<f64>,

    /// The current playback status.
    playback_status: PropertyOwner<PlaybackStatus>,

    /// The current playback rate, where `1.0` is the normal speed. Change it with `set_rate`.
    rate: PropertyOwner<f64>,

    /// Whether tracks are played in a random order. Change it with `set_shuffle`.
    shuffle: PropertyOwner<bool>,

    /// The volume level, where `0.0` is muted and `1.0` is a sensible maximum. Change it with
    /// `set_volume`.
    volume: PropertyOwner<f64>,

    /// The metadata of the current track.
    metadata: PropertyOwner<Metadata>,

    /// The current track position in microseconds.
    ///
    /// The position is computed locally from the last position reported by the player, the
    /// playback status and the rate. Its `changed` event is emitted every 200 milliseconds.
    position: PropertyOwner<i64>,

    /// The path to a local copy of the current track's cover art (`art_url` of `metadata`).
    ///
    /// The image is downloaded (`http` and `https` URIs) or copied (`file` URIs) into the cache
    /// directory. `None` if the cover art can't be cached.
    cached_cover_art: PropertyOwner<Option<PathBuf>>,
}

/// Events of a [`PlayerHandle`].
#[derive(Events, Default)]
#[events(handle = PlayerHandleEvents, export = player_events)]
pub(crate) struct PlayerOwnerEvents {
    /// Emitted when the player disappears from the bus, e.g. when it is closed.
    pub(crate) removed: EventOwner<()>,
}

pub(crate) struct Player {
    name: String,
    connection: Connection,
    properties: Arc<PlayerOwnerProperties>,
    pub(crate) events: PlayerOwnerEvents,
}

impl Player {
    pub(crate) async fn new(name: String, cache_dir: Option<PathBuf>) -> Result<Self> {
        let connection = Connection::session().await?;

        let media_player_proxy = media_player_proxy(&connection, &name).await?;
        let player_proxy = player_proxy(&connection, &name).await?;

        let metadata: Metadata = player_proxy.metadata().await.unwrap_or_default().into();

        let cached_cover_art_dir =
            cache_dir.and_then(|v| file_utils::get_cached_cover_art_dir(v).ok());

        let properties = Arc::new(PlayerOwnerProperties {
            can_quit: PropertyOwner::new(media_player_proxy.can_quit().await.unwrap_or_default()),

            can_raise: PropertyOwner::new(media_player_proxy.can_raise().await.unwrap_or_default()),
            can_set_fullscreen: PropertyOwner::new(
                media_player_proxy
                    .can_set_fullscreen()
                    .await
                    .unwrap_or_default(),
            ),
            desktop_entry: PropertyOwner::new(
                media_player_proxy.desktop_entry().await.unwrap_or_default(),
            ),
            fullscreen: PropertyOwner::new(
                media_player_proxy.fullscreen().await.unwrap_or_default(),
            ),
            has_track_list: PropertyOwner::new(
                media_player_proxy
                    .has_track_list()
                    .await
                    .unwrap_or_default(),
            ),
            identity: PropertyOwner::new(media_player_proxy.identity().await.unwrap_or_default()),
            supported_mime_types: PropertyOwner::new(
                media_player_proxy
                    .supported_mime_types()
                    .await
                    .unwrap_or_default(),
            ),
            supported_uri_schemes: PropertyOwner::new(
                media_player_proxy
                    .supported_uri_schemes()
                    .await
                    .unwrap_or_default(),
            ),

            can_control: PropertyOwner::new(player_proxy.can_control().await.unwrap_or_default()),
            can_go_next: PropertyOwner::new(player_proxy.can_go_next().await.unwrap_or_default()),
            can_go_previous: PropertyOwner::new(
                player_proxy.can_go_previous().await.unwrap_or_default(),
            ),
            can_pause: PropertyOwner::new(player_proxy.can_pause().await.unwrap_or_default()),
            can_play: PropertyOwner::new(player_proxy.can_play().await.unwrap_or_default()),
            can_seek: PropertyOwner::new(player_proxy.can_seek().await.unwrap_or_default()),
            loop_status: PropertyOwner::new(
                player_proxy.loop_status().await.unwrap_or_default().into(),
            ),
            maximum_rate: PropertyOwner::new(player_proxy.maximum_rate().await.unwrap_or_default()),
            minimum_rate: PropertyOwner::new(player_proxy.minimum_rate().await.unwrap_or_default()),
            playback_status: PropertyOwner::new(
                player_proxy
                    .playback_status()
                    .await
                    .unwrap_or_default()
                    .into(),
            ),
            rate: PropertyOwner::new(player_proxy.rate().await.unwrap_or_default()),
            shuffle: PropertyOwner::new(player_proxy.shuffle().await.unwrap_or_default()),
            volume: PropertyOwner::new(player_proxy.volume().await.unwrap_or_default()),
            cached_cover_art: PropertyOwner::new(
                Self::cache_art_cover(cached_cover_art_dir.clone(), &metadata).await,
            ),
            position: PropertyOwner::new(player_proxy.position().await.unwrap_or_default()),
            metadata: PropertyOwner::new(metadata),
        });

        let obj = Player {
            name: name.clone(),
            connection: connection.clone(),
            properties: properties.clone(),
            events: PlayerOwnerEvents::default(),
        };

        let (ready_tx, ready_rx) = tokio::sync::oneshot::channel();

        let name_clone = name.clone();
        let connection_clone = connection.clone();
        let properties_clone = properties.clone();
        tokio::spawn(async move {
            if let Err(e) = Self::listen_properties_change(
                connection_clone,
                name_clone,
                cached_cover_art_dir,
                properties_clone,
                ready_tx,
            )
            .await
            {
                eprintln!("Property listener failed: {e:?}");
            }
        });

        ready_rx.await?;

        tokio::spawn(async move {
            if let Err(e) = Self::track_position(connection, name, properties).await {
                eprintln!("Position tracker failed failed: {e:?}");
            }
        });

        Ok(obj)
    }

    async fn listen_properties_change(
        connection: Connection,
        name: String,
        cached_cover_art_dir: Option<PathBuf>,
        properties: Arc<PlayerOwnerProperties>,
        ready_tx: tokio::sync::oneshot::Sender<()>,
    ) -> Result<()> {
        let proxy =
            zbus::fdo::PropertiesProxy::new(&connection, name.clone(), "/org/mpris/MediaPlayer2")
                .await?;

        let mut stream = proxy.receive_properties_changed().await?;

        let _ = ready_tx.send(());

        while let Some(message) = stream.next().await {
            if let Ok(args) = message.args() {
                match args.interface_name.as_str() {
                    "org.mpris.MediaPlayer2" => {
                        for (key, value) in args.changed_properties {
                            match key {
                                "CanQuit" => properties
                                    .can_quit
                                    .set(bool::try_from(value).unwrap_or_default()),
                                "CanRaise" => properties
                                    .can_raise
                                    .set(bool::try_from(value).unwrap_or_default()),
                                "CanSetFullscreen" => properties
                                    .can_set_fullscreen
                                    .set(bool::try_from(value).unwrap_or_default()),
                                "DesktopEntry" => properties
                                    .desktop_entry
                                    .set(String::try_from(value).unwrap_or_default()),
                                "Fullscreen" => properties
                                    .fullscreen
                                    .set(bool::try_from(value).unwrap_or_default()),
                                "HasTrackList" => properties
                                    .has_track_list
                                    .set(bool::try_from(value).unwrap_or_default()),
                                "Identity" => properties
                                    .identity
                                    .set(String::try_from(value).unwrap_or_default()),
                                "SupportedMimeTypes" => properties
                                    .supported_mime_types
                                    .set(Vec::try_from(value).unwrap_or_default()),
                                "SupportedUriSchemes" => properties
                                    .supported_uri_schemes
                                    .set(Vec::try_from(value).unwrap_or_default()),

                                _ => {}
                            }
                        }
                    }
                    //
                    "org.mpris.MediaPlayer2.Player" => {
                        for (key, value) in args.changed_properties {
                            match key {
                                "CanControl" => properties
                                    .can_control
                                    .set(bool::try_from(value).unwrap_or_default()),
                                "CanGoNext" => properties
                                    .can_go_next
                                    .set(bool::try_from(value).unwrap_or_default()),
                                "CanGoPrevious" => properties
                                    .can_go_previous
                                    .set(bool::try_from(value).unwrap_or_default()),
                                "CanPause" => properties
                                    .can_pause
                                    .set(bool::try_from(value).unwrap_or_default()),
                                "CanPlay" => properties
                                    .can_play
                                    .set(bool::try_from(value).unwrap_or_default()),
                                "CanSeek" => properties
                                    .can_seek
                                    .set(bool::try_from(value).unwrap_or_default()),
                                "LoopStatus" => properties
                                    .loop_status
                                    .set(String::try_from(value).unwrap_or_default().into()),
                                "MaximumRate" => properties
                                    .maximum_rate
                                    .set(f64::try_from(value).unwrap_or_default()),
                                "Metadata" => {
                                    let metadata =
                                        HashMap::try_from(value).unwrap_or_default().into();

                                    if let Some(path) = Self::cache_art_cover(
                                        cached_cover_art_dir.clone(),
                                        &metadata,
                                    )
                                    .await
                                    {
                                        if path
                                            != properties
                                                .cached_cover_art
                                                .return_property()
                                                .read(|v| v.clone())
                                                .unwrap_or_default()
                                        {
                                            properties.cached_cover_art.set(Some(path));
                                        };
                                    }

                                    properties.metadata.set(metadata);
                                }

                                "MinimumRate" => properties
                                    .minimum_rate
                                    .set(f64::try_from(value).unwrap_or_default()),
                                "PlaybackStatus" => properties
                                    .playback_status
                                    .set(String::try_from(value).unwrap_or_default().into()),
                                "Rate" => properties
                                    .rate
                                    .set(f64::try_from(value).unwrap_or_default()),
                                "Shuffle" => properties
                                    .shuffle
                                    .set(bool::try_from(value).unwrap_or_default()),
                                "Volume" => properties
                                    .volume
                                    .set(f64::try_from(value).unwrap_or_default()),
                                _ => {}
                            }
                        }
                    }
                    _ => {}
                }
            }
        }

        Ok(())
    }

    async fn media_player_proxy(&self) -> Result<MediaPlayer2Proxy<'_>> {
        media_player_proxy(&self.connection, &self.name).await
    }

    async fn player_proxy(&self) -> Result<PlayerProxy<'_>> {
        player_proxy(&self.connection, &self.name).await
    }

    async fn cache_art_cover(
        cached_cover_art_dir: Option<PathBuf>,
        metadata: &Metadata,
    ) -> Option<PathBuf> {
        let url = Url::parse(&metadata.art_url.clone()?).ok()?;
        let filename = Uuid::new_v5(&Uuid::NAMESPACE_URL, url.as_str().as_bytes());

        let destination = cached_cover_art_dir?.join(filename.to_string());

        if destination.exists() {
            return Some(destination);
        }

        match url.scheme() {
            "http" | "https" => {
                let response = reqwest::get(url.as_str()).await.ok()?;

                let bytes = response.bytes().await.ok()?;
                tokio::fs::write(&destination, bytes).await.ok()?;
                Some(destination)
            }

            "file" => {
                let source = url.to_file_path().ok()?;
                tokio::fs::copy(source, &destination).await.ok()?;
                Some(destination)
            }

            scheme => {
                eprintln!("Unsupported URI scheme: {scheme}");
                None
            }
        }
    }

    async fn track_position(
        connection: Connection,
        name: String,
        properties: Arc<PlayerOwnerProperties>,
    ) -> Result<()> {
        let player = player_proxy(&connection, &name).await?;
        let mut tracker = PositionTracker {
            position_us: player.position().await?,
            updated_at: std::time::Instant::now(),
            rate: player.rate().await?,
            playing: player.playback_status().await? == "Playing",
        };

        let mut seeked = player.receive_seeked().await?;
        let mut status = player.receive_playback_status_changed().await;
        let mut rate = player.receive_rate_changed().await;

        let mut interval = tokio::time::interval(Duration::from_millis(200));
        interval.set_missed_tick_behavior(MissedTickBehavior::Skip);

        loop {
            tokio::select! {
                Some(signal) = seeked.next() => {
                    let args = signal.args()?;
                    tracker.sync(*args.position());
                    properties.position.set(*args.position());
                }

                Some(change) = status.next() => {
                    let new_status = change.get().await?;

                    let current = tracker.current();
                    tracker.sync(current);
                    properties.position.set(current);
                    tracker.playing = new_status == "Playing";
                }

                Some(change) = rate.next() => {
                    let new_rate = change.get().await?;

                    let current = tracker.current();
                    tracker.sync(current);

                    properties.position.set(current);
                    tracker.rate = new_rate;
                }

                _ = interval.tick() => {
                    let current = tracker.current();
                    tracker.sync(current);
                    properties.position.set(current);
                }

                else => break,
            }
        }

        Ok(())
    }
}

/// A handle to a media player.
///
/// Implements the `org.mpris.MediaPlayer2` and `org.mpris.MediaPlayer2.Player` D-Bus interfaces.
///
/// [`PlayerHandle`] implements [`Clone`] and can be cloned cheaply since underlying data is
/// shared.
#[derive(Clone)]
pub struct PlayerHandle {
    pub(crate) inner: Arc<Player>,

    /// Properties of the player.
    pub properties: PlayerHandleProperties,

    /// Events of the player.
    pub events: PlayerHandleEvents,
}

impl PlayerHandle {
    pub(crate) fn new(inner: Arc<Player>) -> Self {
        Self {
            inner: inner.clone(),
            properties: inner.properties.handle(),
            events: inner.events.handle(),
        }
    }

    /// Asks the player to quit.
    ///
    /// The player may ignore this. See `can_quit`.
    ///
    /// # Errors
    /// Returns [`Error::DBusError`] or [`Error::DBusFdoError`] if the D-Bus call fails.
    pub async fn quit(&self) -> Result<()> {
        self.inner.media_player_proxy().await?.quit().await?;
        Ok(())
    }

    /// Asks the player to bring its user interface to the front.
    ///
    /// The player may ignore this. See `can_raise`.
    ///
    /// # Errors
    /// Returns [`Error::DBusError`] or [`Error::DBusFdoError`] if the D-Bus call fails.
    pub async fn raise(&self) -> Result<()> {
        self.inner.media_player_proxy().await?.raise().await?;
        Ok(())
    }

    //
    // MediaPlayer2.Player
    //

    /// Skips to the next track in the tracklist.
    ///
    /// If there is no next track (and endless playback and track repeat are both off), stops
    /// playback. See `can_go_next`.
    ///
    /// # Errors
    /// Returns [`Error::DBusError`] or [`Error::DBusFdoError`] if the D-Bus call fails.
    pub async fn next(&self) -> Result<()> {
        self.inner.player_proxy().await?.next().await?;
        Ok(())
    }

    /// Opens the URI and starts playing it.
    ///
    /// The URI scheme should be one of `supported_uri_schemes` and the media type should be one of
    /// `supported_mime_types`.
    ///
    /// # Errors
    /// Returns [`Error::DBusError`] or [`Error::DBusFdoError`] if the D-Bus call fails, e.g. if the
    /// URI is not supported.
    pub async fn open_uri(&self, uri: &str) -> Result<()> {
        self.inner.player_proxy().await?.open_uri(uri).await?;
        Ok(())
    }

    /// Pauses playback.
    ///
    /// If playback is already paused, this has no effect. See `can_pause`.
    ///
    /// # Errors
    /// Returns [`Error::DBusError`] or [`Error::DBusFdoError`] if the D-Bus call fails.
    pub async fn pause(&self) -> Result<()> {
        self.inner.player_proxy().await?.pause().await?;
        Ok(())
    }

    /// Starts or resumes playback.
    ///
    /// If already playing, this has no effect. See `can_play`.
    ///
    /// # Errors
    /// Returns [`Error::DBusError`] or [`Error::DBusFdoError`] if the D-Bus call fails.
    pub async fn play(&self) -> Result<()> {
        self.inner.player_proxy().await?.play().await?;
        Ok(())
    }

    /// Pauses playback if it's playing, otherwise starts or resumes it.
    ///
    /// # Errors
    /// Returns [`Error::DBusError`] or [`Error::DBusFdoError`] if the D-Bus call fails.
    pub async fn play_pause(&self) -> Result<()> {
        self.inner.player_proxy().await?.play_pause().await?;
        Ok(())
    }

    /// Skips to the previous track in the tracklist.
    ///
    /// If there is no previous track (and endless playback and track repeat are both off), stops
    /// playback. See `can_go_previous`.
    ///
    /// # Errors
    /// Returns [`Error::DBusError`] or [`Error::DBusFdoError`] if the D-Bus call fails.
    pub async fn previous(&self) -> Result<()> {
        self.inner.player_proxy().await?.previous().await?;
        Ok(())
    }

    /// Seeks forward in the current track by `offset` microseconds.
    ///
    /// A negative value seeks back. Seeking past the end of the track skips to the next track.
    /// See `can_seek`.
    ///
    /// # Errors
    /// Returns [`Error::DBusError`] or [`Error::DBusFdoError`] if the D-Bus call fails.
    pub async fn seek(&self, offset: i64) -> Result<()> {
        self.inner.player_proxy().await?.seek(offset).await?;
        Ok(())
    }

    /// Sets the position of the current track to `position` microseconds.
    ///
    /// `track_id` must be the `track_id` from `metadata` of the current track, otherwise the call
    /// is ignored. This prevents seeking in the wrong track if it has changed in the meantime.
    /// See `can_seek`.
    ///
    /// # Errors
    /// Returns [`Error::DBusError`] or [`Error::DBusFdoError`] if the D-Bus call fails.
    pub async fn set_position(
        &self,
        track_id: &zbus::zvariant::ObjectPath<'_>,
        position: i64,
    ) -> Result<()> {
        self.inner
            .player_proxy()
            .await?
            .set_position(track_id, position)
            .await?;

        Ok(())
    }

    /// Stops playback.
    ///
    /// # Errors
    /// Returns [`Error::DBusError`] or [`Error::DBusFdoError`] if the D-Bus call fails.
    pub async fn stop(&self) -> Result<()> {
        self.inner.player_proxy().await?.stop().await?;

        Ok(())
    }

    /// Sets the loop status.
    ///
    /// Updates `loop_status` if the call succeeds.
    ///
    /// # Errors
    /// Returns [`Error::DBusError`] or [`Error::DBusFdoError`] if the D-Bus call fails.
    pub async fn set_loop_status(&self, value: LoopStatus) -> Result<()> {
        self.inner
            .player_proxy()
            .await?
            .set_loop_status(&value.to_string())
            .await?;

        self.inner.properties.loop_status.set(value);

        Ok(())
    }

    /// Sets the playback rate.
    ///
    /// The value must be in the range from `minimum_rate` to `maximum_rate`. Updates `rate` if the
    /// call succeeds.
    ///
    /// # Errors
    /// Returns [`Error::DBusError`] or [`Error::DBusFdoError`] if the D-Bus call fails.
    pub async fn set_rate(&self, value: f64) -> Result<()> {
        self.inner.player_proxy().await?.set_rate(value).await?;
        self.inner.properties.rate.set(value);
        Ok(())
    }

    /// Enables or disables shuffle.
    ///
    /// Updates `shuffle` if the call succeeds.
    ///
    /// # Errors
    /// Returns [`Error::DBusError`] or [`Error::DBusFdoError`] if the D-Bus call fails.
    pub async fn set_shuffle(&self, value: bool) -> Result<()> {
        self.inner.player_proxy().await?.set_shuffle(value).await?;
        self.inner.properties.shuffle.set(value);
        Ok(())
    }

    /// Sets the volume level.
    ///
    /// Negative values are treated as `0.0`. Updates `volume` if the call succeeds.
    ///
    /// # Errors
    /// Returns [`Error::DBusError`] or [`Error::DBusFdoError`] if the D-Bus call fails.
    pub async fn set_volume(&self, value: f64) -> Result<()> {
        self.inner.player_proxy().await?.set_volume(value).await?;

        self.inner.properties.volume.set(value);
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use std::{collections::HashMap, fs, time::Duration};

    use zbus::object_server::InterfaceRef;

    use super::*;
    use crate::test_utils::*;

    async fn init_handle_with_cache(name: String, cache_dir: Option<PathBuf>) -> PlayerHandle {
        let player = Player::new(name, cache_dir).await.unwrap();
        PlayerHandle::new(Arc::new(player))
    }

    async fn init_handle(name: String) -> PlayerHandle {
        init_handle_with_cache(name, None).await
    }

    async fn get_media_iface_ref(connection: &zbus::Connection) -> InterfaceRef<TestMediaPlayer2> {
        connection
            .object_server()
            .interface::<_, TestMediaPlayer2>("/org/mpris/MediaPlayer2")
            .await
            .unwrap()
    }

    async fn get_player_iface_ref(connection: &zbus::Connection) -> InterfaceRef<TestPlayer> {
        connection
            .object_server()
            .interface::<_, TestPlayer>("/org/mpris/MediaPlayer2")
            .await
            .unwrap()
    }

    #[tokio::test]
    async fn test_properties_changed() {
        let ctx = TestContext::new().await;
        let player_info = ctx.run_player().await;

        let handle = init_handle(player_info.name).await;
        let iface_ref = get_media_iface_ref(&player_info.connection).await;

        {
            let iface = iface_ref.get_mut().await;

            player_info.media_player_data.lock().unwrap().can_quit = true;
            assert_eq!(iface.can_quit(), true);
        }

        iface_ref
            .get_mut()
            .await
            .can_quit_changed(iface_ref.signal_emitter())
            .await
            .unwrap();

        tokio::time::sleep(Duration::from_secs(1)).await;
        handle.properties.can_quit.read(|v| assert_eq!(*v, true))
    }

    #[tokio::test]
    async fn test_metadata_parse() {
        let ctx = TestContext::new().await;
        let player_info = ctx.run_player().await;

        let handle = init_handle(player_info.name).await;

        let iface_ref = get_player_iface_ref(&player_info.connection).await;

        {
            let mut metadata: HashMap<String, String> = HashMap::new();
            metadata.insert("mpris:artUrl".into(), "blah/blah".into());
            metadata.insert("xesam:trackNumber".into(), "10".into());

            player_info.player_data.lock().unwrap().metadata = metadata;
        }

        let iface = iface_ref.get().await;
        iface
            .metadata_changed(iface_ref.signal_emitter())
            .await
            .unwrap();

        tokio::time::sleep(Duration::from_secs(1)).await;

        handle.properties.metadata.read(|v| {
            assert_eq!(v.art_url.as_ref().unwrap(), "blah/blah");
            assert_eq!(v.track_number.unwrap(), 10);
        });
    }

    #[tokio::test]
    async fn test_art_cover_caching() {
        let ctx = TestContext::new().await;

        let player_info = ctx.run_player().await;

        let iface_ref = get_player_iface_ref(&player_info.connection).await;

        {
            let mut metadata: HashMap<String, String> = HashMap::new();
            metadata.insert("mpris:artUrl".into(), "https://picsum.photos/200".into());
            player_info.player_data.lock().unwrap().metadata = metadata;
        }

        let iface = iface_ref.get().await;
        iface
            .metadata_changed(iface_ref.signal_emitter())
            .await
            .unwrap();

        let handle =
            init_handle_with_cache(player_info.name, Some(ctx.temp_dir.path().to_path_buf())).await;

        tokio::time::sleep(Duration::from_secs(2)).await;
        handle.properties.cached_cover_art.read(|v| {
            v.as_ref().unwrap();
        });

        // local file caching

        {
            let local_file = ctx.temp_dir.path().to_path_buf().join("my-art.png");
            fs::write(&local_file, "heh").unwrap();

            let mut metadata: HashMap<String, String> = HashMap::new();
            metadata.insert(
                "mpris:artUrl".into(),
                format!("file://{}", local_file.into_string().unwrap()),
            );
            player_info.player_data.lock().unwrap().metadata = metadata;
        }

        iface
            .metadata_changed(iface_ref.signal_emitter())
            .await
            .unwrap();

        tokio::time::sleep(Duration::from_secs(1)).await;
        handle.properties.cached_cover_art.read(|v| {
            let string = fs::read_to_string(v.as_ref().unwrap()).unwrap();
            assert_eq!(string, "heh");
        });
    }

    #[tokio::test]
    async fn test_position() {
        let ctx = TestContext::new().await;

        let player_info = ctx.run_player().await;
        {
            let mut guard = player_info.player_data.lock().unwrap();
            guard.playback_status = String::from("Playing");
            guard.rate = 1.0;
        }

        let handle = init_handle(player_info.name.clone()).await;

        tokio::time::sleep(Duration::from_secs(2)).await;
        handle.properties.position.read(|v| assert!(*v > 1));
    }
}
