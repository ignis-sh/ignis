use glib::prelude::*;
use glib::translate::*;
use notifications::CloseReason;

#[derive(Copy, Clone, glib::Enum)]
#[enum_type(name = "IgnisNotificationsGLibCloseReason")]
pub enum GCloseReason {
    Expired,
    Dismissed,
    DBusCall,
    Other,
}

impl From<CloseReason> for GCloseReason {
    fn from(value: CloseReason) -> Self {
        match value {
            CloseReason::Expired => GCloseReason::Expired,
            CloseReason::Dismissed => GCloseReason::Dismissed,
            CloseReason::DBusCall => GCloseReason::DBusCall,
            CloseReason::Other => GCloseReason::Other,
        }
    }
}

#[allow(dead_code)]
pub(crate) mod ffi {
    use super::*;

    pub type IgnisNotificationsGLibCloseReason = <super::GCloseReason as super::IntoGlib>::GlibType;

    pub const IGNIS_NOTIFICATIONS_GLIB_CLOSE_REASON_EXPIRED: IgnisNotificationsGLibCloseReason =
        super::GCloseReason::Expired as i32;
    pub const IGNIS_NOTIFICATIONS_GLIB_CLOSE_REASON_DISMISSED: IgnisNotificationsGLibCloseReason =
        super::GCloseReason::Dismissed as i32;
    pub const IGNIS_NOTIFICATIONS_GLIB_CLOSE_REASON_D_BUS_CALL: IgnisNotificationsGLibCloseReason =
        super::GCloseReason::DBusCall as i32;
    pub const IGNIS_NOTIFICATIONS_GLIB_CLOSE_REASON_OTHER: IgnisNotificationsGLibCloseReason =
        super::GCloseReason::Other as i32;

    #[unsafe(no_mangle)]
    pub unsafe extern "C" fn ignis_notifications_glib_close_reason_get_type() -> glib::ffi::GType {
        super::GCloseReason::static_type().into_glib()
    }
}
