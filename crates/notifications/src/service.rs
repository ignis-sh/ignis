use crate::data::ServiceData;
use crate::dbus::{DBusService, DBusServiceSignals};
use crate::private_prelude::*;
use std::sync::OnceLock;
use tokio::sync::broadcast;
use zbus::Connection;
use zbus::connection::Builder;
use zbus::object_server::InterfaceRef;

#[derive(Debug)]
pub(crate) struct NotificationServiceInner {
    pub(crate) data: ServiceData,
    pub(crate) connection: OnceLock<Option<Connection>>,
    pub(crate) tx: broadcast::Sender<Event>,
    pub(crate) cache_dir: Option<PathBuf>,
    pub(crate) settings: Settings,
}

/// A notification daemon that follows XDG Desktop Notifications Specification.
///
/// [`NotificationService`] implements [`Clone`] and can be cloned cheapely since underlying data is
/// shared.
#[derive(Clone, Debug)]
pub struct NotificationService {
    pub(crate) inner: Arc<NotificationServiceInner>,
}

impl NotificationService {
    /// Creates a new instance of the service loading the notification history from file.
    /// * `cache_dir` - Overrides the default cache directory located at `~/.cache/ignis_notifications`.
    ///
    /// # Errors
    /// Returns [`Error::IOError`] if loading notification history from file
    /// fails.
    pub fn new(cache_dir: Option<PathBuf>) -> Result<Self> {
        let (tx, _) = broadcast::channel(64);
        Ok(Self {
            inner: Arc::new(NotificationServiceInner {
                data: ServiceData::new(cache_dir.clone())?,
                connection: OnceLock::new(),
                tx,
                cache_dir,
                settings: Settings::default(),
            }),
        })
    }

    /// Creates a new instance of the service without any I/O operations.
    ///
    /// It doesn't load the notification history from file and doesn't save it consequently.
    /// This method can not fail and is guaranteed to return the instance.
    pub fn new_in_memory() -> Self {
        let (tx, _) = broadcast::channel(64);
        Self {
            inner: Arc::new(NotificationServiceInner {
                data: ServiceData::new_in_memory(),
                connection: OnceLock::new(),
                tx,
                cache_dir: None,
                settings: Settings::default(),
            }),
        }
    }

    /// Returns an instance of event receiver.
    pub fn subscribe(&self) -> broadcast::Receiver<Event> {
        self.inner.tx.subscribe()
    }

    /// Returns an instance of settings that affect behavior of the service.
    pub fn settings(&self) -> Settings {
        self.inner.settings.clone()
    }

    /// Runs the service.
    ///
    /// You have to call this this method in order to receive notifications and perform operations
    /// on them, such as dismissing or invoking actions.
    /// It creates D-Bus connection and registers D-Bus interface on the session bus.
    /// Must be called only once.
    ///
    /// # Errors
    /// Returns [`Error::DBusError`], for example, if the name is already taken on the bus.
    ///
    /// Returns [`Error::ConnectionInitializedTwice`] if this function is called
    /// more than once.
    pub async fn run(&self) -> Result<()> {
        let service = DBusService::new(self.clone())?;

        let connection = Builder::session()?
            .name("org.freedesktop.Notifications")?
            .serve_at("/org/freedesktop/Notifications", service)?
            .build()
            .await?;

        self.inner
            .connection
            .set(Some(connection))
            .map_err(|_| Error::ConnectionInitializedTwice)?;

        Ok(())
    }

    pub(crate) fn get_connection(&self) -> Result<Connection> {
        self.inner
            .connection
            .get()
            .ok_or(Error::NoConnection)?
            .to_owned()
            .ok_or(Error::NoConnection)
    }

    pub(crate) async fn get_dbus_interface(&self) -> Result<InterfaceRef<DBusService>> {
        Ok(self
            .get_connection()?
            .object_server()
            .interface("/org/freedesktop/Notifications")
            .await?)
    }

    /// Dismiss a notification by its ID.
    ///
    /// The notification is removed from the history and application that sent the notification is notified through D-Bus.
    /// Emits [`Event::NotificationClosed`] event.
    ///
    /// # Errors
    /// Returns [`Error::DBusError`].
    ///
    /// Returns [`Error::NotificationNotFound`] if the notification with such ID is
    /// not found.
    pub async fn dismiss_notification(&self, id: u32) -> Result<()> {
        self.get_dbus_interface()
            .await?
            .notification_closed(id, CloseReason::Dismissed.into())
            .await?;

        self.inner.data.remove_notification(id)?;

        let _ = self.inner.tx.send(Event::NotificationClosed {
            id,
            reason: CloseReason::Dismissed,
        });

        Ok(())
    }

