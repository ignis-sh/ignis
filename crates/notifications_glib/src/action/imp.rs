use std::sync::OnceLock;

use glib::prelude::*;
use glib::subclass::prelude::*;
use glib_utils::IntoGLibError;
use glib_utils::glib_async_method;
use glib_utils::runtime;
use notifications::ActionHandle;

use crate::error::GError;

#[derive(Default)]
pub struct GActionImp {
    pub action: OnceLock<ActionHandle>,
}

#[glib::object_subclass]
impl ObjectSubclass for GActionImp {
    const NAME: &'static str = "IgnisNotificationsGLibAction";
    type Type = super::GAction;
    type ParentType = glib::Object;
}

impl ObjectImpl for GActionImp {
    fn properties() -> &'static [glib::ParamSpec] {
        static PROPERTIES: OnceLock<Vec<glib::ParamSpec>> = OnceLock::new();
        PROPERTIES.get_or_init(|| {
            vec![
                glib::ParamSpecUInt::builder("notification-id")
                    .read_only()
                    .build(),
                glib::ParamSpecString::builder("label").read_only().build(),
                glib::ParamSpecString::builder("action-key")
                    .read_only()
                    .build(),
            ]
        })
    }

    fn property(&self, _id: usize, _pspec: &glib::ParamSpec) -> glib::Value {
        match _pspec.name() {
            "id" => self.get_notification_id().to_value(),
            "label" => self.get_label().to_value(),
            "action-key" => self.get_action_key().to_value(),
            _ => unimplemented!(),
        }
    }
}
impl GActionImp {
    fn get_handle(&self) -> ActionHandle {
        self.action
            .get()
            .expect("Inner ActionHandle is empty. This object is initialized incorrectly!")
            .clone()
    }
    pub fn get_notification_id(&self) -> u32 {
        self.get_handle().notification_id()
    }

    pub fn get_label(&self) -> String {
        self.get_handle().label().clone()
    }

    pub fn get_action_key(&self) -> String {
        self.get_handle().action_key().clone()
    }

    pub async fn invoke(&self) -> Result<(), glib::Error> {
        self.get_handle().invoke().await.into_glib_error::<GError>()
    }
}
pub(crate) mod ffi {
    use super::*;
    use glib::translate::*;
    use std::ffi::c_void;

    pub type IgnisNotificationsGLibAction = <super::GActionImp as super::ObjectSubclass>::Instance;

    #[unsafe(no_mangle)]
    pub extern "C" fn ignis_notifications_glib_action_get_type() -> glib::ffi::GType {
        <super::super::GAction as StaticType>::static_type().into_glib()
    }

    #[unsafe(no_mangle)]
    pub extern "C" fn ignis_notifications_glib_action_get_notification_id(
        this: *mut IgnisNotificationsGLibAction,
    ) -> u32 {
        let imp = unsafe { (*this).imp() };
        imp.get_notification_id()
    }

    #[unsafe(no_mangle)]
    pub extern "C" fn ignis_notifications_glib_action_get_label(
        this: *mut IgnisNotificationsGLibAction,
    ) -> *mut glib::ffi::gchar {
        let imp = unsafe { (*this).imp() };
        imp.get_label().to_glib_full()
    }

    #[unsafe(no_mangle)]
    pub extern "C" fn ignis_notifications_glib_action_get_action_key(
        this: *mut IgnisNotificationsGLibAction,
    ) -> *mut glib::ffi::gchar {
        let imp = unsafe { (*this).imp() };
        imp.get_action_key().to_glib_full()
    }

    glib_async_method!(
        IgnisNotificationsGLibAction,
        super::super::GAction,
        ignis_notifications_glib_action_invoke_async,
        ignis_notifications_glib_action_invoke_finish,
        invoke
    );
}
