use thiserror::Error;

#[derive(Error, Debug)]
pub enum Error {
    #[error("D-Bus error: {0}")]
    DBusError(#[from] zbus::Error),

    #[error("D-Bus fdo error: {0}")]
    DBusFdoError(#[from] zbus::fdo::Error),
}

pub type Result<T> = std::result::Result<T, Error>;
