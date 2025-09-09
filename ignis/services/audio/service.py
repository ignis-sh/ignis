from ignis.base_service import BaseService
from ignis.gobject import IgnisProperty, IgnisSignal
from ._imports import Gvc
from .stream import Stream, DefaultStream


class AudioService(BaseService):
    """
    An audio service.
    Allows controlling audio devices.

    Requires `ignis-gvc <https://github.com/ignis-sh/ignis-gvc>`_.

    .. warning::
        This service uses the PulseAudio backend.
        To use it with PipeWire, install ``pipewire-pulse``.

    Example usage:

    .. code-block:: python

        from ignis.services.audio import AudioService

        audio = AudioService.get_default()
        audio.connect("speaker-added", lambda x, speaker: print(speaker.description))
    """

    def __init__(self):
        super().__init__()

        self._control = Gvc.MixerControl(name="Ignis audio control")

        self._speaker = DefaultStream(control=self._control, _type="sink")
        self._microphone = DefaultStream(control=self._control, _type="source")

        self._streams: dict[int, Stream] = {}

        self._speakers: dict[int, Stream] = {}
        self._microphones: dict[int, Stream] = {}
        self._apps: dict[int, Stream] = {}
        self._recorders: dict[int, Stream] = {}

        self._control.connect("default-sink-changed", self.__default_changed, "speaker")
        self._control.connect(
            "default-source-changed", self.__default_changed, "microphone"
        )
        self._control.connect("stream-added", self.__add_stream)
        self._control.connect("stream-removed", self.__remove_stream)

        self._control.open()

    def __default_changed(self, x, y, _type: str) -> None:
        getattr(self, _type)._sync()
        for stream in getattr(self, f"{_type}s"):
            stream.notify("is_default")

    @IgnisSignal
    def speaker_added(self, stream: Stream):
        """
        Emitted when a speaker is added.

        Args:
            stream: The instance of the stream.
        """

    @IgnisSignal
    def microphone_added(self, stream: Stream):
        """
        Emitted when a microphone is added.

        Args:
            stream: The instance of the stream.
        """

    @IgnisSignal
    def app_added(self, stream: Stream):
        """
        Emitted when an app is added.

        Args:
            stream: The instance of the stream.
        """

    @IgnisSignal
    def recorder_added(self, stream: Stream):
        """
        Emitted when a recorder is added.

        Args:
            stream: The instance of the stream.
        """

    @IgnisProperty
    def control(self) -> Gvc.MixerControl:
        """
        An instance of ``Gvc.MixerControl``.
        """
        return self._control

    @IgnisProperty
    def speaker(self) -> Stream:
        """
        The default speaker.
        """
        return self._speaker

    @speaker.setter
    def speaker(self, value: Stream):
        self._control.set_default_sink(value.stream)

    @IgnisProperty
    def microphone(self) -> Stream:
        """
        The default microphone.
        """
        return self._microphone

    @microphone.setter
    def microphone(self, value: Stream):
        self._control.set_default_source(value.stream)

    @IgnisProperty
    def streams(self) -> list[Stream]:
        """
        A list of all streams.
        """
        return list(self._streams.values())

    @IgnisProperty
    def speakers(self) -> list[Stream]:
        """
        A list of speakers.
        """
        return list(self._speakers.values())

    @IgnisProperty
    def microphones(self) -> list[Stream]:
        """
        A list of microphones.
        """
        return list(self._microphones.values())

    @IgnisProperty
    def apps(self) -> list[Stream]:
        """
        A list of applications currently playing sound.
        """
        return list(self._apps.values())

    @IgnisProperty
    def recorders(self) -> list[Stream]:
        """
        A list of audio recorders.
        """
        return list(self._recorders.values())

    def __add_stream(self, control: Gvc.MixerControl, id: int):
        stream = control.lookup_stream_id(id)
        audio_stream = Stream(stream=stream, control=control)
        stream_type = self.__get_stream_type(stream)
        if stream_type:
            getattr(self, f"_{stream_type}s")[id] = audio_stream
            self._streams[id] = audio_stream
            self.emit(f"{stream_type}-added", audio_stream)
            self.notify(f"{stream_type}s")

    def __remove_stream(self, control: Gvc.MixerControl, id: int):
        audio_stream = self._streams.pop(id)
        stream_type = self.__get_stream_type(audio_stream.stream)
        if stream_type:
            getattr(self, f"_{stream_type}s").pop(id)
            audio_stream._remove()
            self.notify(f"{stream_type}s")

    def __get_stream_type(self, stream: Gvc.MixerStream) -> str | None:
        if isinstance(stream, Gvc.MixerSink):
            return "speaker"
        elif isinstance(stream, Gvc.MixerSource):
            return "microphone"
        elif isinstance(stream, Gvc.MixerSourceOutput):
            return "recorder"
        elif isinstance(stream, Gvc.MixerSinkInput):
            return "app"
        else:
            return None
