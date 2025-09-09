from gi.repository import Gio, GLib  # type: ignore
from ignis.dbus import DBusProxy
from ignis import utils
from loguru import logger
from ignis.gobject import IgnisGObject, IgnisProperty
from typing import Literal


class SystemdUnit(IgnisGObject):
    """
    An object tracking a single systemd unit.

    """

    def __init__(self, object_path: str, bus_type: Literal["session", "system"]):
        super().__init__()

        if bus_type == "system":
            self._flags = Gio.DBusCallFlags.ALLOW_INTERACTIVE_AUTHORIZATION
        else:
            self._flags = Gio.DBusCallFlags.NONE

        self._proxy = DBusProxy.new(
            name="org.freedesktop.systemd1",
            object_path=object_path,
            interface_name="org.freedesktop.systemd1.Unit",
            info=utils.load_interface_xml("org.freedesktop.systemd1.Unit"),
            bus_type=bus_type,
        )

        self._proxy.gproxy.connect("g-properties-changed", self.__sync)

    def __handle_result(self, proxy, result, user_data) -> None:
        if isinstance(result, GLib.Error):
            logger.warning(
                f"[Systemd Service] Start/stop/restart request failed: {result.message}"
            )

    def __sync(self, proxy, properties: GLib.Variant, invalidated_properties) -> None:
        prop_dict = properties.unpack()

        if "ActiveState" in prop_dict.keys():
            self.notify("is-active")

    @IgnisProperty
    def name(self) -> str:
        """
        The name of the unit.
        """
        return self._proxy.Id

    @IgnisProperty
    def is_active(self) -> bool:
        """
        Whether the unit is active (running).
        """
        state = self._proxy.ActiveState
        if state == "active":
            return True
        else:
            return False

    def start(self) -> None:
        """
        Start this unit.
        """
        self._proxy.Start(
            "(s)",
            "replace",
            flags=self._flags,
        )

    async def start_async(self) -> None:
        """
        Asynchronous version of :func:`start`.
        """
        await self._proxy.StartAsync(
            "(s)",
            "replace",
            flags=self._flags,
        )

    def stop(self) -> None:
        """
        Stop this unit.
        """
        self._proxy.Stop(
            "(s)",
            "replace",
            flags=self._flags,
        )

    async def stop_async(self) -> None:
        """
        Asynchronous version of :func:`stop`.
        """
        await self._proxy.StopAsync(
            "(s)",
            "replace",
            flags=self._flags,
        )

    def restart(self) -> None:
        """
        Restart this unit.
        """
        self._proxy.Restart(
            "(s)",
            "replace",
            flags=self._flags,
        )

    async def restart_async(self) -> None:
        """
        Asynchronous version of :func:`restart`.
        """
        await self._proxy.RestartAsync(
            "(s)",
            "replace",
            flags=self._flags,
        )
