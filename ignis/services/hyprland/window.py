from ignis.gobject import IgnisProperty, DataGObject, IgnisSignal
from typing import Any

MATCH_DICT = {
    "class": "class_name",
    "initialClass": "initial_class",
    "initialTitle": "initial_title",
    "fullscreenClient": "fullscreen_client",
    "focusHistoryID": "focus_history_id",
    "inhibitingIdle": "inhibiting_idle",
}


class HyprlandWindow(DataGObject):
    """
    A window.
    """

    def __init__(self):
        super().__init__(match_dict=MATCH_DICT)

        self._address: str = ""
        self._mapped: bool = False
        self._hidden: bool = False
        self._at: tuple[int, int] = (-1, -1)
        self._size: tuple[int, int] = (-1, -1)
        self._workspace_id: int = -1
        self._workspace_name: str = ""
        self._floating: bool = False
        self._pseudo: bool = False
        self._monitor: int = -1
        self._class_name: str = ""
        self._title: str = ""
        self._initial_class: str = ""
        self._initial_title: str = ""
        self._pid: int = -1
        self._xwayland: bool = False
        self._pinned: bool = False
        self._fullscreen: int = -1
        self._fullscreen_client: int = -1
        self._grouped: list = []
        self._tags: list = []
        self._swallowing: str = ""
        self._focus_history_id: int = -1
        self._inhibiting_idle: bool = False

    def sync(self, data: dict[str, Any]) -> None:
        """
        :meta private:
        """
        workspace = data.pop("workspace", None)
        if workspace:
            data["workspace_id"] = workspace["id"]
            data["workspace_name"] = workspace["name"]
        super().sync(data)

    @IgnisSignal
    def closed(self):
        """
        Emitted when the window has been closed.
        """

    @IgnisProperty
    def address(self) -> str:
        """
        The address of the window.
        """
        return self._address

    @IgnisProperty
    def mapped(self) -> bool:
        """
        Whether the window is mapped.
        """
        return self._mapped

    @IgnisProperty
    def hidden(self) -> bool:
        """
        Whether the window is hidden.
        """
        return self._hidden

    @IgnisProperty
    def at(self) -> tuple[int, int]:
        """
        The coordinates of the window (e.g., ``(1280, 920)``).
        """
        return self._at

    @IgnisProperty
    def size(self) -> tuple[int, int]:
        """
        The size of the window (e.g., ``(1280, 920)``).
        """
        return self._size

    @IgnisProperty
    def workspace_id(self) -> int:
        """
        The ID of the workspace where the window is placed.
        """
        return self._workspace_id

    @IgnisProperty
    def workspace_name(self) -> str:
        """
        The name of the workspace where the window is placed.
        """
        return self._workspace_name

    @IgnisProperty
    def floating(self) -> bool:
        """
        Whether the window is floating.
        """
        return self._floating

    @IgnisProperty
    def pseudo(self) -> bool:
        """
        Whether the window is pseudo.
        """
        return self._pseudo

    @IgnisProperty
    def monitor(self) -> int:
        """
        The ID of the monitor where the window is placed.
        """
        return self._monitor

    @IgnisProperty
    def class_name(self) -> str:
        """
        The class name of the window.
        """
        return self._class_name

    @IgnisProperty
    def title(self) -> str:
        """
        The title of the window.
        """
        return self._title

    @IgnisProperty
    def initial_class(self) -> str:
        """
        The initial class name of the window.
        """
        return self._initial_class

    @IgnisProperty
    def initial_title(self) -> str:
        """
        The initial title of the window.
        """
        return self._initial_title

    @IgnisProperty
    def pid(self) -> int:
        """
        The PID of the window.
        """
        return self._pid

    @IgnisProperty
    def xwayland(self) -> bool:
        """
        Whether the window is running through Xwayland.
        """
        return self._xwayland

    @IgnisProperty
    def pinned(self) -> bool:
        """
        Whether the window is pinned.
        """
        return self._pinned

    @IgnisProperty
    def fullscreen(self) -> int:
        """
        The fullscreen mode.
        """
        return self._fullscreen

    @IgnisProperty
    def fullscreen_client(self) -> int:
        """
        Fullscreen client.
        """
        return self._fullscreen_client

    @IgnisProperty
    def grouped(self) -> list:
        """
        Grouped.
        """
        return self._grouped

    @IgnisProperty
    def tags(self) -> list:
        """
        Tags.
        """
        return self._tags

    @IgnisProperty
    def swallowing(self) -> str:
        """
        Swallowing.
        """
        return self._swallowing

    @IgnisProperty
    def focus_history_id(self) -> int:
        """
        The focus history ID.
        """
        return self._focus_history_id

    @IgnisProperty
    def inhibiting_idle(self) -> bool:
        """
        The inhibiting idle status.
        """
        return self._inhibiting_idle
