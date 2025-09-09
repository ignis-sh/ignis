from ignis.dbus import DBusService
from ignis import utils
from ignis.gobject import IgnisGObject, IgnisProperty, IgnisSignal
from .action import NotificationAction


class Notification(IgnisGObject):
    """
    A notification object.
    Contains data about the notification and allows performing actions.
    """

    def __init__(
        self,
        dbus: DBusService,
        id: int,
        app_name: str,
        icon: str | None,
        summary: str,
        body: str,
        actions: list[str],
        urgency: int,
        timeout: int,
        time: float,
        popup: bool,
    ):
        super().__init__()

        self.__dbus = dbus
        self._id = id
        self._app_name = app_name
        self._icon = icon
        self._summary = summary
        self._body = body
        self._timeout = timeout
        self._time = time
        self._urgency = urgency
        self._popup = popup
        self._actions = [
            NotificationAction(
                id=str(actions[i]),
                label=str(actions[i + 1]),
                dbus=self.__dbus,
                notification=self,
            )
            for i in range(0, len(actions), 2)
        ]

        utils.Timeout(timeout, self.dismiss)

    @IgnisSignal
    def closed(self):
        """
        Emitted when notification has been closed.
        """

    @IgnisSignal
    def dismissed(self):
        """
        Emitted when notification has been dismissed.
        """

    @IgnisProperty
    def id(self) -> int:
        """
        The ID of the notification.
        """
        return self._id

    @IgnisProperty
    def app_name(self) -> str:
        """
        The name of the application that sent the notification.
        """
        return self._app_name

    @IgnisProperty
    def icon(self) -> str | None:
        """
        The icon name, path to image or ``None``.
        """
        return self._icon

    @IgnisProperty
    def summary(self) -> str:
        """
        The summary text of the notification, usually the title.
        """
        return self._summary

    @IgnisProperty
    def body(self) -> str:
        """
        The body text of the notification, usually containing additional information.
        """
        return self._body

    @IgnisProperty
    def actions(self) -> list["NotificationAction"]:
        """
        A list of actions associated with the notification.
        """
        return self._actions

    @IgnisProperty
    def timeout(self) -> int:
        """
        The timeout for the notification.
        Usually equal to the ``popup_timeout`` property of the :class:`~ignis.services.NotificationService` unless the notification specifies otherwise.
        """
        return self._timeout

    @IgnisProperty
    def time(self) -> float:
        """
        Time in POSIX format when the notification was sent.
        """
        return self._time

    @IgnisProperty
    def urgency(self) -> int:
        """
        The urgency of the notification.

        Levels:
            - -1: Not provided
            - 0: Low
            - 1: Normal
            - 2: Critical
        """
        return self._urgency

    @IgnisProperty
    def popup(self) -> bool:
        """
        Whether the notification is a popup.
        """
        return self._popup

    @IgnisProperty
    def json(self) -> dict:
        """
        The notification data in dictionary format.
        """
        return {
            "id": self._id,
            "app_name": self._app_name,
            "icon": self._icon,
            "summary": self._summary,
            "body": self._body,
            "actions": [j for i in self._actions for j in (i.id, i.label)],
            "timeout": self._timeout,
            "time": self._time,
            "urgency": self._urgency,
        }

    def close(self) -> None:
        """
        Close the notification.
        This will remove it from notifications history.
        """
        self.emit("closed")

    def dismiss(self) -> None:
        """
        Dismiss the notification.
        """
        if self._popup:
            self._popup = False
            self.emit("dismissed")
            self.notify("popup")
