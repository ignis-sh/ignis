use crate::close_reason::GCloseReason;
use crate::error::GError;
use crate::notification::GDesktopNotification;
use gio::prelude::ListModelExt;
use glib::prelude::*;
use glib::subclass::{Signal, prelude::*};
use glib::translate::*;
use glib_utils::{IntoGLibError, glib_async_method, runtime};
use notifications::Event;
use std::sync::OnceLock;

pub struct GNotificationServiceImp {
    pub service: notifications::NotificationService,
    pub notifications: gio::ListStore,
}

impl Default for GNotificationServiceImp {
    fn default() -> Self {
        let service = notifications::NotificationService::new(None).unwrap_or_else(|e| {
            glib::g_error!(
                "ignis-notifications-glib",
                "Failed to initialize Rust Service! Falling back, file I/O is disabled: {e}"
            );
            notifications::NotificationService::new_in_memory()
        });

        let notifications = gio::ListStore::new::<GDesktopNotification>();
        let initial_notifications = service.get_notifications();

        for n in initial_notifications {
            let obj = GDesktopNotification::new_from_rust(n);

            notifications.append(&obj);
        }

        Self {
            service,
            notifications,
        }
    }
}

#[glib::object_subclass]
impl ObjectSubclass for GNotificationServiceImp {
    const NAME: &'static str = "IgnisNotificationsGLibService";
    type Type = super::GNotificationService;
    type ParentType = glib::Object;
}

impl ObjectImpl for GNotificationServiceImp {
    fn signals() -> &'static [glib::subclass::Signal] {
        static SIGNALS: OnceLock<Vec<Signal>> = OnceLock::new();
        SIGNALS.get_or_init(|| {
            vec![
                Signal::builder("notified")
                    .param_types([
                        u32::static_type(),
                        GDesktopNotification::static_type(),
                        bool::static_type(),
                    ])
                    .build(),
                Signal::builder("closed")
                    .param_types([u32::static_type(), GCloseReason::static_type()])
                    .build(),
                Signal::builder("notifications-cleared").build(),
            ]
        })
    }
    fn properties() -> &'static [glib::ParamSpec] {
        static PROPERTIES: OnceLock<Vec<glib::ParamSpec>> = OnceLock::new();

        PROPERTIES.get_or_init(|| {
            vec![
                glib::ParamSpecObject::builder::<gio::ListStore>("notifications")
                    .read_only()
                    .build(),
                glib::ParamSpecBoolean::builder("follow-xdg-timeout").build(),
                glib::ParamSpecUInt::builder("default-timeout").build(),
            ]
        })
    }

    fn property(&self, _id: usize, _pspec: &glib::ParamSpec) -> glib::Value {
        match _pspec.name() {
            "notifications" => self.notifications.to_value(),
            "follow-xdg-timeout" => self.service.settings().follow_xdg_timeout().to_value(),
            "default-timeout" => self.service.settings().default_timeout().to_value(),
            _ => unimplemented!(),
        }
    }

    fn set_property(&self, _id: usize, _value: &glib::Value, _pspec: &glib::ParamSpec) {
        match _pspec.name() {
            "follow-xdg-timeout" => {
                let value: bool = _value
                    .get_owned()
                    .expect("got wrong type for 'follow-xdg-timeout' property");
                self.service.settings().set_follow_xdg_timeout(value);
            }
            "default-timeout" => {
                let value: u32 = _value
                    .get_owned()
                    .expect("got wrong type for 'default-timeout' property");

                self.service.settings().set_default_timeout(value);
            }

            _ => unimplemented!(),
        }
    }

    fn constructed(&self) {
        self.parent_constructed();

        let obj = self.obj().to_owned();

        glib::MainContext::default().spawn_local(async move {
            let notif_store = &obj.imp().notifications;

            while let Some(signal) = obj.imp().service.subscribe().recv().await.ok() {
                match signal {
                    Event::NotificationClosed { id, reason } => {
                        obj.imp().remove_notification(id, reason.into())
                    }
                    Event::Notified {
                        id,
                        notification,
                        replace,
                    } => {
                        let g_desktop_notification =
                            GDesktopNotification::new_from_rust(notification);

                        if !replace {
                            notif_store.append(&g_desktop_notification);
                        } else {
                            let position =
                                glib_utils::search_in_list_store::<GDesktopNotification, _>(
                                    notif_store,
                                    |n| n.imp().get_id() == id,
                                );

                            if let Some(pos) = position {
                                notif_store.splice(pos, 1, &[g_desktop_notification.clone()]);
                            } else {
                                notif_store.append(&g_desktop_notification);
                            }
                        }

                        obj.notify("notifications");
                        obj.emit_by_name_with_values(
                            "notified",
                            &[
                                id.to_value(),
                                g_desktop_notification.to_value(),
                                replace.to_value(),
                            ],
                        );
                    }
                }
            }
        });
    }
}

