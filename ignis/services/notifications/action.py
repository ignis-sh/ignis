from ignis.dbus import DBusService
from gi.repository import GLib  # type: ignore
from ignis.gobject import IgnisGObject, IgnisProperty


class NotificationAction(IgnisGObject):
    """
    A simple object that contains data about a notification action.
    """

    def __init__(self, dbus: DBusService, notification, id: str, label: str):
        super().__init__()
        self.__dbus = dbus
        self.__notification = notification
        self._id = id
        self._label = label

    @IgnisProperty
    def id(self) -> str:
        """
        The ID of the action.
        """
        return self._id

    @IgnisProperty
    def label(self) -> str:
        """
        The label of the notification. This one should be displayed to user.
        """
        return self._label

    def invoke(self) -> None:
        """
        Invoke this action.
        """
        self.__dbus.emit_signal(
            "ActionInvoked", GLib.Variant("(us)", (self.__notification.id, self.id))
        )
