from ignis.gobject import IgnisGObject, IgnisProperty, IgnisSignal
from .ethernet_device import EthernetDevice
from ._imports import NM


class Ethernet(IgnisGObject):
    """
    The class for controlling Ethernet devices.
    """

    def __init__(self, client: NM.Client):
        super().__init__()
        self._client = client
        self._devices: dict[NM.Device, EthernetDevice] = {}

        self._client.connect("device-added", self.__add_device)
        self._client.connect("device-removed", self.__remove_device)

        self._connected_ids: dict[NM.Device, int] = {}

        for device in self._client.get_devices():
            self.__add_device(None, device, False)

    @IgnisSignal
    def new_device(self, device: EthernetDevice):
        """
        Emitted when a new Ethernet device is added.

        Args:
            device: An instance of the device.
        """

    @IgnisProperty
    def devices(self) -> list[EthernetDevice]:
        """
        A list of Ethernet devices.
        """
        return list(self._devices.values())

    @IgnisProperty
    def is_connected(self) -> bool:
        """
        Whether at least one Ethernet device is connected to the network.
        """
        for i in self.devices:
            if i.is_connected:
                return True
        return False

    @IgnisProperty
    def icon_name(self) -> str:
        """
        The general icon name for all devices, depends on ``is_connected`` property.
        """
        if self.is_connected:
            return "network-wired-symbolic"
        else:
            return "network-wired-disconnected-symbolic"

    def __add_device(self, client, device: NM.Device, emit: bool = True) -> None:
        if device in self._connected_ids:
            _id = self._connected_ids.pop(device)
            IgnisGObject.disconnect(
                device, _id
            )  # disconnect() is overrided in NM.Device

        if device.get_device_type() != NM.DeviceType.ETHERNET:
            return

        if len(device.get_available_connections()) == 0:
            _id = device.connect(
                "notify::available-connections",
                lambda x, y: self.__add_device(client, device),
            )
            self._connected_ids[device] = _id
            return

        obj = EthernetDevice(device, self._client)  # type: ignore
        obj.connect(
            "notify::is-connected",
            lambda x, y: self.notify_list("is-connected", "icon-name"),
        )
        self._devices[device] = obj

        device.connect(
            "notify::available-connections",
            lambda x, y: self.__remove_device_on_zero_available_connections(device),
        )

        if emit:
            self.emit("new-device", obj)
            self.notify("devices")

    def __remove_device_on_zero_available_connections(self, device: NM.Device) -> None:
        if device.get_available_connections() == 0:
            self.__remove_device(None, device)

    def __remove_device(self, client, device: NM.Device) -> None:
        if device.get_device_type() != NM.DeviceType.ETHERNET:
            return

        try:
            obj = self._devices.pop(device)
            obj.emit("removed")
            self.notify("devices")
        except KeyError:
            pass
