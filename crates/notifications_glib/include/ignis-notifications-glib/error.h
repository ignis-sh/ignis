#ifndef __ERROR_H_
#define __ERROR_H_

#include <glib-object.h>

G_BEGIN_DECLS

/**
 * IgnisNotificationsGLibError:
 * @IGNIS_NOTIFICATIONS_GLIB_ERROR_DBUS_ERROR: A D-Bus error.
 * @IGNIS_NOTIFICATIONS_GLIB_ERROR_NO_CONNECTION: Attempted to call methods that invole D-Bus interaction without the `IgnisNotificationsGLibService` running
 * @IGNIS_NOTIFICATIONS_GLIB_ERROR_IO_ERROR: I/O file errors
 * @IGNIS_NOTIFICATIONS_GLIB_ERROR_JSON_ERROR: JSON parsing of the notification history failed. Usually indicates that the JSON markup is corrupted
 * @IGNIS_NOTIFICATIONS_GLIB_ERROR_NOTIFICATION_NOT_FOUND: Notification with the given ID is not found
 * @IGNIS_NOTIFICATIONS_GLIB_ERROR_CONNECTION_INITIALIZED_TWICE: Attempted to run the service more than once
 *
 * Enum representing possible errors to occur in the `IgnisNotificationsGLibService`.
 *
 * Since: 0.1
 */
typedef enum IgnisNotificationsGLibError
{
  IGNIS_NOTIFICATIONS_GLIB_ERROR_DBUS_ERROR,
  IGNIS_NOTIFICATIONS_GLIB_ERROR_NO_CONNECTION,
  IGNIS_NOTIFICATIONS_GLIB_ERROR_IO_ERROR,
  IGNIS_NOTIFICATIONS_GLIB_ERROR_JSON_ERROR,
  IGNIS_NOTIFICATIONS_GLIB_ERROR_NOTIFICATION_NOT_FOUND,
  IGNIS_NOTIFICATIONS_GLIB_ERROR_CONNECTION_INITIALIZED_TWICE,
} IgnisNotificationsGLibError;

#define IGNIS_NOTIFICATIONS_GLIB_ERROR           (ignis_notifications_glib_error_quark())

GQuark ignis_notifications_glib_error_quark      (void);

G_END_DECLS

#endif /* __ERROR_H_ */
