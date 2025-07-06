import os
import inspect
from gi.repository import Gio, Gdk, Gtk  # type: ignore
from ignis.exceptions import DisplayNotFoundError


def get_current_dir() -> str:
    """
    Returns the directory of the Python file where this function is called.
    """
    frame = inspect.stack()[1]
    caller_file = frame.filename
    return os.path.dirname(os.path.abspath(caller_file))


DBUS_DIR = get_current_dir() + "/../dbus"


def load_interface_xml(
    interface_name: str | None = None, path: str | None = None, xml: str | None = None
) -> Gio.DBusInterfaceInfo:
    """
    Load interface info from XML.
    If you want to load interface info from the path or XML string, you need to provide ``path`` and ``xml`` as keyword arguments respectively.

    Args:
        interface_name: The name of the interface. The interface must be stored in the ``ignis/dbus/`` directory in the Ignis sources.
        path: The full path to the interface XML.
        xml: The XML string.

    Raises:
        TypeError: If neither of the arguments is provided.

    Returns:
        The interface information.
    """
    xml_string: str

    if interface_name:
        file_path = f"{DBUS_DIR}/{interface_name}.xml"
        with open(file_path) as file:
            xml_string = file.read()
    elif path:
        with open(path) as file:
            xml_string = file.read()
    elif xml:
        xml_string = xml
    else:
        raise TypeError(
            "load_interface_xml() requires at least one positional argument"
        )

    return Gio.DBusNodeInfo.new_for_xml(xml_string).interfaces[0]


def get_gdk_display() -> Gdk.Display:
    """
    Get the default :class:`Gdk.Display` or raise :class:`DisplayNotFoundError` if it's ``None``.

    Returns:
        The default :class:`Gdk.Display`.

    Raises:
        DisplayNotFoundError: If :func:`Gdk.Display.get_default` returned ``None``.
    """
    if display := Gdk.Display.get_default():
        return display
    else:
        raise DisplayNotFoundError()


def open_inspector() -> None:
    """
    Open GTK Inspector.
    """
    Gtk.Window.set_interactive_debugging(True)
