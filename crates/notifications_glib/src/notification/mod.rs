pub mod imp;

use glib::subclass::prelude::*;

use crate::action::GAction;

glib::wrapper! {
    pub struct GDesktopNotification(ObjectSubclass<imp::GDesktopNotificationImp>);
}

impl GDesktopNotification {
    pub(crate) fn new_from_rust(notification: notifications::NotificationHandle) -> Self {
        let obj: GDesktopNotification = glib::Object::builder().build();

        for i in notification.actions().clone() {
            obj.imp().actions.append(&GAction::new_from_rust(i));
        }

        obj.imp()
            .notification
            .set(notification)
            .expect("Failed to set NotificationHandle");

        obj
    }
}
