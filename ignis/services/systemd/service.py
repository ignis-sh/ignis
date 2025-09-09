from __future__ import annotations
import os
from ignis.dbus import DBusProxy
from ignis import utils
from ignis.base_service import BaseService
from ignis.gobject import IgnisProperty
from typing import Literal
from .unit import SystemdUnit


class SystemdService(BaseService):
    """
    A service for managing systemd units through DBus.

    The default behaviour is to operate on the systemd `user` bus.
    To operate on the `system` bus, use ``.get_default("system")``.

    Example usage:

    .. code-block:: python

        from ignis.services.systemd import SystemdService

        systemd_session = SystemdService.get_default()

        example_unit = systemd_session.get_unit("wluma.service")
        example_unit.connect("notify::is-active", lambda x, y: print(example_unit.is_active))

        systemd_system = SystemdService.get_default("system")

        system_example_unit = systemd_system.get_unit("sshd.service")
        system_example_unit.start()

    """

    _session_instance: SystemdService | None = None
    _system_instance: SystemdService | None = None

    def __init__(self, bus_type: Literal["session", "system"] = "session") -> None:
        super().__init__()

        self._bus_type = bus_type

        self._proxy = DBusProxy.new(
            name="org.freedesktop.systemd1",
            object_path="/org/freedesktop/systemd1",
            interface_name="org.freedesktop.systemd1.Manager",
            info=utils.load_interface_xml("org.freedesktop.systemd1.Manager"),
            bus_type=bus_type,
        )

    @classmethod
    def get_default(  # type: ignore
        cls: SystemdService, bus_type: Literal["session", "system"] = "session"
    ) -> SystemdService:
        """
        Returns the default Service object for this process, creating it if necessary.

        Args:
            bus_type: The bus type.

        Bus types:
            - session: current user session
            - system: entire system, requires interactive authorization when calling methods
        """
        if bus_type not in ("session", "system"):
            raise TypeError(f"Invalid bus type: {bus_type}")

        instance_attr = f"_{bus_type}_instance"

        if getattr(cls, instance_attr) is None:
            setattr(cls, instance_attr, cls(bus_type))  # type: ignore
        return getattr(cls, instance_attr)

    @IgnisProperty
    def bus_type(self) -> Literal["session", "system"]:
        """
        The bus type.
        """
        return self._bus_type

    @IgnisProperty
    def units(self) -> list[SystemdUnit]:
        """
        A list of all systemd units on the bus.
        """
        units = []
        for item in self._proxy.gproxy.ListUnitFiles():
            unit_name = os.path.basename(item[0])
            if "@" not in unit_name:
                units.append(self.get_unit(unit_name))

        return units

    def get_unit(self, unit: str) -> SystemdUnit:
        """
        Get :class:`~ignis.services.systemd.SystemdUnit` by the unit name.

        Args:
            unit: The name of the unit to get.

        Returns:
            :class:`~ignis.services.systemd.SystemdUnit`
        """
        object_path = self._proxy.gproxy.LoadUnit("(s)", unit)
        return SystemdUnit(object_path, self._bus_type)
