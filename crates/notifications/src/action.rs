use crate::private_prelude::*;

#[derive(Serialize, Deserialize, Debug)]
pub(crate) struct Action {
    pub(crate) notification_id: u32,
    pub(crate) label: String,
    pub(crate) action_key: String,
}

/// A handle which represents a notification action.
///
/// Notification actions are typically presented as buttons in UI that allow user to
/// interact with the application which sent the notification.
#[derive(Clone, Debug)]
pub struct ActionHandle {
    pub(crate) inner: Arc<Action>,
    pub(crate) service: NotificationService,
}

impl ActionHandle {
    /// Returns the ID of the notification this action belongs to.
    pub fn notification_id(&self) -> u32 {
        self.inner.notification_id
    }

    /// Returns the localized string which should be displayed to the user.
    pub fn label(&self) -> String {
        self.inner.label.clone()
    }

    /// Returns the identifier of the action.
    ///
    /// `"default"` means that the action is default.
    pub fn action_key(&self) -> String {
        self.inner.action_key.clone()
    }

    /// Invoke the action.
    ///
    /// It is a shortcut to [`NotificationService::invoke_action`].
    ///
    /// # Errors
    /// Returns [`Error::DBusError`]
    pub async fn invoke(&self) -> Result<()> {
        self.service
            .invoke_action(self.inner.notification_id, &self.inner.action_key)
            .await?;

        Ok(())
    }
}
