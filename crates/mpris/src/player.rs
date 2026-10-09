use crate::dbus::{MediaPlayer2Proxy, PlayerProxy};
use crate::private_prelude::*;
use futures_util::StreamExt;
use std::sync::{Arc, RwLock};
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
    Ok(PlayerProxy::builder(&connection)
        .destination(name)
        .unwrap()
        .build()
        .await?)
}
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

struct PlayerData {
    can_control: bool,
    can_go_next: bool,
    can_go_previous: bool,
    can_pause: bool,
    can_play: bool,
    can_seek: bool,
    loop_status: LoopStatus,
    maximum_rate: f64,
    minimum_rate: f64,
    playback_status: PlaybackStatus,
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

        let media_player_data = Arc::new(RwLock::new(
            Self::get_media_player_data(&media_player_proxy(&connection, &name).await?).await,
        ));
        let player_data = Arc::new(RwLock::new(
            Self::get_player_data(&player_proxy(&connection, &name).await?).await,
        ));

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

        let media_player_proxy = media_player_proxy(&connection, &name).await?;
        let player_proxy = player_proxy(&connection, &name).await?;
        let mut stream = proxy.receive_properties_changed().await?;

        let _ = ready_tx.send(());

        while let Some(message) = stream.next().await {
            if let Some(args) = message.args().ok() {
                match args.interface_name.as_str() {
                    "org.mpris.MediaPlayer2" => {
                        *media_player_data.write().unwrap() =
                            Self::get_media_player_data(&media_player_proxy).await;
                    }

                    "org.mpris.MediaPlayer2.Player" => {
                        *player_data.write().unwrap() = Self::get_player_data(&player_proxy).await;
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

    async fn get_player_data(proxy: &PlayerProxy<'_>) -> PlayerData {
        let (
            can_control,
            can_go_next,
            can_go_previous,
            can_pause,
            can_play,
            can_seek,
            loop_status,
            maximum_rate,
            minimum_rate,
            playback_status,
            rate,
            shuffle,
            volume,
        ) = futures::join!(
            proxy.can_control(),
            proxy.can_go_next(),
            proxy.can_go_previous(),
            proxy.can_pause(),
            proxy.can_play(),
            proxy.can_seek(),
            proxy.loop_status(),
            proxy.maximum_rate(),
            proxy.minimum_rate(),
            proxy.playback_status(),
            proxy.rate(),
            proxy.shuffle(),
            proxy.volume()
        );

        PlayerData {
            can_control: can_control.unwrap_or_default(),
            can_go_next: can_go_next.unwrap_or_default(),
            can_go_previous: can_go_previous.unwrap_or_default(),
            can_pause: can_pause.unwrap_or_default(),
            can_play: can_play.unwrap_or_default(),
            can_seek: can_seek.unwrap_or_default(),
            loop_status: loop_status.unwrap_or_default().into(),
            maximum_rate: maximum_rate.unwrap_or_default(),
            minimum_rate: minimum_rate.unwrap_or_default(),
            playback_status: playback_status.unwrap_or_default().into(),
            rate: rate.unwrap_or_default(),
            shuffle: shuffle.unwrap_or_default(),
            volume: volume.unwrap_or_default(),
        }
    }

    async fn media_player_proxy(&self) -> Result<MediaPlayer2Proxy<'_>> {
        media_player_proxy(&self.connection, &self.name).await
    }

    async fn player_proxy(&self) -> Result<PlayerProxy<'_>> {
        player_proxy(&self.connection, &self.name).await
    }
}

pub struct PlayerHandle {
    pub(crate) inner: Arc<Player>,
}

impl PlayerHandle {
    //
    pub fn can_quit(&self) -> bool {
        self.inner.media_player_data.read().unwrap().can_quit
    }

    pub fn can_raise(&self) -> bool {
        self.inner.media_player_data.read().unwrap().can_raise
    }

    pub fn can_set_fullscreen(&self) -> bool {
        self.inner
            .media_player_data
            .read()
            .unwrap()
            .can_set_fullscreen
    }

    pub fn desktop_entry(&self) -> String {
        self.inner
            .media_player_data
            .read()
            .unwrap()
            .desktop_entry
            .clone()
    }

    pub fn fullscreen(&self) -> bool {
        self.inner.media_player_data.read().unwrap().fullscreen
    }

    pub async fn set_fullscreen(&self, value: bool) -> Result<()> {
        let proxy = self.inner.media_player_proxy().await?;
        proxy.set_fullscreen(value).await?;

        Ok(())
    }

    pub fn has_track_list(&self) -> bool {
        self.inner.media_player_data.read().unwrap().has_track_list
    }

    pub fn identity(&self) -> String {
        self.inner
            .media_player_data
            .read()
            .unwrap()
            .identity
            .clone()
    }

    pub fn supported_mime_types(&self) -> Vec<String> {
        self.inner
            .media_player_data
            .read()
            .unwrap()
            .supported_mime_types
            .clone()
    }

    pub fn supported_uri_schemes(&self) -> Vec<String> {
        self.inner
            .media_player_data
            .read()
            .unwrap()
            .supported_uri_schemes
            .clone()
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

    pub fn can_control(&self) -> bool {
        self.inner.player_data.read().unwrap().can_control
    }

    pub fn can_go_next(&self) -> bool {
        self.inner.player_data.read().unwrap().can_go_next
    }

    pub fn can_go_previous(&self) -> bool {
        self.inner.player_data.read().unwrap().can_go_previous
    }

    pub fn can_pause(&self) -> bool {
        self.inner.player_data.read().unwrap().can_pause
    }

    pub fn can_play(&self) -> bool {
        self.inner.player_data.read().unwrap().can_play
    }

    pub fn can_seek(&self) -> bool {
        self.inner.player_data.read().unwrap().can_seek
    }

    pub fn loop_status(&self) -> LoopStatus {
        self.inner.player_data.read().unwrap().loop_status
    }

    pub async fn set_loop_status(&self, value: LoopStatus) -> Result<()> {
        self.inner
            .player_proxy()
            .await?
            .set_loop_status(&value.to_string())
            .await?;

        Ok(())
    }

    pub fn maximum_rate(&self) -> f64 {
        self.inner.player_data.read().unwrap().maximum_rate
    }

    // fn metadata(
    //     &self,
    // ) -> zbus::Result<std::collections::HashMap<String, zbus::zvariant::OwnedValue>>;

    pub fn minimum_rate(&self) -> f64 {
        self.inner.player_data.read().unwrap().minimum_rate
    }

    pub fn playback_status(&self) -> PlaybackStatus {
        self.inner.player_data.read().unwrap().playback_status
    }

    // pub fn position(&self) -> i64 {
    //     self.inner.player_data.read().unwrap().posi
    // }

    pub fn rate(&self) -> f64 {
        self.inner.player_data.read().unwrap().rate
    }

    pub async fn set_rate(&self, value: f64) -> Result<()> {
        self.inner.player_proxy().await?.set_rate(value).await?;
        Ok(())
    }

    pub fn shuffle(&self) -> bool {
        self.inner.player_data.read().unwrap().shuffle
    }

    pub async fn set_shuffle(&self, value: bool) -> Result<()> {
        self.inner.player_proxy().await?.set_shuffle(value).await?;
        Ok(())
    }

    pub fn volume(&self) -> f64 {
        self.inner.player_data.read().unwrap().volume
    }

    pub async fn set_volume(&self, value: f64) -> Result<()> {
        self.inner.player_proxy().await?.set_volume(value).await?;
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
