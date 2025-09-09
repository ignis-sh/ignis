import os
from ignis.base_service import BaseService
from .device import BacklightDevice
from .constants import SYS_BACKLIGHT
from ignis import utils
from ignis.gobject import IgnisProperty


class BacklightService(BaseService):
    """
    A backlight service.
    Allows controlling device screen brightness.

    Example Usage:

    .. code-block:: python

        from ignis.services.backlight import BacklightService

        backlight = BacklightService.get_default()

        print(backlight.brightness)
        print(backlight.max_brightness)
        print(backlight.available)

        backlight.set_brightness(30) # set brightness to 30 on all devices

        # backlight.devices[1].set_brightness(50) # set brightness to 50 on the second device in the list
    """

    def __init__(self):
        super().__init__()

        self._devices: list[BacklightDevice] = []

        # FIXME: not working
        utils.FileMonitor(
            path=SYS_BACKLIGHT,
            callback=lambda x, path, event_type: self.__sync_devices()
            if event_type == "deleted" or event_type == "created"
            else None,
        )

        self.__sync_devices()

    def __sync_devices(self) -> None:
        self._devices = []

        for device_name in os.listdir(SYS_BACKLIGHT):
            self._devices.append(BacklightDevice(device_name))

        if len(self._devices) > 0:
            self._devices[0].connect(
                "notify::brightness",
                lambda x, y: self.notify("brightness"),
            )

        self.notify_all()

    @IgnisProperty
    def available(self) -> bool:
        """
        Whether there are controllable backlight devices.
        """
        return len(self._devices) > 0

    @IgnisProperty
    def devices(self) -> list[BacklightDevice]:
        """
        A list of all backlight devices.
        """
        return self._devices

    @IgnisProperty
    def brightness(self) -> int:
        """
        The current brightness of the first backlight device in the list, ``-1`` if there are no backlight devices.
        Setting this property will set provided brightness on ALL backlight devices.
        """
        if len(self._devices) > 0:
            return self._devices[0].brightness
        else:
            return -1

    @brightness.setter
    def brightness(self, value: int) -> None:
        for device in self._devices:
            device.brightness = value

    async def set_brightness_async(self, value: int) -> None:
        """
        Asynchronously set brightness for all devices.

        Args:
            value: The value to set.
        """
        for device in self._devices:
            await device.set_brightness_async(value)

    @IgnisProperty
    def max_brightness(self) -> int:
        """
        The maximum brightness allowed by the first backlight device in the list, ``-1`` if there are no backlight devices.
        """
        if len(self._devices) > 0:
            return self._devices[0].max_brightness
        else:
            return -1
