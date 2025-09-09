from ignis.gobject import IgnisGObject, IgnisProperty, IgnisSignal
from ignis.connection_manager import ConnectionManager
from typing import Literal
from ._imports import Gvc
from .constants import SPEAKER_ICON_TEMPLATE, MICROPHONE_ICON_TEMPLATE


class Stream(IgnisGObject):
    """
    An audio stream.
    A general class for speakers, microphones, applications, and recorders.

    Raises:
        GvcNotFoundError: If Gvc is not found.
    """

    def __init__(self, control: Gvc.MixerControl, stream: "Gvc.MixerStream | None"):
        super().__init__()
        self._conn_mgr = ConnectionManager()
        self._control = control
        self._stream = stream

        self._setup()

    def _setup(self) -> None:
        if not self._stream:
            return

        for property_name in [
            "application_id",
            "id",
            "name",
            "description",
            "is-muted",
            "volume",
        ]:
            self._conn_mgr.connect(
                self._stream,
                f"notify::{property_name}",
                lambda *_, property_name=property_name: self.notify(property_name),
            )
        self._conn_mgr.connect(
            self._stream, "notify::volume", lambda *_: self.notify("icon_name")
        )
        self._conn_mgr.connect(
            self._stream, "notify::is-muted", lambda *_: self.notify("icon_name")
        )

        self.notify_all()

    def _remove(self) -> None:
        self._conn_mgr.disconnect_all()
        self.emit("removed")

    @IgnisSignal
    def removed(self):
        """
        Emitted when the stream has been removed.
        """

    @IgnisProperty
    def stream(self) -> "Gvc.MixerStream | None":
        """
        An instance of ``Gvc.MixerStream``.
        """
        return self._stream

    @IgnisProperty
    def application_id(self) -> str:
        """
        The application ID, or ``""`` if unknown.
        """
        if not self._stream:
            return ""

        return self._stream.get_application_id()

    @IgnisProperty
    def icon_name(self) -> str:
        """
        The current icon name, depending on ``volume`` and ``is_muted`` properties.
        Works only for speakers and microphones.
        """
        if isinstance(self.stream, Gvc.MixerSink):
            template = SPEAKER_ICON_TEMPLATE
        elif isinstance(self.stream, Gvc.MixerSource):
            template = MICROPHONE_ICON_TEMPLATE
        else:
            return "image-missing"

        if self.is_muted:
            return template.format("muted")
        elif self.volume > 67:
            return template.format("high")
        elif self.volume > 33:
            return template.format("medium")
        else:
            return template.format("low")

    @IgnisProperty
    def id(self) -> int:
        """
        The ID of the stream, or ``-1`` if unknown.
        """
        if not self._stream:
            return -1

        return self._stream.get_id()

    @IgnisProperty
    def name(self) -> str:
        """
        The name of the stream, or ``""`` if unknown.
        """
        if not self._stream:
            return ""

        return self._stream.get_name()

    @IgnisProperty
    def description(self) -> str:
        """
        The description of the stream, or ``""`` if unknown.
        """
        if not self._stream:
            return ""

        return self._stream.get_description()

    @IgnisProperty
    def is_muted(self) -> bool:
        """
        Whether the stream is muted.
        """
        if not self._stream:
            return False

        return self._stream.get_is_muted()

    @is_muted.setter
    def is_muted(self, value: bool) -> None:
        self._stream.set_is_muted(value)
        self._stream.change_is_muted(value)

    @IgnisProperty
    def volume(self) -> float:
        """
        The current volume of the stream, or ``-1.0`` if unknown.
        """
        if not self._stream:
            return -1.0

        return round(self._stream.get_volume() / self._control.get_vol_max_norm() * 100)

    @volume.setter
    def volume(self, value: float):
        if not self._stream:
            return None

        self._stream.set_volume(value * self._control.get_vol_max_norm() / 100)
        self._stream.push_volume()

    @IgnisProperty
    def is_default(self) -> bool:
        """
        Whether the stream is default.
        Works only for speakers and microphones.
        """
        if isinstance(self.stream, Gvc.MixerSink):
            default_stream = self._control.get_default_sink()
        elif isinstance(self.stream, Gvc.MixerSource):
            default_stream = self._control.get_default_source()
        else:
            return False

        if not default_stream:
            return False

        return default_stream.get_id() == self.id


class DefaultStream(Stream):
    """
    :meta private:
    """

    def __init__(self, control: Gvc.MixerControl, _type: Literal["sink", "source"]):
        super().__init__(control, None)
        self._type = _type

    def _sync(self) -> None:
        stream = getattr(self._control, f"get_default_{self._type}")()
        if not stream:
            return
        self._stream = stream
        self._setup()
