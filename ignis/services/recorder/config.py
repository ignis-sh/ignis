from dataclasses import dataclass
from .._shared import recorder_arg_types
from ignis.options import options

recorder = options.recorder


# FIXME: looks awfully
# Maybe there is some more elegant way to implement this?
@dataclass
class RecorderConfigDefaults:
    source: recorder_arg_types.Source = recorder.default_source
    path: recorder_arg_types.Path = recorder.default_path
    resolution_limit: recorder_arg_types.ResolutionLimit = (
        recorder.default_resolution_limit
    )
    region: recorder_arg_types.Region = recorder.default_region
    framerate: recorder_arg_types.Framerate = recorder.default_framerate
    audio_devices: recorder_arg_types.AudioDevices = recorder.default_audio_devices
    quality: recorder_arg_types.Quality = recorder.default_quality
    video_codec: recorder_arg_types.VideoCodec = recorder.default_video_codec
    audio_codec: recorder_arg_types.AudioCodec = recorder.default_audio_codec
    audio_bitrate: recorder_arg_types.AudioBitrate = recorder.default_audio_bitrate
    framerate_mode: recorder_arg_types.FramerateMode = recorder.default_framerate_mode
    bitrate_mode: recorder_arg_types.BitrateMode = recorder.default_bitrate_mode
    color_range: recorder_arg_types.ColorRange = recorder.default_color_range
    cursor: recorder_arg_types.Cursor = recorder.default_cursor
    encoder: recorder_arg_types.Encoder = recorder.default_encoder


@dataclass
class RecorderConfigManual:
    # source and path are required
    source: recorder_arg_types.Source
    path: recorder_arg_types.Path

    resolution_limit: recorder_arg_types.ResolutionLimit = None
    region: recorder_arg_types.Region = None
    framerate: recorder_arg_types.Framerate = None
    audio_devices: recorder_arg_types.AudioDevices = None
    quality: recorder_arg_types.Quality = None
    video_codec: recorder_arg_types.VideoCodec = None
    audio_codec: recorder_arg_types.AudioCodec = None
    audio_bitrate: recorder_arg_types.AudioBitrate = None
    framerate_mode: recorder_arg_types.FramerateMode = None
    bitrate_mode: recorder_arg_types.BitrateMode = None
    color_range: recorder_arg_types.ColorRange = None
    cursor: recorder_arg_types.Cursor = None
    encoder: recorder_arg_types.Encoder = None
