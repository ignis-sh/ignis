import os
import sys
from loguru import logger
from ignis import utils
from ignis.gobject import IgnisGObjectSingleton, IgnisProperty, IgnisSignal
from typing import TYPE_CHECKING
from ignis._deprecation import ignore_deprecation_warnings

if TYPE_CHECKING:
    from ignis.app import IgnisApp


class ConfigManager(IgnisGObjectSingleton):
    """
    A simple class to manage your configuration.
    """

    def __init__(self):
        super().__init__()

        self._autoreload_config: bool = True
        self._config_parsed: bool = False

    @IgnisSignal
    def config_parsed(self):
        """
        Emitted when the configuration has been parsed.
        """

    @IgnisProperty
    def is_config_parsed(self) -> bool:
        """
        Whether the configuration is parsed.
        """
        return self._config_parsed

    @IgnisProperty
    def autoreload_config(self) -> bool:
        """
        Whether to automatically reload the configuration when it changes (only .py files).

        Default: ``True``.
        """
        return self._autoreload_config

    @autoreload_config.setter
    def autoreload_config(self, value: bool) -> None:
        self._autoreload_config = value

    def __watch_config(self, path: str, event_type: str, app: "IgnisApp") -> None:
        if event_type != "changes_done_hint":
            return

        if not os.path.isdir(path) and "__pycache__" not in path:
            extension = os.path.splitext(path)[1]
            if extension == ".py" and self.autoreload_config:
                app.reload()

    def _load_config(self, app: "IgnisApp", path: str) -> None:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Provided config path doesn't exists: {path}")

        config_dir = os.path.dirname(path)
        config_filename = os.path.splitext(os.path.basename(path))[0]

        logger.info(f"Using configuration file: {path}")

        self._monitor = utils.FileMonitor(
            path=config_dir,
            callback=lambda _, path, event: self.__watch_config(path, event, app),
            recursive=True,
        )

        sys.path.append(config_dir)
        __import__(config_filename)

        self._config_parsed = True
        self.emit("config-parsed")
        logger.info("Configuration parsed.")

        # FIXME: deprecated
        app.emit("ready")
