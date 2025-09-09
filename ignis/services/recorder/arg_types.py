from typing import Literal

Source = Literal["screen", "screen-direct", "focused", "portal", "region"] | str
Path = str
ResolutionLimit = str | None
Region = str | None
Framerate = int | None
AudioDevices = list[str] | None
Quality = Literal["medium", "high", "very_high", "ultra"] | None
VideoCodec = (
    Literal[
        "auto",
        "h264",
        "hevc",
        "av1",
        "vp8",
        "vp9",
        "hevc_hdr",
        "av1_hdr",
        "hevc_10bit",
        "av1_10bit",
    ]
    | None
)
AudioCodec = Literal["aac", "opus", "flac"] | None
AudioBitrate = int | None
FramerateMode = Literal["cfr", "vfr", "content"] | None
BitrateMode = Literal["auto", "qp", "vbr", "cbr"] | None
ColorRange = Literal["limited", "full"] | None
Cursor = Literal["yes", "no"] | None
Encoder = Literal["gpu", "cpu"] | None
FormatTime = bool
ExtraArgs = dict[str, str]
