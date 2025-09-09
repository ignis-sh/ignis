from ignis.gobject import IgnisGObject, IgnisProperty, IgnisSignal
from ._imports import NM
from .wifi_device import WifiDevice


class Wifi(IgnisGObject):
    """
    The class for controlling Wi-Fi devices.
    """

    def __init__(self, client: NM.Client):
        super().__init__()
        self._client = client
        self._devices: dict[NM.Device, WifiDevice] = {}

        self._client.connect(
            "notify::wireless-enabled",
            lambda *args: self.notify_list("enabled", "icon-name", "is-connected"),
        )
        self._client.connect("device-added", self.__add_device)
        self._client.connect("device-removed", self.__remove_device)

        for device in self._client.get_devices():
            self.__add_device(None, device, False)

    @IgnisSignal
    def new_device(self, device: WifiDevice):
        """
        Emitted when a new Wi-FI device is added.

        Args:
            device: An instance of the device.
        """

    @IgnisProperty
    def devices(self) -> list[WifiDevice]:
        """
        A list of Wi-Fi devices.
        """
        return list(self._devices.values())

    @IgnisProperty
    def is_connected(self) -> bool:
        """
        Whether at least one Wi-Fi device is connected to the network.
        """
        for i in self.devices:
            if i.is_connected:
                return True
        return False

    @IgnisProperty
    def icon_name(self) -> str:
        """
        The icon name of the first device in the list.
        """
        result = None
        for i in self.devices:
            if i.ap.icon_name != "network-wireless-offline-symbolic":
                result = i.ap.icon_name

        if not result:
            return "network-wireless-offline-symbolic"
        else:
            return result

    @IgnisProperty
    def enabled(self) -> bool:
        """
        Whether Wi-Fi is enabled.
        """
        return self._client.wireless_get_enabled()

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._client.wireless_set_enabled(value)

    def __add_device(self, client, device: NM.Device, emit: bool = True) -> None:
        if device.get_device_type() != NM.DeviceType.WIFI:
            return

        obj = WifiDevice(device, self._client)  # type: ignore
        obj.ap.connect(
            "notify::icon-name",
            lambda x, y: self.notify("icon-name"),
        )
        obj.ap.connect(
            "notify::is-connected",
            lambda x, y: self.notify("is-connected"),
        )
        self._devices[device] = obj

        if emit:
            self.emit("new-device", obj)
            self.notify("devices")

    def __remove_device(self, client, device: NM.Device) -> None:
        if device.get_device_type() != NM.DeviceType.WIFI:
            return

        try:
            obj = self._devices.pop(device)
            obj.emit("removed")
            self.notify("devices")
        except KeyError:
            pass
