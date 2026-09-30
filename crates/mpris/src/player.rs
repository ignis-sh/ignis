use crate::dbus::{MediaPlayer2Proxy, PlayerProxy};
use crate::private_prelude::*;
use std::sync::Arc;
use zbus::Connection;

pub(crate) struct Player {
    name: String,
    connection: Connection,
}

impl Player {
    pub(crate) async fn new(name: String) -> Result<Self> {
        let connection = Connection::session().await?;

        Ok(Player { name, connection })
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
    async fn next(&self) -> Result<()> {
        self.inner.player_proxy().await?.next().await?;
        Ok(())
    }
}
