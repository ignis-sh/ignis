use thiserror::Error;

/// Enum representing possible errors to happen during the usage of [`crate::NotificationService`].
#[derive(Error, Debug)]
pub enum Error {
    /// D-Bus error. Carries [`zbus::Error`] inside.
    ///
    /// Usually returned if another notification daemon is running on the session bus.
    #[error("D-Bus error: {0}")]
    DBusError(#[from] zbus::Error),

    /// Returned if attempted to call methods that involve D-Bus interaction and have not called
    /// [`crate::NotificationService::run`] yet.
    #[error("Connection not exist error")]
    NoConnection,

    /// Returned in case of I/O file errors. Carries [`std::io::Error`].
    #[error("I/O Error: {0}")]
    IOError(#[from] std::io::Error),

    /// Returned if JSON parsing of the notification history failed. Carries [`serde_json::Error`].
    ///
    /// Usually indicates that the JSON markup is corrupted.
    #[error(
        "JSON error (you may need to manually fix or remove history file at ~/.cache/ignis_notifications/notifications.json): {0}"
    )]
    JSONError(#[from] serde_json::Error),

    /// Returned if the notification with the given ID is not found.
    #[error("No notification found with id: {0}")]
    NotificationNotFound(u32),

    /// Returned if [`crate::NotificationService::run`] is called more than once.
    #[error("Attempted to initialize connection twice (run() was called twice)")]
    ConnectionInitializedTwice,
}

/// Alias for a [`std::result::Result`] with the error type [`crate::Error`].
pub type Result<T> = std::result::Result<T, Error>;