    /// Invokes an action by its action key and notification ID it belongs to.
    ///
    /// # Errors
    /// Returns [`Error::DBusError`].
    pub async fn invoke_action(&self, notification_id: u32, action_key: &str) -> Result<()> {
        self.get_dbus_interface()
            .await?
            .action_invoked(notification_id, action_key)
            .await?;

        Ok(())
    }

    /// Returns a vector of notification handles.
    pub fn get_notifications(&self) -> Vec<NotificationHandle> {
        self.inner
            .data
            .get_notifications()
            .values()
            .map(|n| NotificationHandle {
                inner: Arc::clone(n),
                service: self.clone(),
            })
            .collect()
    }

    /// Returns a notification handle by notification ID.
    pub fn get_notification_by_id(&self, id: u32) -> Option<NotificationHandle> {
        self.inner
            .data
            .get_notifications()
            .get(&id)
            .map(|n| NotificationHandle {
                inner: n.clone(),
                service: self.clone(),
            })
    }

    /// Clears the notification history.
    ///
    /// It dismisses each notification and notifies applications.
    ///
    /// # Warning
    /// It does **NOT** emit [`Event::NotificationClosed`] event for each notification.
    pub async fn clear_notifications(&self) -> Result<()> {
        for id in self.inner.data.get_notifications().keys() {
            self.get_dbus_interface()
                .await?
                .notification_closed(id.to_owned(), CloseReason::Dismissed.into())
                .await?;
        }

        self.inner.data.clear()
    }
}

// Run with `dbus-run-session cargo test -- --test-threads=1`
// WARNING: must be run serially to avoid D-Bus name conflicts
#[cfg(test)]
mod tests {

    use super::*;
    use std::{collections::HashMap, time::Duration};

    use crate::CloseReason;
    use crate::Urgency;

    use fake::Fake;
    use fake::faker::lorem::en::Sentence;
    use notify_rust::Urgency as ClientUrgency;
    use notify_rust::{
        CloseReason as ClientCloseReason, Notification, NotificationHandle, NotificationResponse,
    };
    use rand::seq::IndexedRandom;
    use tempfile::TempDir;
    use tokio::sync::oneshot;

    impl From<Urgency> for ClientUrgency {
        fn from(value: Urgency) -> Self {
            match value {
                Urgency::Low => ClientUrgency::Low,
                Urgency::Normal => ClientUrgency::Normal,
                Urgency::Critical => ClientUrgency::Critical,
            }
        }
    }

    struct TestContext {
        _temp_dir: TempDir,
        service: NotificationService,
    }

    fn no_tmp_cleanup() -> bool {
        std::env::var_os("NO_TMP_CLEANUP")
            .map(|v| v == "1")
            .unwrap_or(false)
    }

    fn create_random_notification() -> Notification {
        let summary: String = Sentence(3..6).fake();
        let body: String = Sentence(6..12).fake();
        let app_name: String = Sentence(1..3).fake();
        let icon: String = String::from("cat-sleeping-symbolic");

        let mut notification = Notification::new();

        notification
            .appname(&app_name)
            .summary(&summary)
            .body(&body)
            .icon(&icon);

        notification
    }

    async fn send_multiple_random_notifications(quantity: u32) -> HashMap<u32, NotificationHandle> {
        let mut map: HashMap<u32, NotificationHandle> = HashMap::new();

        for _ in 0..quantity {
            let handle = create_random_notification().show_async().await.unwrap();
            let id = handle.id();
            map.insert(id, handle);
        }

        map
    }

    async fn setup_with_details(temp_dir: Option<TempDir>) -> TestContext {
        let mut temp_dir = temp_dir.unwrap_or_else(|| TempDir::new().unwrap());

        if no_tmp_cleanup() {
            temp_dir.disable_cleanup(true);
        }

        let service = NotificationService::new(Some(temp_dir.path().to_path_buf())).unwrap();
        service.run().await.unwrap();

        TestContext {
            _temp_dir: temp_dir,
            service,
        }
    }

    async fn setup() -> TestContext {
        setup_with_details(None).await
    }

    #[tokio::test]
    async fn test_single_notification() {
        let ctx = setup().await;

        let client_urgency_levels = [
            ClientUrgency::Low,
            ClientUrgency::Normal,
            ClientUrgency::Critical,
        ];

        let client_urgency: ClientUrgency = client_urgency_levels
            .choose(&mut rand::rng())
            .unwrap()
            .to_owned();

        let handle = create_random_notification()
            .urgency(client_urgency)
            .show_async()
            .await
            .unwrap();

        let notification = ctx.service.get_notification_by_id(handle.id()).unwrap();

        assert_eq!(handle.appname, notification.app_name());
        assert_eq!(handle.icon, notification.icon().unwrap());
        assert_eq!(handle.summary, notification.summary());
        assert_eq!(handle.body, notification.body());
        assert_eq!(client_urgency, notification.urgency().into());
        assert_eq!(i32::from(handle.timeout), notification.timeout());
    }

