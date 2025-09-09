import asyncio
from ignis.dbus import DBusProxy
from ignis import utils
from ignis.base_service import BaseService
from ignis.gobject import IgnisProperty, IgnisSignal
from .player import MprisPlayer


class MprisService(BaseService):
    """
    A service for controlling media players using the MPRIS interface.

    Example usage:

    .. code-block:: python

        from ignis.services.mpris import MprisService

        mpris = MprisService.get_default()

        mpris.connect("player_added", lambda x, player: print(player.desktop_entry, player.title))
    """

    def __init__(self):
        super().__init__()
        self._players: dict[str, MprisPlayer] = {}

        self.__dbus = DBusProxy.new(
            name="org.freedesktop.DBus",
            object_path="/org/freedesktop/DBus",
            interface_name="org.freedesktop.DBus",
            info=utils.load_interface_xml("org.freedesktop.DBus"),
        )

        self.__dbus.signal_subscribe(
            signal_name="NameOwnerChanged",
            callback=lambda *args: asyncio.create_task(self.__init_player(args[5][0])),
        )

        asyncio.create_task(self.__get_players())

    async def __get_players(self) -> None:
        all_names = self.__dbus.ListNames()
        for name in all_names:
            await self.__init_player(name)

    async def __init_player(self, name: str) -> None:
        if (
            name.startswith("org.mpris.MediaPlayer2")
            and name not in self._players
            and name != "org.mpris.MediaPlayer2.playerctld"
        ):
            player = await MprisPlayer.new_async(name)

            self._players[name] = player
            player.connect("closed", lambda x: self.__remove_player(name))
            self.emit("player_added", player)
            self.notify("players")

    def __remove_player(self, name: str) -> None:
        if name in self._players:
            self._players.pop(name)
            self.notify("players")

    @IgnisSignal
    def player_added(self, player: MprisPlayer):
        """
        Emitted when a player has been added.

        Args:
            player: The instance of the player.
        """
        pass

    @IgnisProperty
    def players(self) -> list[MprisPlayer]:
        """
        A list of currently active players.
        """
        return list(self._players.values())
