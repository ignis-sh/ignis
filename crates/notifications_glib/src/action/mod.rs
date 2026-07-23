pub mod imp;

use glib::subclass::prelude::*;

glib::wrapper! {
    pub struct GAction(ObjectSubclass<imp::GActionImp>);
}

impl GAction {
    pub(crate) fn new_from_rust(action: notifications::ActionHandle) -> Self {
        let obj: Self = glib::Object::builder().build();

        obj.imp()
            .action
            .set(action)
            .expect("Failed to set ActionHandle");

        obj
    }
}
