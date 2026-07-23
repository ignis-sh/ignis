use crate::private_prelude::*;
/// The urgency level of the notification.
///
/// Represents how important is the notification and may affect how it's displayed in the graphical
/// interface.
#[derive(Copy, Clone, Serialize, Deserialize, Debug)]
pub enum Urgency {
    /// A low level of urgency.
    ///
    /// Notification does not require immediate user attention.
    Low,

    /// A normal level of urgency.
    ///
    /// For example, a notification about new message from a chat app.
    Normal,

    /// A critical level of urgency.
    ///
    /// The notification requires user attention and should stand out from the rest of
    /// notifications.
    Critical,
}

impl From<u8> for Urgency {
    fn from(value: u8) -> Self {
        match value {
            0 => Self::Low,
            1 => Self::Normal,
            2 => Self::Critical,
            _ => Self::Low, // fallback
        }
    }
}

impl From<Urgency> for u8 {
    fn from(value: Urgency) -> Self {
        match value {
            Urgency::Low => 0,
            Urgency::Normal => 1,
            Urgency::Critical => 2,
        }
    }
}
