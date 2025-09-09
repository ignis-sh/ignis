from dataclasses import dataclass


@dataclass
class AudioDevice:
    #: The name of the device (e.g., ``alsa_input.pci-0000_00_1f.3.analog-stereo``).
    #: Can be passed to :attr:`.RecorderConfig.audio_devices`.
    device_name: str

    #: The name of the device in a human-readable format (e.g., ``Built-in Audio Analog Stereo``).
    human_readable_name: str
