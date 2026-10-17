use thiserror::Error;

#[derive(Error, Debug)]
pub enum Error {
    #[error("D-Bus error: {0}")]
    DBusError(#[from] zbus::Error),

    #[error("D-Bus fdo error: {0}")]
    DBusFdoError(#[from] zbus::fdo::Error),

    #[error("Sync error: {0}")]
    OneshotSyncError(#[from] tokio::sync::oneshot::error::RecvError),

    #[error("I/O error: {0}")]
    IOError(#[from] std::io::Error),

    #[error("Failed to get cache directory")]
    CacheDirRetrieveError,
}

pub type Result<T> = std::result::Result<T, Error>;
