from gi.repository import GLib  # type: ignore
from ignis.gobject import IgnisGObject, IgnisProperty, IgnisSignal
from loguru import logger
from ._imports import GnomeBluetooth


class BluetoothDevice(IgnisGObject):
    """
    A Bluetooth device.
    """

    def __init__(
        self, client: GnomeBluetooth.Client, gdevice: GnomeBluetooth.Device
    ) -> None:
        super().__init__()

        self._client = client
        self._gdevice = gdevice

        for prop_name in [
            "address",
            "alias",
            "battery-level",
            "battery-percentage",
            "connected",
            "name",
            "paired",
            "trusted",
        ]:
            gdevice.connect(
                f"notify::{prop_name}",
                lambda x, y, prop_name=prop_name: self.notify(prop_name),
            )
        gdevice.connect("notify::icon", lambda x, y: self.notify("icon-name"))

    @IgnisSignal
    def removed(self):
        """
        Emitted when the device has been removed.
        """

    @IgnisProperty
    def gdevice(self) -> GnomeBluetooth.Device:
        """
        The instance of ``GnomeBluetooth.Device`` for this device.
        """
        return self._gdevice

    @IgnisProperty
    def address(self) -> str:
        """
        The Bluetooth device address of the device.
        """
        return self._gdevice.props.address

    @IgnisProperty
    def alias(self) -> str:
        """
        The name alias for the device.
        """
        return self._gdevice.props.alias

    @IgnisProperty
    def battery_level(self) -> int:
        """
        The current battery level of the device (if available).
        """
        return self._gdevice.props.battery_level

    @IgnisProperty
    def battery_percentage(self) -> float:
        """
        The current battery percentage of the device (if available).
        """
        return self._gdevice.props.battery_percentage

    @IgnisProperty
    def connectable(self) -> bool:
        """
        Whether it is possible to connect to the device.
        """
        return self._gdevice.props.connectable

    @IgnisProperty
    def connected(self) -> bool:
        """
        Whether the device is currently connected.
        """
        return self._gdevice.props.connected

    @IgnisProperty
    def icon_name(self) -> str:
        """
        The current icon name of the device.
        """
        return self._gdevice.props.icon

    @IgnisProperty
    def name(self) -> str:
        """
        The complete device name. It is better to use the ``alias`` property when displaying the device name.
        """
        return self._gdevice.props.name

    @IgnisProperty
    def paired(self) -> bool:
        """
        Whether the device is paired.
        """
        return self._gdevice.props.paired

    @IgnisProperty
    def trusted(self) -> bool:
        """
        Whether the remote is seen as trusted.
        """
        return self._gdevice.props.trusted

    @IgnisProperty
    def device_type(self) -> str:
        """
        The type of the device, e.g., ``"mouse"``, ``"speakers"``.

        For more device types, see `GnomeBluetooth.Type <https://lazka.github.io/pgi-docs/index.html#GnomeBluetooth-3.0/flags.html#GnomeBluetooth.Type>`_.
        """
        return GnomeBluetooth.type_to_string(self._gdevice.props.type)  # type: ignore

    async def __connect_service(self, connect: bool) -> None:
        try:
            await self._client.connect_service(self._gdevice.get_object_path(), connect)  # type: ignore
        except GLib.Error as gerror:
            logger.warning(gerror.message)

    async def connect_to(self) -> None:
        """
        Connect to this device.
        """
        await self.__connect_service(True)

    async def disconnect_from(self) -> None:
        """
        Disconnect from this device.
        """
        await self.__connect_service(False)
