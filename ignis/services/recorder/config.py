from dataclasses import dataclass, field, fields
from . import arg_types


@dataclass
class RecorderConfig:
    """
    This documentation describes the arguments only briefly.
    All of them correspond to the arguments of ``gpu-screen-recorder``.

    Run ``gpu-screen-recorder --help`` to get more detailed information about each argument.

    Most of the arguments default to ``None``, which means their value will be automatically determined by ``gpu-screen-recorder``.
    """

    #: [``-w``] Window id to record, a display (monitor name), "screen", "screen-direct", "focused", "portal" or "region".
    source: arg_types.Source

    #: [``-o``] The output file path.
    path: arg_types.Path

    #: [``-s``] The output resolution limit of the video in the format WxH, for example 1920x1080.
    resolution_limit: arg_types.ResolutionLimit = None

    #: [``-region``] The region to capture, only to be used with -w region. This is in format ``WxH+X+Y``.
    region: arg_types.Region = None

    #: [``-f``] Frame rate to record at.
    framerate: arg_types.Framerate = None

    #: [``-a``] Audio device or application to record from (pulse audio device).
    audio_devices: arg_types.AudioDevices = None

    #: [``-q``] Video quality.
    quality: arg_types.Quality = None

    #: [``-k``] Video codec to use.
    video_codec: arg_types.VideoCodec = None

    #: [``-ac``] Audio codec to use.
    audio_codec: arg_types.AudioCodec = None

    #: [``-ab``] Audio bitrate in kbps.
    audio_bitrate: arg_types.AudioBitrate = None

    #: [``-fm``] Framerate mode.
    framerate_mode: arg_types.FramerateMode = None

    #: [``-bm``] Bitrate mode.
    bitrate_mode: arg_types.BitrateMode = None

    #: [``-cr``] Color range.
    color_range: arg_types.ColorRange = None

    #: [``-cursor``] Record cursor.
    cursor: arg_types.Cursor = None

    #: [``-encoder``] Which device should be used for video encoding.
    encoder: arg_types.Encoder = None

    #: Whether to format the time in :attr:`path`.
    format_time: arg_types.FormatTime = True

    #: Extra arguments to pass to ``gpu-screen-recorder``.
    extra_args: arg_types.ExtraArgs = field(default_factory=dict)

    @classmethod
    def new_from_options(cls: type["RecorderConfig"]) -> "RecorderConfig":
        """
        Create a :class:`RecorderConfig` based on options (:class:`~ignis.options.Options.Recorder`).

        Returns:
            An instance of :class:`RecorderConfig` with data from options.

        .. hint::

            You can override an attribute value without changing the options:

            .. code-block:: python

                rec_config = RecorderConfig.new_from_options()

                rec_config.cursor = "no"
                rec_config.source = "screen"
                # ... etc
        """
        from ignis.options import options

        init_kwargs = {}

        for f in fields(cls):
            init_kwargs[f.name] = getattr(options.recorder, f"default_{f.name}")

        return cls(**init_kwargs)
