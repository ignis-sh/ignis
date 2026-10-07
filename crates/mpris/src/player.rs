use crate::dbus::{MediaPlayer2Proxy, PlayerProxy};
use crate::private_prelude::*;
use futures_util::StreamExt;
use std::sync::{Arc, Mutex, RwLock};
use zbus::Connection;

// TODO:
// Sync properties
// Cache cover art
// add signals

#[derive(Default)]
struct MediaPlayerData {
    can_quit: bool,
    can_raise: bool,
    can_set_fullscreen: bool,
    desktop_entry: String,
    fullscreen: bool,
    has_track_list: bool,
    identity: String,
    supported_mime_types: Vec<String>,
    supported_uri_schemes: Vec<String>,
}

#[derive(Default)]
struct PlayerData {
    can_control: bool,
    can_go_next: bool,
    can_go_previous: bool,
    can_pause: bool,
    can_play: bool,
    can_seek: bool,
    loop_status: String, // TODO: make enum
    maximum_rate: f64,
    minimum_rate: f64,
    playback_status: String, // TODO: make enum
    rate: f64,
    shuffle: bool,
    volume: f64,
}

pub(crate) struct Player {
    name: String,
    connection: Connection,
    media_player_data: Arc<RwLock<MediaPlayerData>>,
    player_data: Arc<RwLock<PlayerData>>,
}

impl Player {
    pub(crate) async fn new(name: String) -> Result<Self> {
        let connection = Connection::session().await?;

        let media_player_data = Arc::new(RwLock::new(MediaPlayerData::default()));
        let player_data = Arc::new(RwLock::new(PlayerData::default()));

        let obj = Player {
            name: name.clone(),
            connection: connection.clone(),
            media_player_data: media_player_data.clone(),
            player_data: player_data.clone(),
        };

        let (ready_tx, ready_rx) = tokio::sync::oneshot::channel();

        tokio::spawn(async move {
            if let Err(e) = Self::listen_properties_change(
                connection,
                name,
                media_player_data,
                player_data,
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
        media_player_data: Arc<RwLock<MediaPlayerData>>,
        player_data: Arc<RwLock<PlayerData>>,
        ready_tx: tokio::sync::oneshot::Sender<()>,
    ) -> Result<()> {
        let proxy =
            zbus::fdo::PropertiesProxy::new(&connection, name.clone(), "/org/mpris/MediaPlayer2")
                .await?;

        let media_player_proxy = MediaPlayer2Proxy::builder(&connection)
            .destination(name)
            .unwrap()
            .build()
            .await?;
        let mut stream = proxy.receive_properties_changed().await?;

        let _ = ready_tx.send(());

        while let Some(message) = stream.next().await {
            if let Some(args) = message.args().ok() {
                match args.interface_name.as_str() {
                    "org.mpris.MediaPlayer2" => {
                        *media_player_data.write().unwrap() =
                            Self::get_media_player_data(&media_player_proxy).await;
                    }
                    _ => {}
                }
            }
        }

        Ok(())
    }

    async fn get_media_player_data(proxy: &MediaPlayer2Proxy<'_>) -> MediaPlayerData {
        let (
            can_quit,
            can_raise,
            can_set_fullscreen,
            desktop_entry,
            fullscreen,
            has_track_list,
            identity,
            supported_mime_types,
            supported_uri_schemes,
        ) = futures::join!(
            proxy.can_quit(),
            proxy.can_raise(),
            proxy.can_set_fullscreen(),
            proxy.desktop_entry(),
            proxy.fullscreen(),
            proxy.has_track_list(),
            proxy.identity(),
            proxy.supported_mime_types(),
            proxy.supported_uri_schemes(),
        );

        MediaPlayerData {
            can_quit: can_quit.unwrap_or_default(),
            can_raise: can_raise.unwrap_or_default(),
            can_set_fullscreen: can_set_fullscreen.unwrap_or_default(),
            desktop_entry: desktop_entry.unwrap_or_default(),
            fullscreen: fullscreen.unwrap_or_default(),
            has_track_list: has_track_list.unwrap_or_default(),
            identity: identity.unwrap_or_default(),
            supported_mime_types: supported_mime_types.unwrap_or_default(),
            supported_uri_schemes: supported_uri_schemes.unwrap_or_default(),
        }
    }
    async fn media_player_proxy(&self) -> Result<MediaPlayer2Proxy<'_>> {
        Ok(MediaPlayer2Proxy::builder(&self.connection)
            .destination(self.name.clone())
            .unwrap()
            .build()
            .await?)
    }

    async fn player_proxy(&self) -> Result<PlayerProxy<'_>> {
        Ok(PlayerProxy::builder(&self.connection)
            .destination(self.name.clone())
            .unwrap()
            .build()
            .await?)
    }
}

pub struct PlayerHandle {
    pub(crate) inner: Arc<Player>,
}

impl PlayerHandle {
    pub fn can_quit(&self) -> bool {
        self.inner.media_player_data.read().unwrap().can_quit
    }
    pub async fn next(&self) -> Result<()> {
        self.inner.player_proxy().await?.next().await?;
        Ok(())
    }

    /// Quit method
    pub async fn quit(&self) -> Result<()> {
        self.inner.media_player_proxy().await?.quit().await?;
        Ok(())
    }

    /// Raise method
    pub async fn raise(&self) -> Result<()> {
        self.inner.media_player_proxy().await?.raise().await?;
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use std::time::Duration;

    use super::*;
    use crate::test_utils::*;

    #[tokio::test]
    async fn test_properties_changed() {
        let ctx = TestContext::new().await;
        let player_info = ctx.run_player().await;
        let player = Player::new(player_info.name).await.unwrap();
        let player_handle = PlayerHandle {
            inner: Arc::new(player),
        };

        let iface_ref = player_info
            .connection
            .object_server()
            .interface::<_, TestMediaPlayer2>("/org/mpris/MediaPlayer2")
            .await
            .unwrap();

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
        assert_eq!(player_handle.can_quit(), true);
    }
}
