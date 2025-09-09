import os
import shutil
from ignis import utils
from ignis.base_service import BaseService
from ignis.options import options
from .window import WallpaperLayerWindow
from .constants import CACHE_WALLPAPER_PATH


class WallpaperService(BaseService):
    """
    A simple service to set the wallpaper.
    Supports multiple monitors.

    There are options available for this service: :class:`~ignis.options.Options.Wallpaper`.

    Example usage:

    .. code-block:: python

        .. code-block:: python

        from ignis.services.wallpaper import WallpaperService
        from ignis.options import options

        WallpaperService.get_default()  # just to initialize it

        options.wallpaper.set_wallpaper_path("path/to/image")
    """

    def __init__(self):
        super().__init__()
        self._windows: list[WallpaperLayerWindow] = []
        options.wallpaper.connect_option(
            "wallpaper_path", lambda: self.__update_wallpaper()
        )
        self.__sync()

    def __update_wallpaper(self) -> None:
        try:
            if options.wallpaper.wallpaper_path is not None:
                shutil.copyfile(options.wallpaper.wallpaper_path, CACHE_WALLPAPER_PATH)
        except shutil.SameFileError:
            return

        self.__sync()

    def __sync(self) -> None:
        for i in self._windows:
            i.unrealize()

        if not os.path.isfile(CACHE_WALLPAPER_PATH):
            return

        self._windows = []

        for monitor_id in range(utils.get_n_monitors()):
            gdkmonitor = utils.get_monitor(monitor_id)
            if not gdkmonitor:
                return

            geometry = gdkmonitor.get_geometry()
            window = WallpaperLayerWindow(
                wallpaper_path=CACHE_WALLPAPER_PATH,
                gdkmonitor=gdkmonitor,
                width=geometry.width,
                height=geometry.height,
            )
            self._windows.append(window)
