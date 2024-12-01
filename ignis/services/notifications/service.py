import os
import json
from ignis.dbus import DBusService, DBusProxy
from gi.repository import GLib, GObject, GdkPixbuf  # type: ignore
from ignis.utils import Utils
from loguru import logger
from ignis.services.options import OptionsService
from datetime import datetime
from ignis.base_service import BaseService
from .notification import Notification
from .constants import (
    NOTIFICATIONS_CACHE_DIR,
    NOTIFICATIONS_CACHE_FILE,
    NOTIFICATIONS_EMPTY_CACHE_FILE,
    NOTIFICATIONS_IMAGE_DATA,
)
from ignis.exceptions import AnotherNotificationDaemonRunningError


class NotificationService(BaseService):
    """
    A notification daemon.
    Allow receiving notifications and perform actions on them.

    Raises:
        AnotherNotificationDaemonRunningError: If another notification daemon is already running.

    Example usage:

    .. code-block:: python

        from ignis.services.notifications import NotificationsService

        notifications = NotificationsService.get_default()

        notifications.connect("notified", lambda x, notification: print(notification.app_name, notification.summary))
    """

    def __init__(self):
        super().__init__()

        self.__dbus = DBusService(
            name="org.freedesktop.Notifications",
            object_path="/org/freedesktop/Notifications",
            info=Utils.load_interface_xml("org.freedesktop.Notifications"),
            on_name_lost=self.__on_name_lost,
        )

        self.__dbus.register_dbus_method(
            name="GetServerInformation", method=self.__GetServerInformation
        )
        self.__dbus.register_dbus_method(
            name="GetCapabilities", method=self.__GetCapabilities
        )
        self.__dbus.register_dbus_method(
            name="CloseNotification", method=self.__CloseNotification
        )
        self.__dbus.register_dbus_method(name="Notify", method=self.__Notify)

        self._id: int = 0
        self._notifications: dict[int, Notification] = {}
        self._popups: dict[int, Notification] = {}

        os.makedirs(NOTIFICATIONS_CACHE_DIR, exist_ok=True)
        os.makedirs(NOTIFICATIONS_IMAGE_DATA, exist_ok=True)

        options = OptionsService.get_default()

        opt_group = options.create_group(name="notifications", exists_ok=True)

        self._dnd_opt = opt_group.create_option(
            name="dnd", default=False, exists_ok=True
        )
        self._popup_timeout_opt = opt_group.create_option(
            name="timeout", default=5000, exists_ok=True
        )
        self._max_popups_count_opt = opt_group.create_option(
            name="max_popups_count", default=3, exists_ok=True
        )

        self.__load_notifications()

    def __on_name_lost(self, *args) -> None:
        proxy = DBusProxy(
            name="org.freedesktop.Notifications",
            interface_name="org.freedesktop.Notifications",
            object_path="/org/freedesktop/Notifications",
            info=Utils.load_interface_xml("org.freedesktop.Notifications"),
        )
        try:
            info = proxy.GetServerInformation()
            name = info[0]
        except Exception:  # notification daemon can simply not implement GetServerInformation method, or do it wrongly, so we except all errors
            name = proxy.proxy.get_name_owner()

        raise AnotherNotificationDaemonRunningError(name)

    @GObject.Signal(arg_types=(Notification,))
    def notified(self, *args):
        """
        - Signal

        Emitted when a new notification appears.

        Args:
            notification (:class:`~ignis.services.notifications.Notification`): The instance of the notification.
        """

    @GObject.Signal(arg_types=(Notification,))
    def new_popup(self, *args):
        """
        - Signal

        Emitted when a new popup notification appears.
        Only emitted if ``dnd`` is set to ``False``.

        Args:
            notification (:class:`~ignis.services.notifications.Notification`): The instance of the notification.
        """

    @GObject.Property
    def notifications(self) -> list[Notification]:
        """
        - read-only

        A list of all notifications.
        """
        return list(self._notifications.values())

    @GObject.Property
    def popups(self) -> list[Notification]:
        """
        - read-only

        A list of currently active popup notifications.
        """
        return list(self._popups.values())

    @GObject.Property
    def dnd(self) -> bool:
        """
        - read-write

        Do Not Disturb mode.
        If set to ``True``, the ``new_popup`` signal will not be emitted,
        and all new :class:`~ignis.services.notifications.Notification` instances will have ``popup`` set to ``False``.

        Default: ``False``.
        """
        return self._dnd_opt.value

    @dnd.setter
    def dnd(self, value: bool) -> None:
        self._dnd_opt.value = value

    @GObject.Property
    def popup_timeout(self) -> int:
        """
        - read-write

        The timeout before a popup is automatically dismissed, in milliseconds.

        Default: ``5000``.
        """
        return self._popup_timeout_opt.value

    @popup_timeout.setter
    def popup_timeout(self, value: int) -> None:
        self._popup_timeout_opt.value = value

    @GObject.Property
    def max_popups_count(self) -> int:
        """
        - read-write

        The Maximum number of popups.
        If the length of the ``popups`` list exceeds ``max_popups_count``, the oldest popup will be dismissed.

        Default: ``3``.
        """
        return self._max_popups_count_opt.value

    @max_popups_count.setter
    def max_popups_count(self, value: int) -> None:
        self._max_popups_count_opt.value = value

    def __GetServerInformation(self, *args) -> GLib.Variant:
        return GLib.Variant(
            "(ssss)",
            ("Ignis Notifications Service", "linkfrg", "1.0", "1.2"),
        )

    def __GetCapabilities(self, *args) -> GLib.Variant:
        return GLib.Variant(
            "(as)", (["actions", "body", "icon-static", "persistence"],)
        )

    def __CloseNotification(self, invocation, id: int) -> None:
        notification = self.get_notification(id)
        if notification:
            notification.close()

    def get_notification(self, id: int) -> Notification | None:
        """
        Get :class:`~ignis.services.notifications.Notification` by ID.

        Args:
            id: The ID of the notification to get.

        Returns:
            :class:`~ignis.services.notifications.Notification` or ``None``
        """
        return self._notifications.get(id, None)

    def __Notify(
        self,
        invocation,
        app_name: str,
        replaces_id: int,
        app_icon: str,
        summary: str,
        body: str,
        actions: list,
        hints: dict,
        timeout: int,
    ) -> GLib.Variant:
        def _init(_id: int) -> None:
            self.__init_notification(
                _id=_id,
                app_name=app_name,
                app_icon=app_icon,
                summary=summary,
                body=body,
                actions=actions,
                hints=hints,
                timeout=timeout,
            )

        if replaces_id == 0:
            _id = self._id = self._id + 1
            _init(_id)

        else:
            _id = replaces_id
            old_notification = self.get_notification(replaces_id)
            if old_notification:
                old_notification.close()
                old_notification.connect("closed", lambda x: _init(_id))
            else:
                _init(_id)

        return GLib.Variant("(u)", (_id,))

    def __init_notification(
        self,
        _id: int,
        app_name: str,
        app_icon: str,
        summary: str,
        body: str,
        actions: list,
        hints: dict,
        timeout: int,
    ) -> None:
        icon = None

        if isinstance(app_icon, str):
            icon = app_icon

        if "image-data" in hints:
            icon = f"{NOTIFICATIONS_IMAGE_DATA}/{_id}"
            self.__save_pixbuf(hints["image-data"], icon)

        notification = Notification(
            dbus=self.__dbus,
            id=_id,
            app_name=app_name,
            icon=icon,
            summary=summary,
            body=body,
            actions=actions,
            urgency=hints.get("urgency", 1),
            timeout=self.popup_timeout if timeout == -1 else timeout,
            time=datetime.now().timestamp(),
            popup=not self.dnd,
        )

        if len(self.popups) >= self.max_popups_count:
            if not self.max_popups_count == 0:
                self.popups[-1].dismiss()

        if notification.popup:
            self._popups[notification.id] = notification
            self.emit("new_popup", notification)
            self.notify("popups")

        self.__add_notification(notification)
        self.__sync()
        self.emit("notified", notification)
        self.notify("notifications")

    def __save_pixbuf(self, px_args: list, save_path: str) -> None:
        GdkPixbuf.Pixbuf.new_from_bytes(
            width=px_args[0],
            height=px_args[1],
            has_alpha=px_args[3],
            data=GLib.Bytes.new(px_args[6]),
            colorspace=GdkPixbuf.Colorspace.RGB,
            rowstride=px_args[2],
            bits_per_sample=px_args[4],
        ).savev(save_path, "png")

    def clear_all(self) -> None:
        """
        Clear all notifications.
        """
        for notify in self.notifications:
            notify.close()

    def __close_notification(self, notification: Notification) -> None:
        self._notifications.pop(notification.id)
        if notification.popup:
            notification.dismiss()
        self.__sync()

        self.__dbus.emit_signal(
            "NotificationClosed", GLib.Variant("(uu)", (notification.id, 2))
        )

        self.notify("notifications")

    def __dismiss_popup(self, notification: Notification) -> None:
        if self._popups.get(notification.id, None):
            self._popups.pop(notification.id)
            self.notify("popups")

    def __sync(self) -> None:
        data = {
            "id": self._id,
            "notifications": [n.json for n in self.notifications],
        }
        with open(NOTIFICATIONS_CACHE_FILE, "w") as file:
            json.dump(data, file, indent=2)

    def __add_notification(self, notification: Notification) -> None:
        notification.connect("closed", lambda x: self.__close_notification(x))
        notification.connect("dismissed", lambda x: self.__dismiss_popup(x))
        self._notifications[notification.id] = notification

    def __load_notifications(self) -> None:
        try:
            with open(NOTIFICATIONS_CACHE_FILE) as file:
                log_file = json.load(file)

            for n in log_file.get("notifications", []):
                notification = Notification(**n, popup=False, dbus=self.__dbus)
                self.__add_notification(notification)

            self._id = log_file.get("id", 0)

        except Exception:
            logger.warning("Notification history file is corrupted! Cleaning...")
            with open(NOTIFICATIONS_CACHE_FILE, "w") as file:
                json.dump(NOTIFICATIONS_EMPTY_CACHE_FILE, file, indent=2)
