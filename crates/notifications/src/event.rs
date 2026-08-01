use crate::private_prelude::*;

/// Represents an event happened in the service.
///
/// The source of the event can be both outer D-Bus request or the service itself.
#[derive(Clone)]
pub enum Event {
    /// A new notification arrived.
    Notified {
        /// The ID of the new notification.
        id: u32,

        /// A handle to the notification.
        notification: NotificationHandle,

        /// Whether this notification replaces an old one with this ID.
        replace: bool,
    },

    /// A notification was closed.
    NotificationClosed {
        /// The ID of the closed notification.
        id: u32,

        /// The reason why the notification is closed.
        reason: CloseReason,
    },
}
