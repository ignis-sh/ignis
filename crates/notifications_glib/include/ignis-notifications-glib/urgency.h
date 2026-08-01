#ifndef __IGNIS_NOTIFICATIONS_GLIB_URGENCY_H__
#define __IGNIS_NOTIFICATIONS_GLIB_URGENCY_H__

#include <glib-object.h>

G_BEGIN_DECLS

/**
 * IgnisNotificationsGLibUrgency:
 * @IGNIS_NOTIFICATIONS_GLIB_URGENCY_LOW: A low level of urgency. Notification does not require immediate user attention.
 * @IGNIS_NOTIFICATIONS_GLIB_URGENCY_NORMAL: A normal level of urgency. For example, a notification about new message from a chat app.
 * @IGNIS_NOTIFICATIONS_GLIB_URGENCY_CRITICAL: A critical level of urgency. The notification requires user attention and should stand out from the rest of notifications
 *
 * The urgency level of the notification.
 *
 * Represents how important is the notification and may affect how it's displayed in the graphical interface.
 *
 * Since: 0.1
 */
typedef enum IgnisNotificationsGLibUrgency
{
  IGNIS_NOTIFICATIONS_GLIB_URGENCY_LOW,
  IGNIS_NOTIFICATIONS_GLIB_URGENCY_NORMAL,
  IGNIS_NOTIFICATIONS_GLIB_URGENCY_CRITICAL,
} IgnisNotificationsGLibUrgency;

#define IGNIS_NOTIFICATIONS_GLIB_TYPE_URGENCY (ignis_notifications_glib_urgency_get_type())

GType   ignis_notifications_glib_urgency_get_type       (void);

G_END_DECLS

#endif
