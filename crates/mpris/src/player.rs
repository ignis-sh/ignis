use crate::dbus::{MediaPlayer2Proxy, PlayerProxy};
use crate::private_prelude::*;
use futures_util::StreamExt;
use ignis_core::property::{Property, PropertyOwner};
use std::collections::HashMap;
use std::path::PathBuf;
use std::sync::Arc;
use url::Url;
use uuid::Uuid;
use zbus::Connection;

// TODO:
// Sync properties
// Cache cover art
// add signals

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

struct PlayerOwnerProperties {
    can_quit: PropertyOwner<bool>,
    can_raise: PropertyOwner<bool>,
    can_set_fullscreen: PropertyOwner<bool>,
    desktop_entry: PropertyOwner<String>,
    fullscreen: PropertyOwner<bool>,
    has_track_list: PropertyOwner<bool>,
    identity: PropertyOwner<String>,
    supported_mime_types: PropertyOwner<Vec<String>>,
    supported_uri_schemes: PropertyOwner<Vec<String>>,

    can_control: PropertyOwner<bool>,
    can_go_next: PropertyOwner<bool>,
    can_go_previous: PropertyOwner<bool>,
    can_pause: PropertyOwner<bool>,
    can_play: PropertyOwner<bool>,
    can_seek: PropertyOwner<bool>,
    loop_status: PropertyOwner<LoopStatus>,
    maximum_rate: PropertyOwner<f64>,
    minimum_rate: PropertyOwner<f64>,
    playback_status: PropertyOwner<PlaybackStatus>,
    rate: PropertyOwner<f64>,
    shuffle: PropertyOwner<bool>,
    volume: PropertyOwner<f64>,
    metadata: PropertyOwner<Metadata>,

    cached_art_cover: PropertyOwner<Option<PathBuf>>,
}

pub(crate) struct Player {
    name: String,
    connection: Connection,
    properties: Arc<PlayerOwnerProperties>,
}

impl Player {
    pub(crate) async fn new(name: String, cache_dir: Option<PathBuf>) -> Result<Self> {
        let connection = Connection::session().await?;

        let media_player_proxy = media_player_proxy(&connection, &name).await?;
        let player_proxy = player_proxy(&connection, &name).await?;

        let metadata: Metadata = player_proxy.metadata().await.unwrap_or_default().into();

        let cached_art_cover_dir =
            cache_dir.and_then(|v| file_utils::get_cached_art_cover_dir(v).ok());

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
            cached_art_cover: PropertyOwner::new(
                Self::cache_art_cover(cached_art_cover_dir.clone(), &metadata).await,
            ),
            metadata: PropertyOwner::new(metadata),
        });

        let obj = Player {
            name: name.clone(),
            connection: connection.clone(),
            properties: properties.clone(),
        };

        let (ready_tx, ready_rx) = tokio::sync::oneshot::channel();

        tokio::spawn(async move {
            if let Err(e) = Self::listen_properties_change(
                connection,
                name,
                cached_art_cover_dir,
                properties,
                ready_tx,
            )
            .await
            {
                eprintln!("Property listener failed: {e:?}");
            }
        });

        ready_rx.await?;

        Ok(obj)
    }

    async fn listen_properties_change(
        connection: Connection,
        name: String,
        cached_art_cover_dir: Option<PathBuf>,
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
                                "SupportedUriTypes" => properties
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
                                        cached_art_cover_dir.clone(),
                                        &metadata,
                                    )
                                    .await
                                    {
                                        properties.cached_art_cover.set(Some(path));
                                    }

                                    properties.metadata.set(metadata);
                                }

                                "MinimumRate" => properties
                                    .minimum_rate
                                    .set(f64::try_from(value).unwrap_or_default()),
                                "PlaybackStatus" => properties
                                    .playback_status
                                    .set(String::try_from(value).unwrap_or_default().into()),
                                // "Position" => properties
                                //     .position
                                //     .set(Vec::try_from(value).unwrap_or_default()),
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
        cached_art_cover_dir: Option<PathBuf>,
        metadata: &Metadata,
    ) -> Option<PathBuf> {
        let url = Url::parse(&metadata.art_url.clone()?).ok()?;
        let filename = Uuid::new_v5(&Uuid::NAMESPACE_URL, url.as_str().as_bytes());

        let destination = cached_art_cover_dir?.join(filename.to_string());

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
}

pub struct PlayerHandleProperties {
    pub can_quit: Property<bool>,
    pub can_raise: Property<bool>,
    pub can_set_fullscreen: Property<bool>,
    pub desktop_entry: Property<String>,
    pub fullscreen: Property<bool>,
    pub has_track_list: Property<bool>,
    pub identity: Property<String>,
    pub supported_mime_types: Property<Vec<String>>,
    pub supported_uri_schemes: Property<Vec<String>>,

