from ignis.gobject import IgnisProperty, IgnisSignal, DataGObject
from .window_layout import NiriWindowLayout
from typing import Any


class NiriWindow(DataGObject):
    """
    A window.
    """

    def __init__(self, service):
        super().__init__()

        self.__service = service
        self._id: int = -1
        self._title: str = ""
        self._app_id: str = ""
        self._pid: int = -1
        self._workspace_id: int = -1
        self._is_focused: bool = False
        self._is_floating: bool = False
        self._is_urgent: bool = False
        self._layout: NiriWindowLayout = NiriWindowLayout()

    def sync(self, data: dict[str, Any]) -> None:
        """
        :meta private:
        """
        layout = data.pop("layout", None)

        if layout:
            if type(layout) is dict:
                self._layout.sync(layout)
            else:
                self._layout.sync(layout.data)

            self.notify("layout")

        super().sync(data)

    @IgnisSignal
    def destroyed(self):
        """
        Emitted when the window has been destroyed.
        """

    @IgnisProperty
    def id(self) -> int:
        """
        The unique ID of the window.
        """
        return self._id

    @IgnisProperty
    def title(self) -> str:
        """
        The title of the window.
        """
        return self._title

    @IgnisProperty
    def app_id(self) -> str:
        """
        Application ID of the window.
        """
        return self._app_id

    @IgnisProperty
    def pid(self) -> int:
        """
        The PID of the window.
        """
        return self._pid

    @IgnisProperty
    def workspace_id(self) -> int:
        """
        The ID of the workspace where the window is placed.
        """
        return self._workspace_id

    @IgnisProperty
    def is_focused(self) -> bool:
        """
        Whether the window is focused.
        """
        return self._is_focused

    @IgnisProperty
    def is_floating(self) -> bool:  # type: ignore
        """
        Whether the window is floating.
        """
        return self._is_floating

    @IgnisProperty
    def is_urgent(self) -> bool:
        """
        Whether this window requests your attention.
        """
        return self._is_urgent

    @IgnisProperty
    def layout(self) -> NiriWindowLayout:
        """
        The layout of the window.
        """
        return self._layout

    def close(self) -> None:
        """
        Close this window.
        """
        cmd = {"Action": {"CloseWindow": {"id": self._id}}}
        self.__service.send_command(cmd)

    def focus(self) -> None:
        """
        Focus this window.
        """
        cmd = {"Action": {"FocusWindow": {"id": self._id}}}
        self.__service.send_command(cmd)

    def toggle_fullscreen(self) -> None:
        """
        Toggle fullscreen on this window.
        """
        cmd = {"Action": {"FullscreenWindow": {"id": self._id}}}
        self.__service.send_command(cmd)

    def toggle_floating(self) -> None:
        """
        Move the window between the floating and the tiling layout.
        """
        cmd = {"Action": {"ToggleWindowFloating": {"id": self._id}}}
        self.__service.send_command(cmd)
