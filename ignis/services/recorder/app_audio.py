from dataclasses import dataclass


@dataclass
class ApplicationAudio:
    #: The application which plays audio.
    app: str
