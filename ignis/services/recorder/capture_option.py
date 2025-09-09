from dataclasses import dataclass
from . import arg_types


@dataclass
class CaptureOption:
    #: The name of the option.
    #: Can be passed to :attr:`.RecorderConfig.source`.
    option: arg_types.Source

    #: The resolution of the monitor. ``None`` if :attr:`option` is not a monitor name.
    monitor_resolution: str | None = None
