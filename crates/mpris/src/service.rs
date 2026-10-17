use crate::private_prelude::*;
use futures_util::stream::StreamExt;
use ignis_events::Event;
use std::path::PathBuf;
use std::sync::Mutex;
use std::{collections::HashMap, sync::Arc};
use zbus::Connection;

struct MprisServiceInner {
    pub(crate) players: Mutex<HashMap<String, Arc<Player>>>,
    player_added: Event<PlayerHandle>,
    player_removed: Event<PlayerHandle>,
    cache_dir: Option<PathBuf>,
}

#[derive(Clone)]
pub struct MprisService {
    inner: Arc<MprisServiceInner>,
}

impl Default for MprisService {
    fn default() -> Self {
        Self::new()
    }
}

impl MprisService {
    pub fn new() -> Self {
        Self {
            inner: Arc::new(MprisServiceInner {
                players: Mutex::new(HashMap::new()),
                player_added: Event::<PlayerHandle>::new(),
                player_removed: Event::<PlayerHandle>::new(),
                cache_dir: file_utils::get_service_cache_dir().ok(),
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
        Some(PlayerHandle::new(
            self.inner.players.lock().unwrap().remove(name)?,
        ))
    }

    async fn init_player(&self, name: &str) -> Option<PlayerHandle> {
        let player = Player::new(name.to_string(), self.inner.cache_dir.clone())
            .await
            .ok()?;
        let shared = Arc::new(player);
        let clone = shared.clone();
        self.inner
            .players
            .lock()
            .unwrap()
            .insert(name.to_string(), shared);

        Some(PlayerHandle::new(clone))
    }

    pub fn players(&self) -> Vec<PlayerHandle> {
        self.inner
            .players
            .lock()
            .unwrap()
            .values()
            .map(|p| PlayerHandle::new(p.clone()))
            .collect()
    }
}

#[cfg(test)]
mod tests {

    use std::time::Duration;

    use super::*;
    use fake::Fake;
    use test_utils::*;

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
            // give some time to process each dbus event
            tokio::time::sleep(Duration::from_secs(1)).await;
        }

        assert_eq!(service.players().len(), n);
    }

    #[tokio::test]
    async fn test_player_drop() {
        let ctx = TestContext::new().await;
        let service = MprisService::new();
        service.run().await.unwrap();

        let player_info = ctx.run_player().await;

        tokio::time::sleep(Duration::from_secs(1)).await;
        assert_eq!(service.players().len(), 1);

        ctx.drop_player(&player_info.name).await;

        tokio::time::sleep(Duration::from_secs(1)).await;
        assert_eq!(service.players().len(), 0);
    }
}
