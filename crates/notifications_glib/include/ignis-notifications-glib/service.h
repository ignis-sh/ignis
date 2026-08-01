#ifndef __SERVICE_H__
#define __SERVICE_H__

#include <glib-object.h>
#include <gio/gio.h>

G_BEGIN_DECLS

// Usually properties and signals are documented in C sources
// but we just do it here

/**
 * IgnisNotificationsGLibService:notifications:
 *
 * The `GListStore` containing notifications.
 */

/**
 * IgnisNotificationsGLibService:follow-xdg-timeout:
 *
 * Whether to respect XDG Specification for timeout.
 *
 * If set to `FALSE`, notifications never expire despite the value of [property@IgnisNotificationsGLibNotification:timeout].
 *
 * Otherwise, behavior is based on notification's timeout:
 *
 * - `-1` - timeout value is taken from [property@IgnisNotificationsGLibService:default-timeout].
 * - `0` - the notification never expire
 * - `>=0` - this timeout is used to expire the notification
 */

/**
 * IgnisNotificationsGLibService:default-timeout:
 *
 * The default timeout which is used when a notification doesn't specify timeout (-1).
 *
 * Has effect only if [property@IgnisNotificationsGLib.Service:follow_xdg_timeout] and [property@IgnisNotificationsGLibService:expire-by-default] are both `TRUE`.
 */

/**
 * IgnisNotificationsGLibService:expire-by-default:
 *
 * Whether to expire notifications if the timeout is not specified (when timeout is -1).
 *
 * If `True`, notifications expire after the timeout defined in [property@IgnisNotificationsGLib.Service:default-timeout].
 */

/**
 * IgnisNotificationsGLibService::notified:
 * @self: the #IgnisNotificationsGLibService
 * @id: The id of the notification
 * @notification: The `IgnisNotificationsGLibNotification` instance
 * @replace: Whether it replaces the old notification with the same ID
 *
 * A new notification was sent by an application.
 */

/**
 * IgnisNotificationsGLibService::closed:
 * @self: the #IgnisNotificationsGLibService
 * @id: The id of the notification
 * @reason: The reason why the notification was closed.
 *
 * A notification was closed.
 */

/**
 * IgnisNotificationsGLibService::notifications-cleared:
 * @self: the #IgnisNotificationsGLibService
 *
 * The notification history was cleared. 
 *
 * Emitted by a call to [method@IgnisNotificationsGLib.Service.clear_notifications_async].
 */

/**
 * IgnisNotificationsGLibService:
 * 
 * A notification daemon which follows XDG Desktop Notifications Specification.
 *
 * Since: 0.1
 */
#define IGNIS_NOTIFICATIONS_GLIB_TYPE_SERVICE    (ignis_notifications_glib_service_get_type())

G_DECLARE_FINAL_TYPE (IgnisNotificationsGLibService, ignis_notifications_glib_service, IGNIS_NOTIFICATIONS_GLIB, SERVICE, GObject)

/**
 * ignis_notifications_glib_service_new:
 *
 * Creates a new instance of service.
 *
 * If loading the notification history fails, an error is reported and the new instance is constructed without file I/O support.
 *
 * Returns: (transfer full): a newly created `Service`
 *
 * Since: 0.1
 */
IgnisNotificationsGLibService * ignis_notifications_glib_service_new         (void);


/**
 * ignis_notifications_glib_service_run_async:
 * @self: a `IgnisNotificationsGLibService`
 * @cancellable: (nullable): a `GCancellable` to cancel the operation, or %NULL
 * @callback: (scope async) (closure user_data): callback to invoke when the operation is complete
 * @user_data: data to pass to @callback
 *
 * Runs the service. Must be called only once.
 *
 * Fails if another notification daemon is running, the function was called twice or other D-Bus error occured.
 *
 * Since: 0.1
 */
void        ignis_notifications_glib_service_run_async  (IgnisNotificationsGLibService * self, GCancellable *cancellable, GAsyncReadyCallback callback, gpointer user_data);

/**
 * ignis_notifications_glib_service_run_finish:
 * @self: a `IgnisNotificationsGLibService`
 * @result: a `GAsyncResult`
 * @error: return location for a [enum@IgnisNotificationsGLib.Error] error
 *
 * Finishes call to [method@IgnisNotificationsGLib.Service.run_async].
 * 
 * Returns: %TRUE on success.
 *
 * Since: 0.1
 */
gboolean    ignis_notifications_glib_service_run_finish (IgnisNotificationsGLibService * self, GAsyncResult *result, GError **error);