    pub can_control: Property<bool>,
    pub can_go_next: Property<bool>,
    pub can_go_previous: Property<bool>,
    pub can_pause: Property<bool>,
    pub can_play: Property<bool>,
    pub can_seek: Property<bool>,
    pub loop_status: Property<LoopStatus>,
    pub maximum_rate: Property<f64>,
    pub minimum_rate: Property<f64>,
    pub playback_status: Property<PlaybackStatus>,
    pub rate: Property<f64>,
    pub shuffle: Property<bool>,
    pub volume: Property<f64>,
    pub metadata: Property<Metadata>,

    pub cached_art_cover: Property<Option<PathBuf>>,
}

impl PlayerHandleProperties {
    fn new(inner: &Player) -> Self {
        Self {
            can_quit: inner.properties.can_quit.return_property(),
            can_raise: inner.properties.can_raise.return_property(),
            can_set_fullscreen: inner.properties.can_set_fullscreen.return_property(),
            desktop_entry: inner.properties.desktop_entry.return_property(),
            fullscreen: inner.properties.fullscreen.return_property(),
            has_track_list: inner.properties.has_track_list.return_property(),
            identity: inner.properties.identity.return_property(),
            supported_mime_types: inner.properties.supported_mime_types.return_property(),
            supported_uri_schemes: inner.properties.supported_uri_schemes.return_property(),

            can_control: inner.properties.can_control.return_property(),
            can_go_next: inner.properties.can_go_next.return_property(),
            can_go_previous: inner.properties.can_go_previous.return_property(),
            can_pause: inner.properties.can_pause.return_property(),
            can_play: inner.properties.can_play.return_property(),
            can_seek: inner.properties.can_seek.return_property(),
            loop_status: inner.properties.loop_status.return_property(),
            maximum_rate: inner.properties.maximum_rate.return_property(),
            minimum_rate: inner.properties.minimum_rate.return_property(),
            playback_status: inner.properties.playback_status.return_property(),
            rate: inner.properties.rate.return_property(),
            shuffle: inner.properties.shuffle.return_property(),
            volume: inner.properties.volume.return_property(),
            metadata: inner.properties.metadata.return_property(),
            cached_art_cover: inner.properties.cached_art_cover.return_property(),
        }
    }
}

pub struct PlayerHandle {
    pub(crate) inner: Arc<Player>,
    pub properties: PlayerHandleProperties,
}

impl PlayerHandle {
    pub(crate) fn new(inner: Arc<Player>) -> Self {
        Self {
            inner: inner.clone(),
            properties: PlayerHandleProperties::new(&inner),
        }
    }

    pub async fn quit(&self) -> Result<()> {
        self.inner.media_player_proxy().await?.quit().await?;
        Ok(())
    }

    pub async fn raise(&self) -> Result<()> {
        self.inner.media_player_proxy().await?.raise().await?;
        Ok(())
    }

    //
    // MediaPlayer2.Player
    //

    pub async fn next(&self) -> Result<()> {
        self.inner.player_proxy().await?.next().await?;
        Ok(())
    }

    pub async fn open_uri(&self, uri: &str) -> Result<()> {
        self.inner.player_proxy().await?.open_uri(uri).await?;
        Ok(())
    }

    pub async fn pause(&self) -> Result<()> {
        self.inner.player_proxy().await?.pause().await?;
        Ok(())
    }

    pub async fn play(&self) -> Result<()> {
        self.inner.player_proxy().await?.play().await?;
        Ok(())
    }

    pub async fn play_pause(&self) -> Result<()> {
        self.inner.player_proxy().await?.play_pause().await?;
        Ok(())
    }

    pub async fn previous(&self) -> Result<()> {
        self.inner.player_proxy().await?.previous().await?;
        Ok(())
    }

    pub async fn seek(&self, offset: i64) -> Result<()> {
        self.inner.player_proxy().await?.seek(offset).await?;
        Ok(())
    }

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

    pub async fn stop(&self) -> Result<()> {
        self.inner.player_proxy().await?.stop().await?;

        Ok(())
    }

    // /// Seeked signal
    // #[zbus(signal)]
    // fn seeked(&self, position: i64) -> zbus::Result<()>;

    pub async fn set_loop_status(&self, value: LoopStatus) -> Result<()> {
        self.inner
            .player_proxy()
            .await?
            .set_loop_status(&value.to_string())
            .await?;

        self.inner.properties.loop_status.set(value);

        Ok(())
    }

    // pub fn position(&self) -> i64 {
    //     self.inner.player_data.read().unwrap().posi
    // }

    pub async fn set_rate(&self, value: f64) -> Result<()> {
        self.inner.player_proxy().await?.set_rate(value).await?;
        self.inner.properties.rate.set(value);
        Ok(())
    }

    pub async fn set_shuffle(&self, value: bool) -> Result<()> {
        self.inner.player_proxy().await?.set_shuffle(value).await?;
        self.inner.properties.shuffle.set(value);
        Ok(())
    }

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
        handle.properties.cached_art_cover.read(|v| {
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
        handle.properties.cached_art_cover.read(|v| {
            let string = fs::read_to_string(v.as_ref().unwrap()).unwrap();
            assert_eq!(string, "heh");
        });
    }
}
