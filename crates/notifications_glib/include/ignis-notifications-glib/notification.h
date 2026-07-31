#ifndef __NOTIFICATION_H__
#define __NOTIFICATION_H__

#include <glib-object.h>
#include <gio/gio.h>
#include <ignis-notifications-glib/urgency.h>

G_BEGIN_DECLS

/**
 * IgnisNotificationsGLibNotification::closed:
 * @self: The #IgnisNotificationsGLibNotification
 * @reason: The reason why the notification was closed
 *
 * This notification was closed.
 */

/** 
 * IgnisNotificationsGLibNotification:
 *
 * An object which represents a notification.
 *
 * Since: 0.1
 */
#define IGNIS_NOTIFICATIONS_GLIB_TYPE_NOTIFICATION (ignis_notifications_glib_notification_get_type())

G_DECLARE_FINAL_TYPE (IgnisNotificationsGLibNotification, ignis_notifications_glib_notification, IGNIS_NOTIFICATIONS_GLIB, NOTIFICATION, GObject)

/** 
 * ignis_notifications_glib_notification_get_id:
 * @self: a `IgnisNotificationsGLibNotification`
 *
 * Returns the unique non-zero identifer of the notification.
 *
 * Returns: The ID.
 *
 * Since: 0.1
 */
guint32 ignis_notifications_glib_notification_get_id (IgnisNotificationsGLibNotification* self); 

/** 
 * ignis_notifications_glib_notification_get_app_name:
 * @self: a `IgnisNotificationsGLibNotification`
 *
 * Returns the name of the application that sent the notification. Can be blank.
 *
 * Returns: (transfer full): The app name.
 *
 * Since: 0.1
 */
gchar* ignis_notifications_glib_notification_get_app_name (IgnisNotificationsGLibNotification* self); 

/** 
 * ignis_notifications_glib_notification_get_icon:
 * @self: a `IgnisNotificationsGLibNotification`
 *
 * Returns the optional icon of the notification.
 *
 * It is either file path or icon name.
 *
 * Returns: (transfer full): The icon.
 *
 * Since: 0.1
 */
gchar* ignis_notifications_glib_notification_get_icon (IgnisNotificationsGLibNotification* self); 

/** 
 * ignis_notifications_glib_notification_get_summary:
 * @self: a `IgnisNotificationsGLibNotification`
 *
 * Returns the summary text briefly describing the notification.
 *
 * Returns: (transfer full): The summary text.
 *
 * Since: 0.1
 */
gchar* ignis_notifications_glib_notification_get_summary (IgnisNotificationsGLibNotification* self); 

/**
 * ignis_notifications_glib_notification_get_body:
 * @self: a `IgnisNotificationsGLibNotification`
 *
 * Returns optional detailed body text. Can be empty.
 *
 * Returns: (transfer full): The body text.
 *
 * Since: 0.1
 */
gchar* ignis_notifications_glib_notification_get_body (IgnisNotificationsGLibNotification* self); 

/**
 * ignis_notifications_glib_notification_get_actions:
 * @self: a `IgnisNotificationsGLibNotification`
 *
 * Returns list of actions. Can be empty.
 *
 * Returns: (transfer full) (element-type IgnisNotificationsGLibAction): The list of actions.
 *
 * Since: 0.1
 */
GPtrArray* ignis_notifications_glib_notification_get_actions (IgnisNotificationsGLibNotification* self); 

/**
 * ignis_notifications_glib_notification_get_urgency:
 * @self: a `IgnisNotificationsGLibNotification`
 *
 * Returns the urgency level of the notification.
 *
 * Returns: the urgency level.
 *
 * Since: 0.1
 */
IgnisNotificationsGLibUrgency ignis_notifications_glib_notification_get_urgency (IgnisNotificationsGLibNotification* self); 

/**
 * ignis_notifications_glib_notification_get_timeout:
 * @self: a `IgnisNotificationsGLibNotification`
 *
 * Returns the expire timeout of the notification.
 *
 * Returns: The timeout in milliseconds.
 *
 * Since: 0.1
 */
gint32 ignis_notifications_glib_notification_get_timeout (IgnisNotificationsGLibNotification* self); 

/**
 * ignis_notifications_glib_notification_dismiss_async:
 * @self: a `IgnisNotificationsGLibNotification`
 * @cancellable: (nullable): a `GCancellable` to cancel the task or `NULL`
 * @callback: (scope async) (closure user_data): callback to call when the operation is complete
 * @user_data: user data to pass to @callback
 *
 * Dismisses this notification.
 *
 * Since: 0.1
 */
void        ignis_notifications_glib_notification_dismiss_async  (IgnisNotificationsGLibNotification * self, GCancellable *cancellable, GAsyncReadyCallback callback, gpointer user_data);

/**
 * ignis_notifications_glib_notification_dismiss_finish:
 * @self: a `IgnisNotificationsGLibService`
 * @result: a `GAsyncResult`
 * @error: return location for a [enum@IgnisNotificationsGLib.Error] error
 *
 * Finishes call to [method@IgnisNotificationsGLib.Notification.dismiss_async].
 * 
 * Returns: %TRUE on success.
 *
 * Since: 0.1
 */
gboolean    ignis_notifications_glib_notification_dismiss_finish (IgnisNotificationsGLibNotification * self, GAsyncResult *result, GError **error);

G_END_DECLS

#endif
