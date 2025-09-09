from ignis.base_service import BaseService
from ignis.gobject import IgnisProperty
from ._imports import NM
from .wifi import Wifi
from .ethernet import Ethernet
from .vpn import Vpn


class NetworkService(BaseService):
    """
    A Network service. Uses ``NetworkManager``.
    """

    def __init__(self):
        super().__init__()
        self._client = NM.Client.new(None)
        self._wifi = Wifi(self._client)
        self._ethernet = Ethernet(self._client)
        self._vpn = Vpn(self._client)

    @IgnisProperty
    def wifi(self) -> Wifi:
        """
        The Wi-Fi object.
        """
        return self._wifi

    @IgnisProperty
    def ethernet(self) -> Ethernet:
        """
        The Ethernet object.
        """
        return self._ethernet

    @IgnisProperty
    def vpn(self) -> Vpn:
        """
        The Vpn object.
        """
        return self._vpn
