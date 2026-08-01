#[derive(Debug, Copy, Clone, PartialEq, Eq, glib::ErrorDomain)]
#[error_domain(name = "ignis-notifications-glib-error")]
pub enum GError {
    DBusError,
    NoConnection,
    IOError,
    JSONError,
    NotificationNotFound,
    ConnectionInitializedTwice,
}

impl From<&notifications::Error> for GError {
    fn from(e: &notifications::Error) -> Self {
        match e {
            notifications::Error::NoConnection => GError::NoConnection,
            notifications::Error::DBusError(_) => GError::DBusError,
            notifications::Error::IOError(_) => GError::IOError,
            notifications::Error::JSONError(_) => GError::JSONError,
            notifications::Error::NotificationNotFound(_) => GError::NotificationNotFound,
            notifications::Error::ConnectionInitializedTwice => GError::ConnectionInitializedTwice,
        }
    }
}

#[allow(dead_code)]
pub(crate) mod ffi {
    use glib::{prelude::*, translate::*};

    pub type IgnisNotificationsGLibError = i32;

    pub const IGNIS_NOTIFICATIONS_GLIB_ERROR_DBUS_ERROR: IgnisNotificationsGLibError =
        super::GError::DBusError as i32;

    pub const IGNIS_NOTIFICATIONS_GLIB_ERROR_NO_CONNECTION: IgnisNotificationsGLibError =
        super::GError::NoConnection as i32;

    pub const IGNIS_NOTIFICATIONS_GLIB_ERROR_IO_ERROR: IgnisNotificationsGLibError =
        super::GError::IOError as i32;

    pub const IGNIS_NOTIFICATIONS_GLIB_ERROR_JSON_ERROR: IgnisNotificationsGLibError =
        super::GError::JSONError as i32;

    pub const IGNIS_NOTIFICATIONS_GLIB_ERROR_NOTIFICATION_NOT_FOUND: IgnisNotificationsGLibError =
        super::GError::NotificationNotFound as i32;

    pub const IGNIS_NOTIFICATIONS_GLIB_ERROR_CONNECTION_INITIALIZED_TWICE:
        IgnisNotificationsGLibError = super::GError::ConnectionInitializedTwice as i32;

    #[unsafe(no_mangle)]
    pub unsafe extern "C" fn ignis_notifications_glib_error_quark() -> glib::ffi::GQuark {
        <super::GError as ErrorDomain>::domain().into_glib()
    }
}
