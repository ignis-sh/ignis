use std::sync::OnceLock;

use gio::prelude::ListModelExt;
use glib::prelude::*;
use glib::subclass::{Signal, prelude::*};
use glib_utils::{IntoGLibError, glib_async_method, runtime};
use notifications::NotificationHandle;

use crate::action::GAction;
use crate::close_reason::GCloseReason;
use crate::error::GError;
use crate::urgency::GUrgency;

pub struct GDesktopNotificationImp {
    pub notification: OnceLock<NotificationHandle>,
    pub(crate) actions: gio::ListStore,
}

impl Default for GDesktopNotificationImp {
    fn default() -> Self {
        Self {
            notification: OnceLock::new(),
            actions: gio::ListStore::new::<GAction>(),
        }
    }
}

#[glib::object_subclass]
impl ObjectSubclass for GDesktopNotificationImp {
    const NAME: &'static str = "IgnisNotificationsGLibNotification";
    type Type = super::GDesktopNotification;
    type ParentType = glib::Object;
}

impl ObjectImpl for GDesktopNotificationImp {
    fn signals() -> &'static [glib::subclass::Signal] {
        static SIGNALS: OnceLock<Vec<Signal>> = OnceLock::new();
        SIGNALS.get_or_init(|| {
            vec![
                Signal::builder("closed")
                    .param_types([GCloseReason::static_type()])
                    .build(),
            ]
        })
    }

    fn properties() -> &'static [glib::ParamSpec] {
        static PROPERTIES: OnceLock<Vec<glib::ParamSpec>> = OnceLock::new();
        PROPERTIES.get_or_init(|| {
            vec![
                glib::ParamSpecUInt::builder("id").read_only().build(),
                glib::ParamSpecString::builder("app-name")
                    .read_only()
                    .build(),
                glib::ParamSpecString::builder("icon").read_only().build(),
                glib::ParamSpecString::builder("summary")
                    .read_only()
                    .build(),
                glib::ParamSpecString::builder("body").read_only().build(),
                glib::ParamSpecObject::builder::<gio::ListStore>("actions")
                    .read_only()
                    .build(),
                glib::ParamSpecEnum::builder::<GUrgency>("urgency")
                    .read_only()
                    .build(),
                glib::ParamSpecInt::builder("timeout").read_only().build(),
            ]
        })
    }

    fn property(&self, _id: usize, _pspec: &glib::ParamSpec) -> glib::Value {
        match _pspec.name() {
            "id" => self.get_id().to_value(),
            "app-name" => self.get_app_name().to_value(),
            "icon" => self.get_icon().to_value(),
            "summary" => self.get_summary().to_value(),
            "body" => self.get_body().to_value(),
            "actions" => self.actions.to_value(),
            "urgency" => self.get_urgency().to_value(),
            "timeout" => self.get_timeout().to_value(),
            _ => unimplemented!(),
        }
    }
}
impl GDesktopNotificationImp {
    fn get_handle(&self) -> NotificationHandle {
        self.notification
            .get()
            .expect("Inner NotificationHandle is empty. This object was initialized incorrectly!")
            .clone()
    }
    pub fn get_id(&self) -> u32 {
        self.get_handle().id()
    }

    pub fn get_app_name(&self) -> String {
        self.get_handle().app_name().clone()
    }

    pub fn get_icon(&self) -> Option<String> {
        self.get_handle().icon().clone()
    }

    pub fn get_summary(&self) -> String {
        self.get_handle().summary().clone()
    }

    pub fn get_body(&self) -> String {
        self.get_handle().body().clone()
    }

    pub fn get_actions(&self) -> Vec<GAction> {
        let mut res = Vec::new();
        for i in 0..self.actions.n_items() {
            if let Some(item) = self.actions.item(i)
                && let Ok(action) = item.downcast::<GAction>()
            {
                res.push(action);
            }
        }

        res
    }

    pub fn get_urgency(&self) -> GUrgency {
        self.get_handle().urgency().into()
    }

