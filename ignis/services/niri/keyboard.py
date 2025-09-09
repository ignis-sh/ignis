from ignis.gobject import IgnisProperty, DataGObject


class NiriKeyboardLayouts(DataGObject):
    """
    Configured keyboard layouts.
    """

    def __init__(self, service):
        super().__init__()
        self.__service = service
        self._names: list = []
        self._current_idx: int = -1

    @IgnisProperty
    def names(self) -> list:
        """
        XKB names of the configured layouts.
        """
        return self._names

    @IgnisProperty
    def current_idx(self) -> int:
        """
        Index of the currently active layout in names.
        """
        return self._current_idx

    @IgnisProperty
    def current_name(self) -> str:
        """
        Name of the currently active layout.
        """
        return self._names[self._current_idx]

    def switch_layout(self, layout: str) -> None:
        """
        Switch the keyboard layout.

        Args:
            layout: The layout to switch to (``Next``, ``Prev`` or a valid id)
        """
        cmd = {"Action": {"SwitchLayout": {"layout": layout}}}
        self.__service.send_command(cmd)
