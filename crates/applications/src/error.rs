use thiserror::Error;

/// Error enum
#[derive(Error, Debug)]
pub enum Error {
    /// An error in inotify.
    #[error("Notify error: {0}")]
    NotifyError(#[from] notify::Error),

    /// Attempted to launch application/action but exec string is empty.
    #[error("Exec string is empty")]
    ExecEmpty,

    /// I/O error.
    #[error("I/O Error: {0}")]
    IOError(#[from] std::io::Error),
}

/// Alias for a [`std::result::Result`] with the error type [`crate::Error`].
pub type Result<T> = std::result::Result<T, Error>;
