import os
from gi.repository import Gtk, Gio  # type: ignore
from ignis import utils


def get_paintable(
    widget: Gtk.Widget, icon_name: str, size: int
) -> "Gtk.IconPaintable | None":
    """
    Get a ``Gdk.Paintable`` by icon name.

    Args:
        widget: The parent widget.
        icon_name: The name of the icon to look up.
        size: The size of the icon.

    Returns:
        The paintable object for the icon or ``None`` if no such icon exists.
    """

    icon = Gio.ThemedIcon.new(icon_name)
    icon_theme = Gtk.IconTheme.get_for_display(utils.get_gdk_display())
    return icon_theme.lookup_by_gicon(
        icon,
        size,
        widget.get_scale_factor(),
        widget.get_direction(),
        Gtk.IconLookupFlags.PRELOAD,
    )


def get_file_icon_name(path: str, symbolic: bool = False) -> str | None:
    """
    Get a standart icon name for the file or directory.

    Args:
        path: The path to the file or directory.
        symbolic: Whether the icon should be symbolic.

    Returns:
        The name of the icon. ``None`` if the icon with the given name is not found.
    """
    file = Gio.File.new_for_path(path)
    if not os.path.exists(path):
        raise FileNotFoundError(f"No such file or directory: {path}")
    info = file.query_info("standard::icon", Gio.FileQueryInfoFlags.NONE)
    icon_obj: Gio.ThemedIcon = info.get_icon()  # type: ignore
    icon_names = icon_obj.get_names()

    if symbolic:
        for icon in icon_names:
            if icon.endswith("-symbolic"):
                return icon

    if len(icon_names) > 0:
        return icon_names[0]

    return None


def get_app_icon_name(app_id: str) -> str | None:
    """
    Get the application icon name by the application ID.

    Args:
        app_id: The application ID, without ``.desktop`` extension.

    Returns:
        The application icon name, or ``None`` if the application with the given ID doesn't exist or has no icon.
    """
    try:
        app_info = Gio.DesktopAppInfo.new(app_id + ".desktop")
    except TypeError:
        return None

    if not app_info:
        return None

    return app_info.get_string("Icon")
