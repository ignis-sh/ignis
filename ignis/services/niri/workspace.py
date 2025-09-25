from ignis.gobject import IgnisProperty, IgnisSignal, DataGObject


class NiriWorkspace(DataGObject):
    """
    A workspace.
    """

    def __init__(self, service):
        super().__init__()
        self.__service = service
        self._id: int = -1
        self._idx: int = -1
        self._name: str = ""
        self._output: str = ""
        self._is_urgent: bool = False
        self._is_active: bool = False
        self._is_focused: bool = False
        self._active_window_id: int = -1

    @IgnisSignal
    def destroyed(self):
        """
        Emitted when the workspace has been destroyed.
        """

    @IgnisProperty
    def id(self) -> int:
        """
        The unique ID of the workspace.
        """
        return self._id

    @IgnisProperty
    def idx(self) -> int:
        """
        The index of the workspace on its monitor.
        """
        return self._idx

    @IgnisProperty
    def name(self) -> str:
        """
        The name of the workspace.
        """
        return self._name

    @IgnisProperty
    def output(self) -> str:
        """
        The name of the output on which the workspace is placed.
        """
        return self._output

    @IgnisProperty
    def is_urgent(self) -> bool:
        """
        Whether the workspace currently has an urgent window in its output.
        """
        return self._is_urgent

    @IgnisProperty
    def is_active(self) -> bool:
        """
        Whether the workspace is currently active on its output.
        """
        return self._is_active

    @IgnisProperty
    def is_focused(self) -> bool:
        """
        Whether the workspace is currently focused.
        """
        return self._is_focused

    @IgnisProperty
    def active_window_id(self) -> int:
        """
        The ID of the active window on this workspace.
        """
        return self._active_window_id

    def switch_to(self) -> None:
        """
        Switch to this workspace.
        """
        cmd = {"Action": {"FocusWorkspace": {"reference": {"Id": self._id}}}}
        self.__service.send_command(cmd)