    #[tokio::test]
    async fn test_multiple_notifications() {
        let ctx = setup().await;
        send_multiple_random_notifications(50).await;

        assert!(ctx.service.get_notifications().is_sorted_by_key(|x| x.id()));
        assert_eq!(ctx.service.get_notifications().len(), 50);
    }

    #[tokio::test]
    async fn test_dismiss_notification() {
        let ctx = setup().await;
        let handle = create_random_notification().show_async().await.unwrap();
        let id = handle.id();

        let (tx, rx) = oneshot::channel();

        tokio::spawn(async move {
            handle
                .wait_for_action_async(|response| {
                    match response {
                        NotificationResponse::Closed(reason) => tx.send(reason.to_owned()).unwrap(),
                        _ => unimplemented!(),
                    };
                })
                .await;
        });
        // FIXME: Hacky workaround to prevent the test from hanging
        // For some reason calling NotificationService.close_notification() immediately
        // makes the handle "miss" the signal and therefore never call the closure
        tokio::time::sleep(Duration::from_millis(1)).await;

        ctx.service.dismiss_notification(id).await.unwrap();

        let close_reason = rx.await.unwrap();
        assert_eq!(close_reason, ClientCloseReason::Dismissed);
    }

    #[tokio::test]
    async fn test_invoke_action() {
        let ctx = setup().await;
        let handle = Notification::new()
            .summary("i am waiting")
            .action("default", "default")
            .action("asked", "no one asked")
            .show_async()
            .await
            .unwrap();
        let id = handle.id();

        let (tx, rx) = oneshot::channel();

        tokio::spawn(async move {
            handle
                .wait_for_action_async(|response| {
                    match response {
                        NotificationResponse::Action(action) => {
                            tx.send(action.clone()).unwrap();
                        }
                        _ => unimplemented!(),
                    };
                })
                .await;
        });

        // FIXME: the same here
        tokio::time::sleep(Duration::from_millis(1)).await;

        let n = ctx.service.get_notification_by_id(id).unwrap();
        assert_eq!(n.actions().len(), 2);

        for action in n.actions() {
            if action.action_key() == "asked" {
                action.invoke().await.unwrap();
            }
        }

        let action_key = rx.await.unwrap();
        assert_eq!(action_key, "asked")
    }

    #[tokio::test]
    async fn test_clear_notifications() {
        let ctx = setup().await;

        send_multiple_random_notifications(10).await;

        assert_eq!(ctx.service.get_notifications().len(), 10);
        ctx.service.clear_notifications().await.unwrap();

        assert_eq!(ctx.service.get_notifications().len(), 0);
    }

    // FIXME: Bug in notify-rust causes panic when using image_data()
    // because it uses get_server_information() that thereby uses zbus::block_on()
    // Starting a runtime from within another runtime is prohibited.
    // Happens only when "tokio" feature of zbus is enabled.
    // TODO: report the issue in notify-rust repo
    //
    // #[tokio::test]
    // async fn test_image_data() {
    //     let ctx = setup().await;
    //
    //     let width = 64;
    //     let height = 64;
    //
    //     let img_buffer =
    //         ImageBuffer::<Rgba<u8>, _>::from_pixel(width, height, Rgba([255, 255, 255, 255]));
    //
    //     let img = Image::from_rgba(width as i32, height as i32, img_buffer.into_raw()).unwrap();
    //
    //     let client_handle = create_random_notification()
    //         .image_data(img)
    //         .show_async()
    //         .await
    //         .unwrap();
    //
    //     let handle = ctx
    //         .service
    //         .get_notification_by_id(client_handle.id())
    //         .unwrap();
    //
    //     let path = PathBuf::from(handle.icon().unwrap());
    //
    //     assert!(path.exists());
    // }

    async fn check_timeout(ms: i32) {
        let ctx = setup().await;

        create_random_notification()
            .timeout(ms)
            .show_async()
            .await
            .unwrap();

        let (tx, rx) = oneshot::channel();

        let mut sub = ctx.service.subscribe();
        tokio::spawn(async move {
            while let Some(e) = sub.recv().await.ok() {
                match e {
                    Event::NotificationClosed { id: _, reason } => {
                        tx.send(reason).unwrap();
                        break;
                    }
                    _ => {}
                }
            }
        });

        let reason = rx.await.unwrap();
        assert_eq!(reason, CloseReason::Expired);
    }

    #[tokio::test]
    async fn test_default_timeout() {
        check_timeout(-1).await;
    }

    #[tokio::test]
    async fn test_requested_timeout() {
        check_timeout(1000).await;
    }
}
