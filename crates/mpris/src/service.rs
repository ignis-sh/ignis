use crate::private_prelude::*;
use futures_util::stream::StreamExt;
use ignis_events::Event;
use std::sync::Mutex;
use std::{collections::HashMap, sync::Arc};
use zbus::Connection;

struct MprisServiceInner {
    pub(crate) players: Mutex<HashMap<String, Arc<Player>>>,
    player_added: Event<PlayerHandle>,
    player_removed: Event<PlayerHandle>,
}

#[derive(Clone)]
pub struct MprisService {
    inner: Arc<MprisServiceInner>,
}

impl MprisService {
    pub fn new() -> Self {
        Self {
            inner: Arc::new(MprisServiceInner {
                players: Mutex::new(HashMap::new()),
                player_added: Event::<PlayerHandle>::new(),
                player_removed: Event::<PlayerHandle>::new(),
            }),
        }
    }

    pub async fn run(&self) -> Result<()> {
        let connection = Connection::session().await?;
        let proxy = zbus::fdo::DBusProxy::new(&connection).await?;

        for name in proxy.list_names().await? {
            if name.starts_with("org.mpris.MediaPlayer2")
                && !self
                    .inner
                    .players
                    .lock()
                    .unwrap()
                    .contains_key(&name.to_string())
            {
                self.init_player(&name).await;
            }
        }

        let service = self.clone();
        tokio::spawn(async move { service.listen_dbus_changes(proxy).await });

        Ok(())
    }

    async fn listen_dbus_changes(&self, proxy: zbus::fdo::DBusProxy<'_>) -> Result<()> {
        while let Some(event) = proxy.receive_name_owner_changed().await?.next().await {
            if let Some(args) = event.args().ok()
                && let name = args.name.to_string()
                && name.starts_with("org.mpris.MediaPlayer2")
            {
                match (&**args.old_owner(), &**args.new_owner()) {
                    (None, Some(_new_owner)) => {
                        // Name acquired
                        if let Some(handle) = self.init_player(&name).await {
                            self.inner.player_added.emit(&handle);
                        }
                    }

                    (Some(_old_owner), None) => {
                        // Name lost
                        if let Some(handle) = self.remove_player(&name) {
                            self.inner.player_removed.emit(&handle);
                        }
                    }

                    (Some(_), Some(_)) => {}

                    (None, None) => {
                        // Should not normally happen for NameOwnerChanged
                    }
                }
            }
        }
        Ok(())
    }

    fn remove_player(&self, name: &str) -> Option<PlayerHandle> {
        Some(PlayerHandle {
            inner: self.inner.players.lock().unwrap().remove(name)?,
        })
    }

    async fn init_player(&self, name: &str) -> Option<PlayerHandle> {
        let player = Player::new(name.to_string()).await.ok()?;
        let shared = Arc::new(player);
        let clone = shared.clone();
        self.inner
            .players
            .lock()
            .unwrap()
            .insert(name.to_string(), shared);

        Some(PlayerHandle { inner: clone })
    }

    pub fn players(&self) -> Vec<PlayerHandle> {
        self.inner
            .players
            .lock()
            .unwrap()
            .values()
            .map(|p| PlayerHandle { inner: p.clone() })
            .collect()
    }
}

#[cfg(test)]
mod tests {

    use std::time::Duration;

    use super::*;
    use fake::{Dummy, Fake, Faker};
    use zbus::{conn::Builder, interface, object_server::SignalEmitter};

    #[derive(Dummy)]
    struct TestMediaPlayer2 {
        can_quit: bool,
        can_raise: bool,
        can_set_fullscreen: bool,
        desktop_entry: String,
        fullscreen: Mutex<bool>,
        has_track_list: bool,
        identity: String,
        supported_mime_types: Vec<String>,
        supported_uri_schemes: Vec<String>,
    }

    #[interface(name = "org.mpris.MediaPlayer2")]
    impl TestMediaPlayer2 {
        fn quit(&self) {}
        fn raise(&self) {}

        #[zbus(property)]
        fn can_quit(&self) -> bool {
            self.can_quit
        }

        #[zbus(property)]
        fn can_raise(&self) -> bool {
            self.can_raise
        }

        #[zbus(property)]
        fn can_set_fullscreen(&self) -> bool {
            self.can_set_fullscreen
        }

        #[zbus(property)]
        fn desktop_entry(&self) -> String {
            self.desktop_entry.clone()
        }

        #[zbus(property)]
        fn fullscreen(&self) -> bool {
            self.can_raise
        }
        #[zbus(property)]
        fn set_fullscreen(&self, value: bool) {
            *self.fullscreen.lock().unwrap() = value;
        }

        #[zbus(property)]
        fn has_track_list(&self) -> bool {
            self.has_track_list
        }

        #[zbus(property)]
        fn identity(&self) -> String {
            self.identity.clone()
        }

        #[zbus(property)]
        fn supported_mime_types(&self) -> Vec<String> {
            self.supported_mime_types.clone()
        }

        #[zbus(property)]
        fn supported_uri_schemes(&self) -> Vec<String> {
            self.supported_uri_schemes.clone()
        }
    }

