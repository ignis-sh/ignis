#ifndef __ACTION_H__
#define __ACTION_H__

#include <glib-object.h>
#include <gio/gio.h>

G_BEGIN_DECLS

/**
 * IgnisNotificationsGLibAction:
 *
 * An object that represents a notification action.
 * 
 * # Action
 *
 * Notification actions are typically presented as buttons in UI that allow user to
 * interact with the application which sent the notification.
 *
 * Since: 0.1
 */
#define IGNIS_NOTIFICATIONS_GLIB_TYPE_ACTION    (ignis_notifications_glib_action_get_type())

G_DECLARE_FINAL_TYPE (IgnisNotificationsGLibAction, ignis_notifications_glib_action, IGNIS_NOTIFICATIONS_GLIB, ACTION, GObject)

/**
 * ignis_notifications_glib_action_invoke_async:
 * @self: a `IgnisNotificationsGLibAction`
 * @cancellable: (nullable): a `GCancellable` to cancel the task, can be `NULL` 
 * @callback: (scope async) (closure user_data): callback to invoke when the operation is complete 
 * @user_data: data to pass to @callback
 *
 * Invokes this action.
 *
 * Since: 0.1
 */
void        ignis_notifications_glib_action_invoke_async  (IgnisNotificationsGLibAction * self, GCancellable *cancellable, GAsyncReadyCallback callback, gpointer user_data);

/**
 * ignis_notifications_glib_action_invoke_finish:
 * @self: a `IgnisNotificationsGLibService`
 * @result: a `GAsyncResult`
 * @error: return location for a [enum@IgnisNotificationsGLib.Error] error
 *
 * Finishes call to [method@IgnisNotificationsGLib.Action.invoke_finish].
 * 
 * Returns: %TRUE on success.
 *
 * Since: 0.1
 */
gboolean    ignis_notifications_glib_action_invoke_finish (IgnisNotificationsGLibAction * self, GAsyncResult *result, GError **error);

/**
 * ignis_notifications_glib_action_get_notification_id:
 * @self: a `IgnisNotificationsGLibAction`
 *
 * Returns the ID of the notification this action belongs to.
 *
 * Returns: The ID of the notification.
 *
 * Since: 0.1
 */
guint32 ignis_notifications_glib_action_get_notification_id(IgnisNotificationsGLibAction* self);

/**
 * ignis_notifications_glib_action_get_label:
 * @self: a `IgnisNotificationsGLibAction`
 *
 * Returns the localized string which should be displayed to the user.
 *
 * Returns: (transfer full): The label.
 *
 * Since: 0.1
 */
gchar* ignis_notifications_glib_action_get_label(IgnisNotificationsGLibAction* self);

/**
 * ignis_notifications_glib_action_get_action_key:
 * @self: a `IgnisNotificationsGLibAction`
 *
 * Returns the identifier of the action.
 *
 * `"default"` means that the action is default.
 *
 * Returns: (transfer full): The action key.
 *
 * Since: 0.1
 */
gchar* ignis_notifications_glib_action_get_action_key(IgnisNotificationsGLibAction* self);

G_END_DECLS

#endif
