import asyncio
from ignis import utils
from ignis.dbus import DBusService, DBusProxy
from gi.repository import Gio, GLib  # type: ignore
from ignis.base_service import BaseService
from .item import SystemTrayItem
from ignis.exceptions import AnotherSystemTrayRunningError
from ignis.gobject import IgnisProperty, IgnisSignal


class SystemTrayService(BaseService):
    """
    A system tray, where application icons are placed.

    Raises:
        AnotherSystemTrayRunningError: If another system tray is already running.

    Example usage:

    .. code-block:: python

        from ignis.services.system_tray import SystemTrayService

        system_tray = SystemTrayService.get_default()

        system_tray.connect("added", lambda x, item: print(item.title))
    """

    def __init__(self):
        super().__init__()
        self._items: dict[str, SystemTrayItem] = {}
        self._init_item_tasks: list[str] = []

        self.__dbus: DBusService = DBusService(
            name="org.kde.StatusNotifierWatcher",
            object_path="/StatusNotifierWatcher",
            info=utils.load_interface_xml("org.kde.StatusNotifierWatcher"),
            on_name_lost=self.__on_name_lost,
        )

        self.__dbus.register_dbus_property(
            name="ProtocolVersion", method=self.__ProtocolVersion
        )
        self.__dbus.register_dbus_property(
            name="IsStatusNotifierHostRegistered",
            method=self.__IsStatusNotifierHostRegistered,
        )
        self.__dbus.register_dbus_property(
            name="RegisteredStatusNotifierItems",
            method=self.__RegisteredStatusNotifierItems,
        )

        self.__dbus.register_dbus_method(
            name="RegisterStatusNotifierItem", method=self.__RegisterStatusNotifierItem
        )

    def __on_name_lost(self, *args) -> None:
        proxy = DBusProxy.new(
            name="org.kde.StatusNotifierWatcher",
            interface_name="org.kde.StatusNotifierWatcher",
            object_path="/StatusNotifierWatcher",
            info=utils.load_interface_xml("org.kde.StatusNotifierWatcher"),
        )
        name = proxy.gproxy.get_name_owner()
        raise AnotherSystemTrayRunningError(name)

    @IgnisSignal
    def added(self, item: SystemTrayItem):
        """
        Emitted when a new item is added.

        Args:
            item: The instance of the system tray item.
        """

    @IgnisProperty
    def items(self) -> list[SystemTrayItem]:
        """
        A list of system tray items.
        """
        return list(self._items.values())

    def __ProtocolVersion(self) -> GLib.Variant:
        return GLib.Variant("i", 0)

    def __IsStatusNotifierHostRegistered(self) -> GLib.Variant:
        return GLib.Variant("b", True)

    def __RegisteredStatusNotifierItems(self) -> GLib.Variant:
        return GLib.Variant("as", list(self._items.keys()))

    def __RegisterStatusNotifierItem(
        self, invocation: Gio.DBusMethodInvocation, service: str
    ) -> None:
        if service.startswith("/"):
            object_path = service
            bus_name = invocation.get_sender()

        else:
            object_path = "/StatusNotifierItem"
            bus_name = service

        invocation.return_value(None)

        if bus_name in self._items:
            return

        if bus_name in self._init_item_tasks:
            return

        asyncio.create_task(self.__initialize_item(bus_name, object_path))

        self._init_item_tasks.append(bus_name)

    async def __initialize_item(self, bus_name: str, object_path: str) -> None:
        item = await SystemTrayItem.new_async(bus_name, object_path)

        if not item:
            return

        self._items[bus_name] = item
        item.connect("removed", self.__remove_item, bus_name)
        self.emit("added", item)
        self.notify("items")
        self.__dbus.emit_signal(
            "StatusNotifierItemRegistered",
            GLib.Variant("(s)", (bus_name + object_path,)),
        )

        try:
            self._init_item_tasks.remove(bus_name)
        except ValueError:
            pass

    def __remove_item(self, x, bus_name: str) -> None:
        self._items.pop(bus_name)
        self.notify("items")
        self.__dbus.emit_signal(
            "StatusNotifierItemUnregistered", GLib.Variant("(s)", (bus_name,))
        )