    pub fn get_timeout(&self) -> i32 {
        self.get_handle().timeout()
    }

    pub async fn dismiss(&self) -> Result<(), glib::Error> {
        self.get_handle()
            .dismiss()
            .await
            .into_glib_error::<GError>()?;

        Ok(())
    }
}
pub(crate) mod ffi {
    use crate::urgency::ffi::IgnisNotificationsGLibUrgency;

    use super::*;
    use glib::translate::*;
    use std::ffi::c_void;

    pub type IgnisNotificationsGLibNotification =
        <super::GDesktopNotificationImp as super::ObjectSubclass>::Instance;

    #[unsafe(no_mangle)]
    pub unsafe extern "C" fn ignis_notifications_glib_notification_new()
    -> *mut IgnisNotificationsGLibNotification {
        glib::Object::builder::<super::super::GDesktopNotification>()
            .build()
            .to_glib_full()
    }

    #[unsafe(no_mangle)]
    pub extern "C" fn ignis_notifications_glib_notification_get_type() -> glib::ffi::GType {
        <super::super::GDesktopNotification as StaticType>::static_type().into_glib()
    }

    #[unsafe(no_mangle)]
    pub extern "C" fn ignis_notifications_glib_notification_get_id(
        this: *mut IgnisNotificationsGLibNotification,
    ) -> u32 {
        let imp = unsafe { (*this).imp() };
        imp.get_id()
    }

    #[unsafe(no_mangle)]
    pub extern "C" fn ignis_notifications_glib_notification_get_app_name(
        this: *mut IgnisNotificationsGLibNotification,
    ) -> *mut glib::ffi::gchar {
        let imp = unsafe { (*this).imp() };
        imp.get_app_name().to_glib_full()
    }

    #[unsafe(no_mangle)]
    pub extern "C" fn ignis_notifications_glib_notification_get_icon(
        this: *mut IgnisNotificationsGLibNotification,
    ) -> *mut glib::ffi::gchar {
        let imp = unsafe { (*this).imp() };
        imp.get_icon().to_glib_full()
    }

    #[unsafe(no_mangle)]
    pub extern "C" fn ignis_notifications_glib_notification_get_summary(
        this: *mut IgnisNotificationsGLibNotification,
    ) -> *mut glib::ffi::gchar {
        let imp = unsafe { (*this).imp() };
        imp.get_summary().to_glib_full()
    }

    #[unsafe(no_mangle)]
    pub extern "C" fn ignis_notifications_glib_notification_get_body(
        this: *mut IgnisNotificationsGLibNotification,
    ) -> *mut glib::ffi::gchar {
        let imp = unsafe { (*this).imp() };
        imp.get_body().to_glib_full()
    }

    #[unsafe(no_mangle)]
    pub extern "C" fn ignis_notifications_glib_notification_get_actions(
        this: *mut IgnisNotificationsGLibNotification,
    ) -> *mut glib::ffi::GPtrArray {
        let imp = unsafe { (*this).imp() };
        imp.get_actions().to_glib_full()
    }

    #[unsafe(no_mangle)]
    pub extern "C" fn ignis_notifications_glib_notification_get_urgency(
        this: *mut IgnisNotificationsGLibNotification,
    ) -> IgnisNotificationsGLibUrgency {
        let imp = unsafe { (*this).imp() };
        imp.get_urgency().into_glib()
    }

    #[unsafe(no_mangle)]
    pub extern "C" fn ignis_notifications_glib_notification_get_timeout(
        this: *mut IgnisNotificationsGLibNotification,
    ) -> i32 {
        let imp = unsafe { (*this).imp() };
        imp.get_timeout()
    }

    glib_async_method!(
        IgnisNotificationsGLibNotification,
        super::super::GDesktopNotification,
        ignis_notifications_glib_notification_dismiss_async,
        ignis_notifications_glib_notification_dismiss_finish,
        dismiss,
    );
}
