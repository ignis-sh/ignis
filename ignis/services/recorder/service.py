import signal
import asyncio
import datetime
import subprocess
import shutil
from ignis.base_service import BaseService
from ignis.gobject import IgnisProperty, IgnisSignal
from ignis.exceptions import (
    GpuScreenRecorderError,
    GpuScreenRecorderNotFoundError,
    RecorderPortalCaptureCanceled,
)
from loguru import logger
from .config import RecorderConfig
from .capture_option import CaptureOption
from .audio_device import AudioDevice
from .app_audio import ApplicationAudio
from typing import TypeVar, Protocol


class _InfoCls(Protocol):
    def __init__(self, arg1: str, arg2: str = ...) -> None: ...


_ParseListCls = TypeVar("_ParseListCls", bound=_InfoCls)


class RecorderService(BaseService):
    """
    A screen recorder. Uses ``gpu-screen-recorder`` as the backend.

    There are options available for this service: :class:`~ignis.options.Options.Recorder`.

    Example usage:

    .. code-block:: python

        import asyncio
        from ignis.services.recorder import RecorderService, RecorderConfig

        recorder = RecorderService.get_default()

        # You can create a configuration from the options
        rec_config = RecorderConfig.new_from_options()

        # You can override them for this config
        rec_config.cursor = False

        # Manual creation of configuration
        rec_config = RecorderConfig(
            source="portal",  # You can also pass a monitor name here
            path="path/to/file",
            # only source and path are required btw
            # arguments below are optional
            video_codec="h264",
            framerate=144,
            cursor=True,
            # "default_input" for microphone
            # "default_output" for internal audio
            # "default_output|default_input" for both
            audio_devices=["default_output"],
            # and a lot more...
        )

        # Start recording
        asyncio.create_task(recorder.start_recording(config=rec_config))

        # Stop recording
        recorder.stop_recording()

        # Pause recording
        recorder.pause_recording()

        # Continue recording
        recorder.continue_recording()

        # You can list available capture options (sources)
        print(recorder.list_capture_options())

        # And audio devices
        print(recorder.list_audio_devices())
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

    @IgnisProperty
    def is_available(self) -> bool:
        """
        Whether gpu-screen-recorder is installed and available.
        """
        return bool(shutil.which("gpu-screen-recorder"))

    def __check_availability(self) -> None:
        if not self.is_available:
            raise GpuScreenRecorderNotFoundError()

    async def start_recording(self, config: RecorderConfig) -> None:
        """
        Start recording.
        This function exits when recording ends.

        Args:
            config: The recorder configuration.

        Raises:
            GpuScreenRecorderError: If an error occurs during recording.
            GpuScreenRecorderNotFoundError: If ``gpu-screen-recorder`` is not found.
            RecorderPortalCaptureCanceled: If the user cancels the desktop portal capture (when :attr:`RecorderConfig.source` is set to ``"portal"``).
        """
        self.__check_availability()

        cmd_args: list[str] = []

        cmd_options: dict[str, str] = {}

        for key, value in {
            "-w": config.source,
            "-s": config.resolution_limit,
            "-region": config.region,
            "-o": datetime.datetime.now().strftime(config.path)
            if config.format_time
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

        for key, value in config.extra_args.items():
            cmd_args.extend([key, value])

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

        if returncode == 60:
            raise RecorderPortalCaptureCanceled()
        else:
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

    def __set_paused(self, value: bool) -> None:
        if not self._process:
            return

        self._is_paused = value
        self._process.send_signal(signal.SIGUSR2)
        self.notify("is-paused")

    def pause_recording(self) -> None:
        """
        Pause recording. This has an effect only if the recording is active and not already paused.
        """
        if not self._is_paused:
            self.__set_paused(True)

    def continue_recording(self) -> None:
        """
        Continue recording. This has an effect only if the recording is active and paused.
        """
        if self._is_paused:
            self.__set_paused(False)

    def __call_cmd(self, cmd: str) -> str:
        self.__check_availability()

        proc = subprocess.run(
            ["gpu-screen-recorder", cmd], text=True, capture_output=True
        )

        if proc.returncode != 0:
            raise GpuScreenRecorderError(returncode=proc.returncode, stderr=proc.stderr)

        return proc.stdout

    async def __call_cmd_async(self, cmd: str) -> str:
        self.__check_availability()

        proc = await asyncio.create_subprocess_exec(
            "gpu-screen-recorder",
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        bstdout, bstderr = await proc.communicate()

        if proc.returncode != 0:
            raise GpuScreenRecorderError(
                returncode=proc.returncode, stderr=bstderr.decode()
            )

        return bstdout.decode()

    def __parse_list(
        self,
        stdout: str,
        klass: type[_ParseListCls],
    ) -> list[_ParseListCls]:
        if stdout == "":
            return []

        result = []

        for string in stdout.strip().split("\n"):
            if "|" not in string:
                result.append(klass(string))

            elif "|" in string:
                arg1, arg2 = string.split("|", 1)

                result.append(klass(arg1, arg2))
            else:
                raise ValueError(f"Invalid string: {string}")

        return result

    def __list_helper(
        self, cmd: str, klass: type[_ParseListCls]
    ) -> list[_ParseListCls]:
        return self.__parse_list(self.__call_cmd(cmd), klass)

    async def __list_helper_async(
        self, cmd: str, klass: type[_ParseListCls]
    ) -> list[_ParseListCls]:
        return self.__parse_list(await self.__call_cmd_async(cmd), klass)

    def list_capture_options(self) -> list[CaptureOption]:
        """
        List available capture options.

        Returns:
            A list of available capture options.

        Raises:
            GpuScreenRecorderError: If ``gpu-screen-recorder`` exits with an error.
            GpuScreenRecorderNotFoundError: If ``gpu-screen-recorder`` is not found.
        """
        return self.__list_helper("--list-capture-options", CaptureOption)

    async def list_capture_options_async(self) -> list[CaptureOption]:
        """
        Asynchronous version of :func:`list_capture_options`.

        Returns:
            A list of available capture options.

        Raises:
            GpuScreenRecorderError: If ``gpu-screen-recorder`` exits with an error.
            GpuScreenRecorderNotFoundError: If ``gpu-screen-recorder`` is not found.
        """
        return await self.__list_helper_async("--list-capture-options", CaptureOption)

    def list_audio_devices(self) -> list[AudioDevice]:
        """
        List audio devices.

        Returns:
            A list of audio devices.

        Raises:
            GpuScreenRecorderError: If ``gpu-screen-recorder`` exits with an error.
            GpuScreenRecorderNotFoundError: If ``gpu-screen-recorder`` is not found.
        """
        return self.__list_helper("--list-audio-devices", AudioDevice)

    async def list_audio_devices_async(self) -> list[AudioDevice]:
        """
        Asynchronous version of :func:`list_audio_devices`.

        Returns:
            A list of audio devices.

        Raises:
            GpuScreenRecorderError: If ``gpu-screen-recorder`` exits with an error.
            GpuScreenRecorderNotFoundError: If ``gpu-screen-recorder`` is not found.
        """
        return await self.__list_helper_async("--list-audio-devices", AudioDevice)

    def list_application_audio(self) -> list[ApplicationAudio]:
        """
        List applications that you can record audio from.

        Returns:
            A list of applications that you can record audio from.

        Raises:
            GpuScreenRecorderError: If ``gpu-screen-recorder`` exits with an error.
            GpuScreenRecorderNotFoundError: If ``gpu-screen-recorder`` is not found.
        """
        return self.__list_helper("--list-application-audio", ApplicationAudio)

    async def list_application_audio_async(self) -> list[ApplicationAudio]:
        """
        Asynchronous version of :func:`list_application_audio`.

        Returns:
            A list of applications that you can record audio from.

        Raises:
            GpuScreenRecorderError: If ``gpu-screen-recorder`` exits with an error.
            GpuScreenRecorderNotFoundError: If ``gpu-screen-recorder`` is not found.
        """
        return await self.__list_helper_async(
            "--list-application-audio", ApplicationAudio
        )
