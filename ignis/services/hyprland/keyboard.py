from ignis.gobject import IgnisProperty, DataGObject

MATCH_DICT = {
    "capsLock": "caps_lock",
    "numLock": "num_lock",
}


class HyprlandKeyboard(DataGObject):
    """
    A keyboard.
    """

    def __init__(self, service):
        super().__init__(match_dict=MATCH_DICT)
        self.__service = service
        self._address: str = ""
        self._name: str = ""
        self._rules: str = ""
        self._model: str = ""
        self._layout: str = ""
        self._variant: str = ""
        self._options: str = ""
        self._active_keymap: str = ""
        self._caps_lock: bool = False
        self._num_lock: bool = False
        self._main: bool = False

    @IgnisProperty
    def address(self) -> str:
        """
        The address of the keyboard.
        """
        return self._address

    @IgnisProperty
    def name(self) -> str:
        """
        The name of the keyboard.
        """
        return self._name

    @IgnisProperty
    def rules(self) -> str:
        """
        The rules of the keyboard.
        """
        return self._rules

    @IgnisProperty
    def model(self) -> str:
        """
        The model of the keyboard.
        """
        return self._model

    @IgnisProperty
    def layout(self) -> str:
        """
        The layout of the keyboard.
        """
        return self._layout

    @IgnisProperty
    def variant(self) -> str:
        """
        The variant of the keyboard.
        """
        return self._variant

    @IgnisProperty
    def options(self) -> str:
        """
        The options of the keyboard.
        """
        return self._options

    @IgnisProperty
    def active_keymap(self) -> str:
        """
        The currently active keymap of the keyboard.
        """
        return self._active_keymap

    @IgnisProperty
    def caps_lock(self) -> bool:
        """
        Whether Caps Lock is active.
        """
        return self._caps_lock

    @IgnisProperty
    def num_lock(self) -> bool:
        """
        Whether Num Lock is active.
        """
        return self._num_lock

    @IgnisProperty
    def main(self) -> bool:
        """
        Whether the keyboard is main.
        """
        return self._main

    def switch_layout(self, layout: str) -> None:
        """
        Switch the keyboard layout.

        Args:
            layout: The layout to switch to. For example: ``next``, ``prev``, ``0``, ``1``, etc.
        """
        self.__service.send_command(f"switchxkblayout {self.name} {layout}")
