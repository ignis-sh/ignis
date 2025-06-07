import signal
import asyncio
import datetime
import subprocess
from ignis.app import IgnisApp
from ignis.base_service import BaseService
from ignis.gobject import IgnisProperty, IgnisSignal
from ignis.exceptions import GpuScreenRecorderError
from loguru import logger
from .config import RecorderConfigDefaults, RecorderConfigManual

app = IgnisApp.get_default()


class RecorderService(BaseService):
    """
    A screen recorder.
    Uses XDG Desktop portal and PipeWire.
    Allow record screen with microphone audio and internal system audio.

    There are options available for this service: :class:`~ignis.options.Options.Recorder`.

    Dependencies:
        - GStreamer
        - PipeWire
        - gst-plugin-pipewire
        - gst-plugins-good
        - gst-plugins-ugly
        - pipewire-pulse: for audio recording.

    Raises:
        GstNotFoundError: If GStreamer is not found.
        GstPluginNotFoundError: If GStreamer plugin is not found.

    Example usage:

    .. code-block:: python

        from ignis.services.recorder import RecorderService
        from ignis import utils

        recorder = RecorderService.get_default()

        recorder.start_recording(record_internal_audio=True)

        # record for 30 seconds and then stop
        utils.Timeout(ms=30 * 1000, target=recorder.stop_recording)
    """

    def __init__(self):
        super().__init__()

        self._active: bool = False
        self._is_paused: bool = False

        self._process: asyncio.subprocess.Process | None = None

    @IgnisSignal
    def recording_started(self):
        """
        Emitted when recording starts.
        """

    @IgnisSignal
    def recording_stopped(self):
        """
        Emitted when recording stops.
        """

    @IgnisProperty
    def active(self) -> bool:
        """
        Whether recording is currently active.
        """
        return self._active

    @IgnisProperty
    def is_paused(self) -> bool:
        """
        Whether recording is currently paused.
        """
        return self._is_paused

    async def start_recording(
        self,
        config: RecorderConfigDefaults | RecorderConfigManual,
        format_time: bool = True,
        *extra_args,
    ) -> None:
        """
        Start recording.
        """

        cmd_args: list[str] = []

        cmd_options: dict[str, str] = {}

        for key, value in {
            "-w": config.source,
            "-s": config.resolution_limit,
            "-region": config.region,
            "-o": datetime.datetime.now().strftime(config.path)
            if format_time
            else config.path,
            "-f": str(config.framerate) if config.framerate else None,
            "-q": config.quality,
            "-ac": config.audio_codec,
            "-ab": str(config.audio_bitrate) if config.audio_bitrate else None,
            "-bm": config.bitrate_mode,
            "-cr": config.color_range,
            "-k": config.video_codec,
            "-fm": config.framerate_mode,
            "-cursor": config.cursor,
            "-encoder": config.encoder,
        }.items():
            if value is not None:
                cmd_options[key] = value

        if config.audio_devices:
            for device in config.audio_devices:
                cmd_args.extend(["-a", device])

        for key, value in cmd_options.items():
            cmd_args.extend([key, value])

        cmd_args.extend(extra_args)

        logger.debug(f"Running gpu-screen-recorder with args:\n{cmd_args}")

        self._process = await asyncio.create_subprocess_exec(
            "gpu-screen-recorder",
            *cmd_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        self._active = True
        self._is_paused = False

        self.notify("active")
        self.notify("is-paused")
        self.emit("recording-started")

        bstdout, bstderr = await self._process.communicate()

        stdout = bstdout.decode().strip()
        stderr = bstderr.decode().strip()

        logger.debug(
            f"gpu-screen-recorder exited with returncode: {self._process.returncode}\nstdout:\n{stdout}\nstderr:\n{stderr}"
        )

        if self._process.returncode != 0:
            self.__recording_error(self._process.returncode, stderr)

    def __recording_error(self, returncode: int | None, stderr: str) -> None:
        self._active = False
        self._is_paused = False
        self.notify("active")
        self.notify("is-paused")

        raise GpuScreenRecorderError(returncode=returncode, stderr=stderr)

    def stop_recording(self) -> None:
        """
        Stop recording.
        """
        if not self._process:
            return

        self._process.send_signal(signal.SIGINT)

        self._active = False
        self._is_paused = False

        self.notify("active")
        self.notify("is-paused")
        self.emit("recording_stopped")

    def pause_recording(self) -> None:
        """
        Pause recording. This has an effect only if the recording is active and not already paused.
        """
        if not self._process:
            return

        self._is_paused = True
        self._process.send_signal(signal.SIGUSR2)
        self.notify("is-paused")

    def continue_recording(self) -> None:
        """
        Continue recording. This has an effect only if the recording is active and paused.
        """
        if not self._process:
            return

        self._is_paused = False
        self._process.send_signal(signal.SIGUSR2)
        self.notify("is-paused")
