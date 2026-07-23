use glib::prelude::*;
use glib::translate::*;
use notifications::Urgency;

#[derive(Copy, Clone, Default, glib::Enum)]
#[enum_type(name = "IgnisNotificationsGLibUrgency")]
pub enum GUrgency {
    #[default]
    Low,
    Normal,
    Critical,
}

impl From<Urgency> for GUrgency {
    fn from(value: Urgency) -> Self {
        match value {
            Urgency::Low => GUrgency::Low,
            Urgency::Normal => GUrgency::Normal,
            Urgency::Critical => GUrgency::Critical,
        }
    }
}

#[allow(dead_code)]
pub(crate) mod ffi {
    use super::*;

    pub type IgnisNotificationsGLibUrgency = <super::GUrgency as super::IntoGlib>::GlibType;
    pub const IGNIS_NOTIFICATIONS_GLIB_URGENCY_LOW: IgnisNotificationsGLibUrgency =
        super::GUrgency::Low as i32;
    pub const IGNIS_NOTIFICATIONS_GLIB_URGENCY_NORMAL: IgnisNotificationsGLibUrgency =
        super::GUrgency::Normal as i32;
    pub const IGNIS_NOTIFICATIONS_GLIB_URGENCY_CRITICAL: IgnisNotificationsGLibUrgency =
        super::GUrgency::Critical as i32;

    #[unsafe(no_mangle)]
    pub unsafe extern "C" fn ignis_notifications_glib_urgency_get_type() -> glib::ffi::GType {
        super::GUrgency::static_type().into_glib()
    }
}
