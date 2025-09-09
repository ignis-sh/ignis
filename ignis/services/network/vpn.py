from ignis.gobject import IgnisGObject, IgnisProperty, IgnisSignal
from ._imports import NM
from .util import check_is_vpn


class VpnConnection(IgnisGObject):
    """
    A VPN connection.
    """

    def __init__(
        self, connection: "NM.Connection | NM.ActiveConnection", client: NM.Client
    ):
        super().__init__()
        self._connection = connection
        self._client = client

        active_uuids = [
            conn.get_uuid() for conn in self._client.get_active_connections()
        ]
        self._is_connected: bool = connection.get_uuid() in active_uuids

        self._client.connect("notify::active-connections", self.__update_is_connected)
        self.__update_is_connected()

    @IgnisSignal
    def removed(self):
        """
        Emitted when this VPN connection is removed.
        """

    @IgnisProperty
    def is_connected(self) -> bool:
        """
        Whether the device is connected to the network.
        """
        return self._is_connected

    @IgnisProperty
    def name(self) -> str | None:
        """
        The id (name) of the vpn connection or ``None`` if unknown.
        """
        return self._connection.get_id()

    async def toggle_connection(self) -> None:
        """
        Toggle this VPN depending on it's `is_connected` property
        """
        if self.is_connected:
            await self.disconnect_from()
        else:
            await self.connect_to()

    async def connect_to(self) -> None:
        """
        Connect to this VPN.
        """

        await self._client.activate_connection_async(
            self._connection,  # type: ignore
            None,
            None,
        )

    async def disconnect_from(self) -> None:
        """
        Disconnect from this VPN.
        """

        for conn in self._client.get_active_connections():
            if conn.get_uuid() == self._connection.get_uuid():
                await self._client.deactivate_connection_async(  # type: ignore
                    conn,
                )

    def __update_is_connected(self, *args) -> None:
        active_uuids = [
            conn.get_uuid() for conn in self._client.get_active_connections()
        ]
        self._is_connected = self._connection.get_uuid() in active_uuids

        self.notify("is-connected")


class Vpn(IgnisGObject):
    """
    The class for controlling VPN connections.
    """

    def __init__(self, client: NM.Client):
        super().__init__()
        self._client = client
        self._connections: dict[NM.Connection, VpnConnection] = {}
        self._active_connections: dict[NM.ActiveConnection, VpnConnection] = {}

        self._client.connect("active-connection-added", self.__add_active_connection)
        self._client.connect(
            "active-connection-removed", self.__remove_active_connection
        )
        self._client.connect("connection-added", self.__add_connection)
        self._client.connect("connection-removed", self.__remove_connection)

        for i in self._client.get_connections():
            self.__add_connection(None, i, False)

        for a in self._client.get_active_connections():
            self.__add_active_connection(None, a, False)

    @IgnisSignal
    def new_connection(self, connection: VpnConnection):
        """
        Emitted when a new VPN connection is added.

        Args:
            connection: An instance of the VPN connection.
        """

    @IgnisSignal
    def new_active_connection(self, connection: VpnConnection):
        """
        Emitted when a VPN connection is activated.

        Args:
            connection: An instance of the newly activated VPN connection.
        """

    @IgnisProperty
    def connections(self) -> list[VpnConnection]:
        """
        A list of all VPN connections.
        """
        return list(self._connections.values())

    @IgnisProperty
    def active_connections(self) -> list[VpnConnection]:
        """
        A list of active VPN connections.
        """
        return list(self._active_connections.values())

    @IgnisProperty
    def active_vpn_id(self) -> str | None:
        """
        The id (name) of the first active vpn connection.
        """
        if not self.is_connected:
            return None
        else:
            return self.active_connections[0].name

    @IgnisProperty
    def is_connected(self) -> bool:
        """
        Whether at least one VPN connection is active.
        """
        return len(self._active_connections) != 0

    @IgnisProperty
    def icon_name(self) -> str:
        """
        The general icon name for all vpn connections, depends on ``is_connected`` property.
        """
        if self.is_connected:
            return "network-vpn-symbolic"
        else:
            return "network-vpn-disconnected-symbolic"

    @check_is_vpn
    def __add_connection(
        self, client, connection: NM.Connection, emit: bool = True
    ) -> None:
        obj = VpnConnection(connection=connection, client=self._client)
        self._connections[connection] = obj

        if emit:
            self.emit("new-connection", obj)
            self.notify("connections")

    @check_is_vpn
    def __remove_connection(self, client, connection: NM.Connection) -> None:
        try:
            obj = self._connections.pop(connection)
            obj.emit("removed")
            self.notify("connections")
        except KeyError:
            pass

    @check_is_vpn
    def __add_active_connection(
        self, client, connection: NM.ActiveConnection, emit: bool = True
    ) -> None:
        obj = VpnConnection(connection=connection, client=self._client)
        obj.connect(
            "notify::is-connected",
            lambda x, y: self.notify_list("is-connected", "icon-name"),
        )

        self._active_connections[connection] = obj

        if emit:
            self.emit("new-active-connection", obj)
            self.notify("active-connections")
            self.notify("active-vpn-id")
            self.notify("is-connected")

    @check_is_vpn
    def __remove_active_connection(
        self, client, connection: NM.ActiveConnection
    ) -> None:
        try:
            obj = self._active_connections.pop(connection)
            obj.emit("removed")
            self.notify("active-connections")
            self.notify("active-vpn-id")
            self.notify("is-connected")
        except KeyError:
            pass
