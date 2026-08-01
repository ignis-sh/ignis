use crate::private_prelude::*;

#[derive(Serialize, Deserialize, Debug)]
pub(crate) struct Notification {
    pub(crate) id: u32,
    pub(crate) app_name: String,
    pub(crate) icon: Option<String>,
    pub(crate) summary: String,
    pub(crate) body: String,
    pub(crate) actions: Vec<Arc<Action>>,
    pub(crate) urgency: Urgency,
    pub(crate) timeout: i32,
}

/// A handle to a notification.
#[derive(Clone, Debug)]
pub struct NotificationHandle {
    pub(crate) inner: Arc<Notification>,
    pub(crate) service: NotificationService,
}

impl NotificationHandle {
    /// Returns the unique non-zero identifer of the notification.
    pub fn id(&self) -> u32 {
        self.inner.id
    }

    /// Returns the name of the application that sent the notification. Can be blank.
    pub fn app_name(&self) -> String {
        self.inner.app_name.clone()
    }

    /// Returns the optional icon of the notification.
    ///
    /// It is either file path or icon name.
    // TODO: make it enum
    pub fn icon(&self) -> Option<String> {
        self.inner.icon.clone()
    }

    /// Returns the summary text briefly describing the notification.
    pub fn summary(&self) -> String {
        self.inner.summary.clone()
    }

    /// Returns optional detailed body text. Can be empty.
    pub fn body(&self) -> String {
        self.inner.body.clone()
    }

    /// Returns vector of action handles. Can be empty.
    pub fn actions(&self) -> Vec<ActionHandle> {
        self.inner
            .actions
            .iter()
            .map(|a| ActionHandle {
                inner: a.clone(),
                service: self.service.clone(),
            })
            .collect()
    }

    /// Returns the urgency level of the notification.
    pub fn urgency(&self) -> Urgency {
        self.inner.urgency
    }

    /// Returns the expire timeout of the notification.
    pub fn timeout(&self) -> i32 {
        self.inner.timeout
    }

    /// Dismisses this notification.
    ///
    /// # Errors
    /// It is a shortcut to [`NotificationService::dismiss_notification`] and therefore returns the
    /// same errors.
    pub async fn dismiss(&self) -> Result<()> {
        self.service.dismiss_notification(self.id()).await?;
        Ok(())
    }
}