impl GNotificationServiceImp {
    fn remove_notification(&self, id: u32, reason: GCloseReason) {
        let notif_store = &self.notifications;

        let position =
            glib_utils::search_in_list_store::<GDesktopNotification, _>(notif_store, |n| {
                n.imp().get_id() == id
            });

        if let Some(position) = position {
            let gnotification = notif_store
                .item(position)
                .unwrap()
                .downcast_ref::<GDesktopNotification>()
                .unwrap()
                .to_owned();

            notif_store.remove(position);

            gnotification.emit_by_name_with_values("closed", &[reason.to_value()]);
            self.obj().notify("notifications");
            self.obj()
                .emit_by_name_with_values("closed", &[id.to_value(), reason.to_value()]);
        }
    }
    pub async fn run_async(&self) -> Result<(), glib::Error> {
        self.service.run().await.into_glib_error::<GError>()?;

        Ok(())
    }

    pub fn get_notifications(&self) -> Vec<GDesktopNotification> {
        (0..self.notifications.n_items())
            .map(|i| {
                self.notifications
                    .item(i)
                    .unwrap()
                    .downcast::<GDesktopNotification>()
                    .unwrap()
            })
            .collect()
    }

    pub async fn dismiss_notification(&self, notification_id: u32) -> Result<(), glib::Error> {
        self.service
            .dismiss_notification(notification_id)
            .await
            .into_glib_error::<GError>()?;

        self.remove_notification(notification_id, GCloseReason::Dismissed);

        Ok(())
    }

    pub async fn invoke_action(
        &self,
        notification_id: u32,
        action_key: &str,
    ) -> Result<(), glib::Error> {
        self.service
            .invoke_action(notification_id, action_key)
            .await
            .into_glib_error::<GError>()
    }

    pub async fn clear_notifications(&self) -> Result<(), glib::Error> {
        // NOTE: it doesn't emit closed for each notification as it was before
        // Users should manually clear their notification list widget contents
        //
        self.service
            .clear_notifications()
            .await
            .into_glib_error::<GError>()?;

        self.notifications.remove_all();
        self.obj()
            .emit_by_name_with_values("notifications-cleared", &[]);
        Ok(())
    }
}

pub(crate) mod ffi {
    use super::*;
    use std::ffi::c_void;

    pub type IgnisNotificationsGLibService =
        <super::GNotificationServiceImp as super::ObjectSubclass>::Instance;

    #[unsafe(no_mangle)]
    pub unsafe extern "C" fn ignis_notifications_glib_service_new()
    -> *mut IgnisNotificationsGLibService {
        glib::Object::builder::<super::super::GNotificationService>()
            .build()
            .to_glib_full()
    }

    #[unsafe(no_mangle)]
    pub extern "C" fn ignis_notifications_glib_service_get_type() -> glib::ffi::GType {
        <super::super::GNotificationService as StaticType>::static_type().into_glib()
    }

    glib_async_method!(
        IgnisNotificationsGLibService,
        super::super::GNotificationService,
        ignis_notifications_glib_service_run_async,
        ignis_notifications_glib_service_run_finish,
        run_async,
    );

    glib_async_method!(
        IgnisNotificationsGLibService,
        super::super::GNotificationService,
        ignis_notifications_glib_service_dismiss_notification_async,
        ignis_notifications_glib_service_dismiss_notification_finish,
        dismiss_notification,
        notification_id: u32 => { notification_id }
    );

    glib_async_method!(
        IgnisNotificationsGLibService,
        super::super::GNotificationService,
        ignis_notifications_glib_service_invoke_action_async,
        ignis_notifications_glib_service_invoke_action_finish,
        invoke_action,
        notification_id: u32 => { notification_id },
        action_key: *mut glib::ffi::gchar => {
            let string: String = unsafe { from_glib_none(action_key) };
            &*string.clone()
        }
    );

    #[unsafe(no_mangle)]
    pub unsafe extern "C" fn ignis_notifications_glib_service_get_notifications(
        this: *mut IgnisNotificationsGLibService,
    ) -> *mut glib::ffi::GList {
        let imp = unsafe { (*this).imp() };
        imp.get_notifications().to_glib_full()
    }

    glib_async_method!(
        IgnisNotificationsGLibService,
        super::super::GNotificationService,
        ignis_notifications_glib_service_clear_notifications_async,
        ignis_notifications_glib_service_clear_notifications_finish,
        clear_notifications,
    );
}
