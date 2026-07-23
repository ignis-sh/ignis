use crate::private_prelude::*;
use std::sync::RwLock;

#[derive(Debug)]
struct SettingsInner {
    follow_xdg_timeout: bool,
    default_timeout: u32,
}

impl Default for SettingsInner {
    fn default() -> Self {
        Self {
            follow_xdg_timeout: true,
            default_timeout: 3000,
        }
    }
}

/// Settings for [`NotificationService`].
///
/// This struct provides methods to change behavior of some parts of the service.
/// [`Settings`] uses shared ownership for the data, so cloning it is a cheap operation.
#[derive(Default, Debug, Clone)]
pub struct Settings {
    inner: Arc<RwLock<SettingsInner>>,
}

impl Settings {
    /// Returns whether to respect XDG Specification for timeout.
    ///
    /// If set to `False`, notifications never expire despite the [`NotificationHandle::timeout()`].
    /// Otherwise, behavior is based on notification's timeout:
    /// * `-1` - timeout value is taken from [`Settings::default_timeout()`].
    /// * `0` - the notification never expire
    /// * `>=0` - this timeout is used to expire the notification
    ///
    /// Default: `True`.
    pub fn follow_xdg_timeout(&self) -> bool {
        self.inner.write().unwrap().follow_xdg_timeout
    }

    /// Returns the default timeout.
    ///
    /// Has effect only if [`Settings::follow_xdg_timeout()`] is `false` and
    /// [`NotificationHandle::timeout()`] is `0`.
    ///
    /// Default: `3000`.
    pub fn default_timeout(&self) -> u32 {
        self.inner.write().unwrap().default_timeout
    }

    /// Sets [`Settings::follow_xdg_timeout()`] setting.
    pub fn set_follow_xdg_timeout(&self, value: bool) {
        self.inner.write().unwrap().follow_xdg_timeout = value;
    }

    /// Sets [`Settings::default_timeout()`] setting.
    pub fn set_default_timeout(&self, value: u32) {
        self.inner.write().unwrap().default_timeout = value;
    }
}
