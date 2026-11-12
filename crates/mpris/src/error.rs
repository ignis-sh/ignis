use thiserror::Error;

/// Errors returned by this crate.
#[derive(Error, Debug)]
pub enum Error {
    /// A D-Bus error.
    #[error("D-Bus error: {0}")]
    DBusError(#[from] zbus::Error),

    /// An error returned by the player through D-Bus, e.g. the method is not supported.
    #[error("D-Bus fdo error: {0}")]
    DBusFdoError(#[from] zbus::fdo::Error),

    /// An internal task stopped before it finished initializing a player.
    #[error("Sync error: {0}")]
    OneshotSyncError(#[from] tokio::sync::oneshot::error::RecvError),

    /// An I/O error.
    #[error("I/O error: {0}")]
    IOError(#[from] std::io::Error),

    /// The cache directory could not be determined.
    #[error("Failed to get cache directory")]
    CacheDirRetrieveError,
}

/// A [`Result`](std::result::Result) alias where the error is [`Error`](enum@Error).
pub type Result<T> = std::result::Result<T, Error>;
