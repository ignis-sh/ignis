use crate::private_prelude::*;
use gdk_pixbuf::{Colorspace, Pixbuf};
use std::collections::HashMap;
use tokio::time::{Duration, sleep};
use tracing::error;
use zbus::fdo;
use zbus::object_server::SignalEmitter;
use zbus::{interface, zvariant::OwnedValue};
use zvariant::{Array, Structure};

pub struct DBusService {
    service: NotificationService,
    image_dir: PathBuf,
}

#[interface(name = "org.freedesktop.Notifications")]
impl DBusService {
    #[allow(clippy::too_many_arguments)]
    async fn notify(
        &self,
        app_name: &str,
        replaces_id: u32,
        app_icon: &str,
        summary: &str,
        body: &str,
        actions: Vec<String>,
        hints: HashMap<String, OwnedValue>,
        timeout: i32,
    ) -> u32 {
        let replace = replaces_id != 0;

        let id: u32 = if replace {
            replaces_id
        } else {
            self.service.inner.data.increment_counter()
        };

        let mut iter = actions.into_iter();

        let mut action_obj_vec = Vec::new();

        while let (Some(action_key), Some(label)) = (iter.next(), iter.next()) {
            action_obj_vec.push(Arc::new(Action {
                notification_id: id,
                label,
                action_key,
            }))
        }

        let new_notification = Arc::new(Notification {
            id,
            app_name: app_name.to_string(),
            icon: self.get_icon(app_icon, &hints, id),
            summary: summary.to_string(),
            body: body.to_string(),
            actions: action_obj_vec,
            urgency: hints
                .get("urgency")
                .and_then(|v| v.downcast_ref::<u8>().ok())
                .unwrap_or(0)
                .into(),
            timeout,
        });

        if let Err(e) =
            self.service
                .inner
                .data
                .add_notification(id, new_notification.clone(), replace)
        {
            error!("Failed to add notification: {e}");
        }

        let handle = NotificationHandle {
            inner: new_notification,
            service: self.service.clone(),
        };

        let _ = self.service.inner.tx.send(Event::Notified {
            id,
            notification: handle,
            replace,
        });

        if self.service.inner.settings.follow_xdg_timeout() {
            let actual_timeout = match timeout {
                -1 => self.service.inner.settings.default_timeout(),
                _ => timeout.try_into().unwrap_or(0), // do not do anything if timeout is negative
                                                      // and not -1
            };

            let service = self.service.clone();

            // not equals 0 means should expire
            if actual_timeout != 0 {
                tokio::spawn(async move {
                    sleep(Duration::from_millis(actual_timeout as u64)).await;

                    // Notification can be closed by user before timeout ends
                    // Do not try to expire it if it is already removed
                    if let Ok(_) = service.inner.data.remove_notification(id) {
                        let reason = CloseReason::Expired;

                        if let Ok(interface) = service.get_dbus_interface().await {
                            let _ = interface.notification_closed(id, reason.into()).await;
                        }

                        let _ = service
                            .inner
                            .tx
                            .send(Event::NotificationClosed { id, reason: reason });
                    };
                });
            }
        }

        id
    }

    async fn get_server_information(&self) -> (&str, &str, &str, &str) {
        ("Ignis Notification Service", "linkfrg", "1.0", "1.2")
    }

    async fn get_capabilities(&self) -> &[&str] {
        &["actions", "body", "icon-static", "persistence"]
    }

    async fn close_notification(
        &self,
        id: u32,
        #[zbus(signal_emitter)] emitter: SignalEmitter<'_>,
    ) -> fdo::Result<()> {
        emitter
            .notification_closed(id, CloseReason::DBusCall.into())
            .await?;

        let _ = self.service.inner.data.remove_notification(id);

        let _ = self.service.inner.tx.send(Event::NotificationClosed {
            id,
            reason: CloseReason::DBusCall,
        });

        Ok(())
    }

    // Reason:
    // 1 - The notification expired.
    // 2 - The notification was dismissed by the user.
    // 3 - The notification was closed by a call to CloseNotification.
    // 4 - Undefined/reserved reasons.
    #[zbus(signal)]
    async fn notification_closed(
        emitter: &SignalEmitter<'_>,
        id: u32,
        reason: u32,
    ) -> zbus::Result<()>;

    #[zbus(signal)]
    async fn action_invoked(
        emitter: &SignalEmitter<'_>,
        id: u32,
        action_key: &str,
    ) -> zbus::Result<()>;
}

impl DBusService {
    pub fn new(service: NotificationService) -> Result<Self> {
        Ok(Self {
            image_dir: file_utils::get_image_dir(service.inner.cache_dir.clone())?,
            service,
        })
    }
    fn save_pixbuf(&self, value: &OwnedValue, notification_id: u32) -> Option<String> {
        let s = value.downcast_ref::<Structure>().ok()?;
        let fields = s.fields();

        let width = fields.first()?.downcast_ref::<i32>().ok()?;
        let height = fields.get(1)?.downcast_ref::<i32>().ok()?;
        let rowstride = fields.get(2)?.downcast_ref::<i32>().ok()?;
        let has_alpha = fields.get(3)?.downcast_ref::<bool>().ok()?;
        let bits_per_sample = fields.get(4)?.downcast_ref::<i32>().ok()?;
        // let channels = fields.get(5)?.downcast_ref::<i32>().ok()?;
        let data: Vec<u8> = fields
            .get(6)?
            .downcast_ref::<Array>()
            .ok()?
            .iter()
            .map(|v| u8::try_from(v).unwrap())
            .collect();

        let path = self.image_dir.join(notification_id.to_string());

        Pixbuf::from_bytes(
            &glib::Bytes::from(&data),
            Colorspace::Rgb,
            has_alpha,
            bits_per_sample,
            width,
            height,
            rowstride,
        )
        .savev(&path, "png", &[])
        .ok()?;

        Some(path.to_string_lossy().to_string())
    }

    fn get_icon(
        &self,
        app_icon: &str,
        hints: &HashMap<String, OwnedValue>,
        notification_id: u32,
    ) -> Option<String> {
        if let Some(value) = hints.get("image-data") {
            return self.save_pixbuf(value, notification_id);
        }

        if let Some(value) = hints.get("image-path") {
            return value.downcast_ref::<String>().ok();
        }

        if let Some(value) = hints.get("icon_data") {
            return self.save_pixbuf(value, notification_id);
        }

        Some(app_icon.to_string())
    }
}