    #[derive(Dummy)]
    struct TestPlayer {
        can_control: bool,
        can_go_next: bool,
        can_go_previous: bool,
        can_pause: bool,
        can_play: bool,
        can_seek: bool,
        loop_status: Mutex<String>,
        maximum_rate: f64,
        minimum_rate: f64,
        metadata: HashMap<String, String>,
        playback_status: String,
        position: i64,
        rate: Mutex<f64>,
        shuffle: Mutex<bool>,
        volume: Mutex<f64>,
    }

    #[interface(name = "org.mpris.MediaPlayer2.Player")]
    impl TestPlayer {
        fn next(&self) {}
        fn open_uri(&self, _uri: &str) {}
        fn pause(&self) {}
        fn play(&self) {}
        fn play_pause(&self) {}
        fn previous(&self) {}
        fn seek(&self, _offset: i64) {}
        fn set_position(&self, _track_id: String, _position: i64) {}
        fn stop(&self) {}

        #[zbus(signal)]
        async fn seeked(&self, _emitter: &SignalEmitter<'_>, position: i64) -> zbus::Result<()>;

        #[zbus(property)]
        fn can_control(&self) -> bool {
            self.can_control
        }
        #[zbus(property)]
        fn can_go_next(&self) -> bool {
            self.can_go_next
        }

        #[zbus(property)]
        fn can_go_previous(&self) -> bool {
            self.can_go_previous
        }

        #[zbus(property)]
        fn can_pause(&self) -> bool {
            self.can_pause
        }

        #[zbus(property)]
        fn can_play(&self) -> bool {
            self.can_play
        }

        #[zbus(property)]
        fn can_seek(&self) -> bool {
            self.can_seek
        }

        #[zbus(property)]
        fn loop_status(&self) -> String {
            self.loop_status.lock().unwrap().clone()
        }

        #[zbus(property)]
        fn set_loop_status(&self, value: &str) {
            *self.loop_status.lock().unwrap() = String::from(value);
        }

        #[zbus(property)]
        fn maximum_rate(&self) -> f64 {
            self.maximum_rate
        }

        #[zbus(property)]
        fn metadata(&self) -> std::collections::HashMap<String, String> {
            self.metadata.clone()
        }

        #[zbus(property)]
        fn minimum_rate(&self) -> f64 {
            self.minimum_rate
        }

        #[zbus(property)]
        fn playback_status(&self) -> String {
            self.playback_status.clone()
        }

        #[zbus(property)]
        fn position(&self) -> i64 {
            self.position
        }

        #[zbus(property)]
        fn rate(&self) -> f64 {
            *self.rate.lock().unwrap()
        }
        #[zbus(property)]
        fn set_rate(&self, value: f64) {
            *self.rate.lock().unwrap() = value;
        }

        #[zbus(property)]
        fn shuffle(&self) -> bool {
            *self.shuffle.lock().unwrap()
        }
        #[zbus(property)]
        fn set_shuffle(&self, value: bool) {
            *self.shuffle.lock().unwrap() = value;
        }

        #[zbus(property)]
        fn volume(&self) -> f64 {
            *self.volume.lock().unwrap()
        }

        #[zbus(property)]
        fn set_volume(&self, value: f64) {
            *self.volume.lock().unwrap() = value;
        }
    }

    struct TestContext {
        conns: Mutex<HashMap<String, zbus::Connection>>,
    }

    impl TestContext {
        async fn new() -> Self {
            Self {
                conns: Mutex::new(HashMap::new()),
            }
        }

        async fn run_player(&self) -> String {
            let name: String = fake::faker::lorem::en::Word().fake();
            let media_player: TestMediaPlayer2 = Faker.fake();
            let player: TestPlayer = Faker.fake();

            let well_known_name = format!("org.mpris.MediaPlayer2.{}", name);

            self.conns.lock().unwrap().insert(
                well_known_name.clone(),
                Builder::session()
                    .unwrap()
                    .name(well_known_name.clone())
                    .unwrap()
                    .serve_at("/org/mpris/MediaPlayer2", media_player)
                    .unwrap()
                    .serve_at("/org/mpris/MediaPlayer2", player)
                    .unwrap()
                    .build()
                    .await
                    .unwrap(),
            );

            well_known_name
        }

        async fn drop_player(&self, name: &str) {
            let conn = self.conns.lock().unwrap().remove(name).unwrap();
            conn.release_name(name).await.unwrap();
        }
    }

    #[tokio::test]
    async fn test_bus_scanning() {
        let ctx = TestContext::new().await;
        let n: usize = (0..=5).fake();

        for _ in 0..n {
            ctx.run_player().await;
        }

        let service = MprisService::new();
        service.run().await.unwrap();

        assert_eq!(service.players().len(), n);
    }

    #[tokio::test]
    async fn test_player_detection() {
        let ctx = TestContext::new().await;
        let n: usize = (0..=5).fake();

        let service = MprisService::new();
        service.run().await.unwrap();

        for _ in 0..n {
            ctx.run_player().await;
        }

        tokio::time::sleep(Duration::from_secs(1)).await;

        assert_eq!(service.players().len(), n);
    }

    #[tokio::test]
    async fn test_player_drop() {
        let ctx = TestContext::new().await;
        let service = MprisService::new();
        service.run().await.unwrap();

        let name = ctx.run_player().await;

        tokio::time::sleep(Duration::from_secs(1)).await;
        assert_eq!(service.players().len(), 1);

        ctx.drop_player(&name).await;

        tokio::time::sleep(Duration::from_secs(1)).await;
        assert_eq!(service.players().len(), 0);
    }
}
