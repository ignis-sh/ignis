import os
from ignis import DATA_DIR, CACHE_DIR, is_sphinx_build
from gi.repository import GLib  # type: ignore
from ignis.options_manager import OptionsManager, OptionsGroup, TrackedList
from loguru import logger
from ignis.services._shared import recorder_arg_types


OPTIONS_FILE = f"{DATA_DIR}/options.json"
OLD_OPTIONS_FILE = f"{CACHE_DIR}/ignis_options.json"


def get_recorder_default_file_location() -> str | None:
    if not is_sphinx_build:
        return GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_VIDEOS)
    else:
        return "XDG Videos directory"


# FIXME: remove after v0.6 release
def _migrate_old_options_file() -> None:
    logger.warning(
        f"Migrating options to the new file: {OLD_OPTIONS_FILE} -> {OPTIONS_FILE}"
    )

    with open(OLD_OPTIONS_FILE) as f:
        data = f.read()

    with open(OPTIONS_FILE, "w") as f:
        f.write(data)

    logger.success(
        f"Done. Consider using new options file instead: $XDG_DATA_HOME/ignis/options.json ({OPTIONS_FILE}). The old one is deprecated. See the Breaking Changes Tracker for more info."
    )


class Options(OptionsManager):
    """
    Options for Ignis.

    .. warning::

        Use already initialized instance of this class:

        .. code-block:: python

            from ignis.options import options

            print(options.notifications.dnd)

    Below are classes with options, their names begin with a capital letter.
    However, if you want to get the current value of an option or set a value,
    use an initialized instance that starts with a lowercase letter.

    For example:
        * ``Notifications`` -> ``notifications``
        * ``Recorder`` -> ``recorder``
        * and etc.

    You can use classes (not instances of them) to obtain default values of options.

    .. hint::
        If the option is of type :class:`~ignis.options_manager.TrackedList`, it means that it is regular Python list.
        But you can call ``.append()``, ``.remove()``, ``.insert()``, etc., and the changes will be applied!

    The options file is located at :obj:`ignis.DATA_DIR`/options.json (``$XDG_DATA_HOME/ignis/options.json``).

    Example usage:

    .. code-block::

        from ignis.options import options

        # Get an option value
        print(options.notifications.dnd)

        # Set a new value for an option
        options.notifications.dnd = True

        # Connect to an option change event
        options.notifications.connect_option("dnd", lambda: print("option dnd changed! new value:", options.notifications.dnd))

        # You can also bind to an option!
        options.notifications.bind("dnd")

        # Obtain the default value of an option
        print(options.Notifications.popup_timeout)
    """

    def __init__(self):
        if not os.path.exists(OPTIONS_FILE) and os.path.exists(OLD_OPTIONS_FILE):
            _migrate_old_options_file()

        try:
            super().__init__(file=OPTIONS_FILE)
        except FileNotFoundError:
            pass

    class Notifications(OptionsGroup):
        """
        Options for the :class:`~ignis.services.notifications.NotificationService`.
        """

        #: Do Not Disturb mode.
        #:
        #: If set to ``True``, the ``new_popup`` signal will not be emitted,
        #: and all new :class:`~ignis.services.notifications.Notification` instances will have ``popup`` set to ``False``.
        dnd: bool = False

        #: The timeout before a popup is automatically dismissed, in milliseconds.
        popup_timeout: int = 5000

        #: The maximum number of popups.
        #:
        #: If the length of the ``popups`` list exceeds ``max_popups_count``, the oldest popup will be dismissed.
        max_popups_count: int = 3

    class Recorder(OptionsGroup):
        """
        Options for the :class:`~ignis.services.recorder.RecorderService`.
        """

        #: The default location for saving recordings. Defaults to XDG Video directory.
        default_file_location: str | None = get_recorder_default_file_location()

        #: The default filename for recordings. Supports time formating.
        default_filename: str = "%Y-%m-%d_%H-%M-%S.mp4"

        default_source: recorder_arg_types.Source = "portal"

        default_path: recorder_arg_types.Path = os.path.join(
            default_file_location,  # type: ignore
            default_filename,
        )

        default_resolution_limit: recorder_arg_types.ResolutionLimit = None

        default_region: recorder_arg_types.Region = None

        default_framerate: recorder_arg_types.Framerate = None

        default_audio_devices: recorder_arg_types.AudioDevices = None

        default_quality: recorder_arg_types.Quality = None

        default_video_codec: recorder_arg_types.VideoCodec = None

        default_audio_codec: recorder_arg_types.AudioCodec = None

        default_audio_bitrate: recorder_arg_types.AudioBitrate = None

        default_framerate_mode: recorder_arg_types.FramerateMode = None

        default_bitrate_mode: recorder_arg_types.BitrateMode = None

        default_color_range: recorder_arg_types.ColorRange = None

        default_cursor: recorder_arg_types.Cursor = None

        default_encoder: recorder_arg_types.Encoder = None

    class Applications(OptionsGroup):
        """
        Options for the :class:`~ignis.services.applications.ApplicationsService`.
        """

        #: A list of the pinned applications desktop files, e.g. ``"firefox.desktop"``, ``"code.desktop"``.
        pinned_apps: TrackedList[str] = TrackedList()

    class Wallpaper(OptionsGroup):
        """
        Options for the :class:`~ignis.services.wallpaper.WallpaperService`.
        """

        #: The path to the wallpaper image.
        wallpaper_path: str | None = None

    notifications = Notifications()
    recorder = Recorder()
    applications = Applications()
    wallpaper = Wallpaper()


options = Options()