/**
 * ignis_notifications_glib_service_get_notifications:
 * @self: a `IgnisNotificationsGLibService`
 *
 * Returns a list of notifications.
 *
 * Returns: (transfer container) (element-type IgnisNotificationsGLibNotification): A list of notifications.
 *
 * Since: 0.1
 */
GList* ignis_notifications_glib_service_get_notifications(IgnisNotificationsGLibService* self);


/**
 * ignis_notifications_glib_service_dismiss_notification_async:
 * @self: a `IgnisNotificationsGLibService`
 * @notification_id: The ID of the notification to dismiss.
 * @cancellable: (nullable): a `GCancellable` to cancel the operation, or %NULL
 * @callback: (scope async) (closure user_data): callback to invoke when the operation is complete
 * @user_data: data to pass to @callback
 *
 * Dismisses a notification by its ID.
 *
 * The notification is removed from the history and application that sent the notification is notified through D-Bus.
 *
 * Fails if notification is already removed.
 *
 * Since: 0.1
 */
void ignis_notifications_glib_service_dismiss_notification_async(IgnisNotificationsGLibService* self, guint32 notification_id, GCancellable* cancellable, GAsyncReadyCallback callback, gpointer user_data);

/**
 * ignis_notifications_glib_service_dismiss_notification_finish:
 * @self: a `IgnisNotificationsGLibService`
 * @result: a `GAsyncResult`
 * @error: return location for a [enum@IgnisNotificationsGLib.Error] error
 *
 * Finishes call to [method@IgnisNotificationsGLib.Service.dismiss_notification_finish].
 * 
 * Returns: %TRUE on success.
 *
 * Since: 0.1
 */
gboolean    ignis_notifications_glib_service_dismiss_notification_finish (IgnisNotificationsGLibService * self, GAsyncResult *result, GError **error);


/**
 * ignis_notifications_glib_service_invoke_action_async:
 * @self: a `IgnisNotificationsGLibService`
 * @notification_id: The ID of the notification.
 * @action_key: The key of the action.
 * @cancellable: (nullable): a `GCancellable` to cancel the operation, or %NULL
 * @callback: (scope async) (closure user_data): callback to invoke when the operation is complete
 * @user_data: data to pass to @callback
 *
 * Invokes an action by its action key and notification ID it belongs to.
 *
 * Since: 0.1
 */
void ignis_notifications_glib_service_invoke_action_async(IgnisNotificationsGLibService* self, guint32 notification_id, gchar* action_key, GCancellable* cancellable, GAsyncReadyCallback callback, gpointer user_data);

/**
 * ignis_notifications_glib_service_invoke_action_finish:
 * @self: a `IgnisNotificationsGLibService`
 * @result: a `GAsyncResult`
 * @error: return location for a [enum@IgnisNotificationsGLib.Error] error
 *
 * Finishes call to [method@IgnisNotificationsGLib.Service.invoke_action_async].
 * 
 * Returns: %TRUE on success.
 *
 * Since: 0.1
 */
gboolean    ignis_notifications_glib_service_invoke_action_finish (IgnisNotificationsGLibService * self, GAsyncResult *result, GError **error);

/**
 * ignis_notifications_glib_service_clear_notifications_async:
 * @self: a `IgnisNotificationsGLibService`
 * @cancellable: (nullable): a `GCancellable` to cancel the operation, or %NULL
 * @callback: (scope async) (closure user_data): callback to invoke when the operation is complete
 * @user_data: data to pass to @callback
 *
 * Clears the notification history.
 *
 * It dismisses each notification and notifies applications.
 *
 * # Warning
 *
 * It does **NOT** emit `closed` signal for each notification. It emits `notifications-cleared` instead.
 *
 * Since: 0.1
 */
void ignis_notifications_glib_service_clear_notifications_async(IgnisNotificationsGLibService* self, GCancellable* cancellable, GAsyncReadyCallback callback, gpointer user_data);

/**
 * ignis_notifications_glib_service_clear_notifications_finish:
 * @self: a `IgnisNotificationsGLibService`
 * @result: a `GAsyncResult`
 * @error: return location for a [enum@IgnisNotificationsGLib.Error] error
 *
 * Finishes call to [method@IgnisNotificationsGLib.Service.clear_notifications_async].
 * 
 * Returns: %TRUE on success.
 *
 * Since: 0.1
 */
gboolean    ignis_notifications_glib_service_clear_notifications_finish (IgnisNotificationsGLibService * self, GAsyncResult *result, GError **error);

G_END_DECLS

#endif /* __SERVICE_H__ */
