use crate::private_prelude::*;
use futures_util::stream::StreamExt;
use ignis_core::Events;
use ignis_core::event::EventOwner;
use std::path::PathBuf;
use std::sync::Mutex;
use std::{collections::HashMap, sync::Arc};
use zbus::Connection;

/// Events of [`MprisService`].
#[derive(Events, Default)]
#[events(handle = MprisServiceEvents, export = mpris_service_events)]
struct MprisServiceOwnerEvents {
    /// Emitted with the new player when a player appears on the bus.
    ///
    /// It is not emitted for players that are already running when the service starts. Use
    /// `players` to get them.
    player_added: EventOwner<PlayerHandle>,

    /// Emitted with the player when a player disappears from the bus, e.g. when it is closed.
    player_removed: EventOwner<PlayerHandle>,
}

struct MprisServiceInner {
    pub(crate) players: Mutex<HashMap<String, Arc<Player>>>,
    events: MprisServiceOwnerEvents,
    cache_dir: Option<PathBuf>,
}

/// A service which tracks media players on the session bus.
///
/// A player is any D-Bus client which owns a name starting with `org.mpris.MediaPlayer2`.
///
/// [`MprisService`] implements [`Clone`] and can be cloned cheaply since underlying data is
/// shared.
#[derive(Clone)]
pub struct MprisService {
    inner: Arc<MprisServiceInner>,

    /// Events of the service.
    pub events: MprisServiceEvents,
}

impl Default for MprisService {
    fn default() -> Self {
        Self::new()
    }
}

impl MprisService {
    /// Creates a new instance of the service.
    ///
    /// Cover arts are cached in `$XDG_CACHE_HOME/ignis-mpris/images`. If the cache directory
    /// can't be created, cover arts are not cached.
    ///
    /// The service doesn't track players until [`MprisService::run`] is called.
    pub fn new() -> Self {
        let events = MprisServiceOwnerEvents::default();

        Self {
            events: events.handle(),
            inner: Arc::new(MprisServiceInner {
                players: Mutex::new(HashMap::new()),
                cache_dir: file_utils::get_service_cache_dir().ok(),
                events,
            }),
        }
    }

    /// Runs the service.
    ///
    /// Connects to the session bus, adds players which are already running and starts watching
    /// for players appearing and disappearing in the background. Must be called only once.
    ///
    /// Players that fail to initialize are skipped.
    ///
    /// # Errors
    /// Returns [`Error::DBusError`] or [`Error::DBusFdoError`] if connecting to the session bus or
    /// listing the names on it fails.
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
                            self.inner.events.player_added.emit(&handle);
                        }
                    }

                    (Some(_old_owner), None) => {
                        // Name lost
                        if let Some(handle) = self.remove_player(&name) {
                            self.inner.events.player_removed.emit(&handle);
                            handle.inner.events.removed.emit(&());
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

    /// Returns the currently running players.
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
