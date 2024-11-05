import os
from ignis.gobject import IgnisGObject
from gi.repository import GObject  # type: ignore
from ignis.utils import Utils
from ignis.dbus import DBusProxy
from .constants import SYS_BACKLIGHT
from .util import get_session_path


class BacklightDevice(IgnisGObject):
    """
    A backlight device.
    """

    def __init__(self, device_name: str):
        super().__init__()
        self._device_name = device_name
        self._brightness: int = -1
        self._max_brightness: int = -1

        self._PATH_TO_BRIGHTNESS = os.path.join(
            SYS_BACKLIGHT, device_name, "brightness"
        )
        self._PATH_TO_MAX_BRIGHTNESS = os.path.join(
            SYS_BACKLIGHT, device_name, "max_brightness"
        )

        with open(self._PATH_TO_MAX_BRIGHTNESS) as backlight_file:
            self._max_brightness = int(backlight_file.read().strip())

        Utils.FileMonitor(
            path=self._PATH_TO_BRIGHTNESS,
            callback=lambda path, event_type: self.__sync_brightness()
            if event_type != "changed"  # "changed" event is called multiple times
            else None,
        )

        self.__session_proxy = DBusProxy(
            name="org.freedesktop.login1",
            object_path=get_session_path(),
            info=Utils.load_interface_xml("org.freedesktop.login1.Session"),
            interface_name="org.freedesktop.login1.Session",
            bus_type="system",
        )

        self.__sync_brightness()

    def __sync_brightness(self) -> None:
        with open(self._PATH_TO_BRIGHTNESS) as backlight_file:
            self._brightness = int(backlight_file.read().strip())

        self.notify("brightness")

    @GObject.Property
    def device_name(self) -> str:
        """
        - read-only

        The name of the directory in ``/sys/class/backlight``.
        """
        return self._device_name

    @GObject.Property
    def max_brightness(self) -> int:
        """
        - read-only

        The maximum brightness allowed by the device.
        """
        return self._max_brightness

    @GObject.Property
    def brightness(self) -> int:
        """
        - read-write

        The current brightness of the device.
        """
        return self._brightness

    @brightness.setter
    def brightness(self, value: int) -> None:
        self.__session_proxy.SetBrightness(
            "(ssu)",
            "backlight",
            self._device_name,
            value,
            result_handler=lambda *args: None,
        )
