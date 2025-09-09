from ignis.gobject import IgnisGObject, IgnisProperty, IgnisSignal
from ._imports import NM
from .constants import STATE


class EthernetDevice(IgnisGObject):
    """
    An Ethernet device.
    """

    def __init__(self, device: NM.DeviceEthernet, client: NM.Client):
        super().__init__()
        self._device = device
        self._client = client
        self._name: str | None = None
        self._is_connected: bool = False

        self._connection: NM.RemoteConnection = (
            self._device.get_available_connections()[0]
        )
        setting_connection: NM.SettingConnection = (
            self._connection.get_setting_connection()
        )
        self._name = setting_connection.props.id

        self._device.connect("notify::active-connection", self.__update_is_connected)
        self.__update_is_connected()

    @IgnisSignal
    def removed(self):
        """
        Emitted when this Ethernet device is removed.
        """

    @IgnisProperty
    def carrier(self) -> bool:
        """
        Whether the device has a carrier.
        """
        return self._device.props.carrier

    @IgnisProperty
    def perm_hw_address(self) -> str:
        """
        The permanent hardware (MAC) address of the device.
        """
        return self._device.props.perm_hw_address

    @IgnisProperty
    def speed(self) -> int:
        """
        The speed of the device.
        """
        return self._device.props.speed

    @IgnisProperty
    def state(self) -> str | None:
        """
        The current state of the device or ``None`` if unknown.
        """
        return STATE.get(self._device.get_state(), None)

    @IgnisProperty
    def is_connected(self) -> bool:
        """
        Whether the device is connected to the network.
        """
        return self._is_connected

    @IgnisProperty
    def name(self) -> str | None:
        """
        The name of the connection or ``None`` if unknown.
        """
        return self._name

    async def connect_to(self) -> None:
        """
        Connect this Ethernet device to the network.
        """

        await self._client.activate_connection_async(  # type: ignore
            self._connection,
            self._device,
            None,
        )

    async def disconnect_from(self) -> None:
        """
        Disconnect this Ethernet device from the network.
        """
        if not self.is_connected:
            return

        await self._client.deactivate_connection_async(  # type: ignore
            self._device.get_active_connection(),
        )

    def __update_is_connected(self, *args) -> None:
        if not self._device.get_active_connection():
            self._is_connected = False
        else:
            self._is_connected = True
        self.notify("is-connected")
