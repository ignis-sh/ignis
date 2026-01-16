from typing import Any

from ignis.gobject import DataGObject, IgnisProperty, IgnisSignal


class NiriCast(DataGObject):
    """
    A Cast.
    """

    def __init__(self, service):
        super().__init__()

        self._service = service
        self._stream_id: int = -1
        self._session_id: int = -1
        self._kind: str = ""
        self._target: dict = {}
        self._is_dynamic_target: bool = False
        self._is_active: bool = False
        self._pid: int = -1
        self._pw_node_id: int = -1

    @IgnisSignal
    def destroyed(self):
        """
        Emitted when the cast has been destroyed.
        """

    @IgnisProperty
    def stream_id(self) -> int:
        """
        Stream ID of the screencast that uniquely identifies it.
        """
        return self._stream_id

    @IgnisProperty
    def session_id(self) -> int:
        """
        Session ID of the screencast.
        """
        return self._session_id

    @IgnisProperty
    def kind(self) -> str:
        """
        Kind of this screencast.
        """
        return self._kind

    @IgnisProperty
    def target(self) -> dict:
        """
        Target being captured.
        """
        return self._target

    @IgnisProperty
    def is_dynamic_target(self) -> bool:
        """
        Whether this is a Dynamic Cast Target screencast.
        """
        return self._is_dynamic_target

    @IgnisProperty
    def is_active(self) -> bool:
        """
        Whether the cast is currently streaming frames.
        """
        return self._is_active

    @IgnisProperty
    def pid(self) -> int:
        """
        Process ID of the screencast consumer, if known.
        """
        return self._pid

    @IgnisProperty
    def pw_node_id(self) -> int:
        """
        PipeWire node ID of the screencast stream.
        """
        return self._pw_node_id
