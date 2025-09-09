from ignis.gobject import DataGObject, IgnisSignal, IgnisProperty
from typing import Any, Literal

MATCH_DICT = {
    "refreshRate": "refresh_rate",
    "dpmsStatus": "dpms_status",
    "activelyTearing": "actively_tearing",
    "directScanoutTo": "direct_scanout_to",
    "currentFormat": "current_format",
    "mirrorOf": "mirror_of",
    "availableModes": "available_modes",
}


class HyprlandMonitor(DataGObject):
    """
    A monitor.
    """

    def __init__(self):
        super().__init__(match_dict=MATCH_DICT)

        self._id: int = -1
        self._name: str = ""
        self._description: str = ""
        self._make: str = ""
        self._model: str = ""
        self._serial: str = ""
        self._width: int = -1
        self._height: int = -1
        self._refresh_rate: int = -1
        self._x: int = -1
        self._y: int = -1
        self._active_workspace_id: int = -1
        self._active_workspace_name: str = ""
        self._special_workspace_id: int = -1
        self._special_workspace_name: str = ""
        self._reserved: tuple[int, int, int, int] = (-1, -1, -1, -1)
        self._scale: float = -1
        self._transform: int = -1
        self._focused: bool = False
        self._dpms_status: bool = False
        self._vrr: bool = False
        self._solitary: str = ""
        self._actively_tearing: bool = False
        self._direct_scanout_to: str = ""
        self._disabled: bool = False
        self._current_format: str = ""
        self._mirror_of: str = ""
        self._available_modes: list[str] = []

    @IgnisSignal
    def removed(self):
        """
        Emitted when the monitor has been removed.
        """

    def sync(self, data: dict[str, Any]) -> None:
        """
        :meta private:
        """

        def replace_ws(type_: Literal["active", "special"]) -> None:
            ws = data.pop(f"{type_}Workspace", None)
            if ws:
                data[f"{type_}_workspace_id"] = ws["id"]
                data[f"{type_}_workspace_name"] = ws["name"]

        replace_ws("active")
        replace_ws("special")

        super().sync(data)

    @IgnisProperty
    def id(self) -> int:
        """
        The ID of the monitor.
        """
        return self._id

    @IgnisProperty
    def name(self) -> str:
        """
        The name of the monitor.
        """
        return self._name

    @IgnisProperty
    def description(self) -> str:
        """
        The description of the monitor.
        """
        return self._description

    @IgnisProperty
    def make(self) -> str:
        """
        The make of the monitor.
        """
        return self._make

    @IgnisProperty
    def model(self) -> str:
        """
        The model of the monitor.
        """
        return self._model

    @IgnisProperty
    def serial(self) -> str:
        """
        The serial of the monitor.
        """
        return self._serial

    @IgnisProperty
    def width(self) -> int:
        """
        The width of the monitor.
        """
        return self._width

    @IgnisProperty
    def height(self) -> int:
        """
        The height of the monitor.
        """
        return self._height

    @IgnisProperty
    def refresh_rate(self) -> int:
        """
        The refresh rate of the monitor.
        """
        return self._refresh_rate

    @IgnisProperty
    def x(self) -> int:
        """
        The `x` coordinate of the monitor.
        """
        return self._x

    @IgnisProperty
    def y(self) -> int:
        """
        The `y` coordinate of the monitor.
        """
        return self._y

    @IgnisProperty
    def active_workspace_id(self) -> int:
        """
        The ID of the active workspace on this monitor.
        """
        return self._active_workspace_id

    @IgnisProperty
    def active_workspace_name(self) -> str:
        """
        The name of the active workspace on this monitor.
        """
        return self._active_workspace_name

    @IgnisProperty
    def special_workspace_id(self) -> int:
        """
        The ID of the special workspace on this monitor.
        """
        return self._special_workspace_id

    @IgnisProperty
    def special_workspace_name(self) -> str:
        """
        The name of the special workspace on this monitor.
        """
        return self._special_workspace_name

    @IgnisProperty
    def reserved(self) -> tuple[int, int, int, int]:
        """
        Reserved.
        """
        return self._reserved

    @IgnisProperty
    def scale(self) -> float:
        """
        The scale of the monitor.
        """
        return self._scale

    @IgnisProperty
    def transform(self) -> int:
        """
        The transform value (how the monitor is rotated).
        """
        return self._transform

    @IgnisProperty
    def focused(self) -> bool:
        """
        Whether the monitor is focused.
        """
        return self._focused

    @IgnisProperty
    def dpms_status(self) -> bool:
        """
        Whether DPMS (Display Power Management Signaling) is on.
        """
        return self._dpms_status

    @IgnisProperty
    def vrr(self) -> bool:
        """
        Whether VRR (Variable Refresh Rate) is on.
        """
        return self._vrr

    @IgnisProperty
    def solitary(self) -> str:
        """
        The solitary status.
        """
        return self._solitary

    @IgnisProperty
    def actively_tearing(self) -> bool:
        """
        Whether the monitor is actively tearing.
        """
        return self._actively_tearing

    @IgnisProperty
    def direct_scanout_to(self) -> str:
        """
        The direct scanout status.
        """
        return self._direct_scanout_to

    @IgnisProperty
    def disabled(self) -> bool:
        """
        Whether the monitor is disabled.
        """
        return self._disabled

    @IgnisProperty
    def current_format(self) -> str:
        """
        The current format of the monitor.
        """
        return self._current_format

    @IgnisProperty
    def mirror_of(self) -> str:
        """
        The name of another display that the monitor is mirroring, or `"none"`.
        """
        return self._mirror_of

    @IgnisProperty
    def available_modes(self) -> list[str]:
        """
        A list of available modes.
        """
        return self._available_modes
