from gi.repository import Gtk, GLib  # type: ignore
from ignis._deprecation import deprecated


class WindowNotFoundError(Exception):
    """
    Raised when a window is not found.

    Args:
        window_name: The name of the window.
    """

    def __init__(self, window_name: str, *args) -> None:
        self._window_name = window_name
        super().__init__(f'No such window: "{window_name}"', *args)

    @property
    def window_name(self) -> str:
        """
        The name of the window.
        """
        return self._window_name


class WindowAddedError(Exception):
    """
    Raised when a window is already added to the application.

    Args:
        window_name: The name of the window.
    """

    def __init__(self, window_name: str, *args) -> None:
        self._window_name = window_name
        super().__init__(f'Window already added: "{window_name}"', *args)

    @property
    def window_name(self) -> str:
        """
        The name of the window.
        """
        return self._window_name


class GvcNotFoundError(Exception):
    """
    Raised when Gvc is not found.
    """

    def __init__(self, *args) -> None:
        super().__init__(
            "Gvc not found! To use the audio service, ensure that Ignis is installed correctly",
            *args,
        )


class HyprlandIPCNotFoundError(Exception):
    """
    Raised when Hyprland IPC is not found.
    """

    def __init__(self, *args: object) -> None:
        super().__init__(
            "Hyprland IPC not found! To use the Hyprland service, ensure that Hyprland is running",
            *args,
        )


class NiriIPCNotFoundError(Exception):
    """
    Raised when Niri IPC is not found.
    """

    def __init__(self, *args: object) -> None:
        super().__init__(
            "Niri IPC not found! To use the Niri service, ensure that Niri is running",
            *args,
        )


class NetworkManagerNotFoundError(Exception):
    """
    Raised when NetworkManager is not found.
    """

    def __init__(self, *args: object) -> None:
        super().__init__(
            "NetworkManager not found! To use the network service, install NetworkManager",
            *args,
        )


@deprecated("GstNotFoundError is deprecated and no longer used.")
class GstNotFoundError(Exception):
    """
    Raised when GStreamer is not found.
    """

    def __init__(self, *args: object) -> None:
        super().__init__(
            "GStreamer not found! To use the recorder service, install GStreamer", *args
        )


@deprecated("GstPluginNotFoundError is deprecated and no longer used.")
class GstPluginNotFoundError(Exception):
    """
    Raised when a GStreamer plugin is not found.

    Args:
        plugin_name: The name of the plugin.
        plugin_package: The package name of the plugin.
    """

    def __init__(self, plugin_name: str, plugin_package: str, *args) -> None:
        self._plugin_name = plugin_name
        self._plugin_package = plugin_package
        super().__init__(
            f"{plugin_name} GStreamer plugin not found! To use the recorder service, install {plugin_package}",
            *args,
        )

    @property
    def plugin_name(self) -> str:
        """
        The name of the plugin.
        """
        return self._plugin_name

    @property
    def plugin_package(self) -> str:
        """
        The package name of the plugin.
        """
        return self._plugin_package


class SassCompilationError(Exception):
    """
    Raised when the Sass compilation fails.

    Args:
        stderr: The stderr output from the Sass compiler.
    """

    def __init__(self, stderr: str, *args: object) -> None:
        self._stderr = stderr
        super().__init__(f"SASS compilation error:\n{stderr}", *args)

    @property
    def stderr(self) -> str:
        """
        The stderr output from the Sass compiler.
        """
        return self._stderr


class SassNotFoundError(Exception):
    """
    Raised when a compatible Sass compiler is not found.
    """

    def __init__(self, *args: object) -> None:
        super().__init__(
            "Sass compiler not found! To compile SCSS/SASS, install either dart-sass or grass-sass",
            *args,
        )


class MonitorNotFoundError(Exception):
    """
    Raised when a monitor with the given ID is not found.

    Args:
        monitor_id: The ID of the monitor.
    """

    def __init__(self, monitor_id: int, *args: object) -> None:
        self._monitor_id = monitor_id
        super().__init__(f"No such monitor with id: {monitor_id}", *args)

    @property
    def monitor_id(self) -> int:
        """
        The ID of the monitor.
        """
        return self._monitor_id


class LayerShellNotSupportedError(Exception):
    """
    Raised when the Layer Shell protocol is not supported.
    """

    def __init__(self, *args: object) -> None:
        super().__init__(
            "zwlr_layer_shell_v1 is not supported! Ensure you are running a Wayland compositor that implements the zwlr_layer_shell_v1 protocol",
            *args,
        )


class IgnisNotRunningError(Exception):
    """
    Raised when Ignis is not running.
    """

    def __init__(self, *args: object) -> None:
        super().__init__("Ignis is not running", *args)


class IgnisAlreadyRunningError(Exception):
    """
    Raised when an Ignis instance with the given ID is already running.
    """

    def __init__(self, instance_id: str, *args: object) -> None:
        super().__init__(
            f"An Ignis instance with the given ID is already running: {instance_id}",
            *args,
        )


class DBusMethodNotFoundError(Exception):
    """
    Raised when a D-Bus method is not found or not registered.

    Args:
        method_name: The name of the D-Bus method.
    """

    def __init__(self, method_name: str, *args: object) -> None:
        self._method_name = method_name
        super().__init__(
            f'No such registered D-Bus method with name: "{method_name}"', *args
        )

    @property
    def method_name(self) -> str:
        """
        The name of the D-Bus method.
        """
        return self._method_name


class DBusPropertyNotFoundError(Exception):
    """
    Raised when a D-Bus property is not found or not registered.

    Args:
        property_name: The name of the D-Bus property.
    """

    def __init__(self, property_name: str, *args: object) -> None:
        self._property_name = property_name
        super().__init__(
            f'No such registered D-Bus property with name: "{property_name}"', *args
        )

    @property
    def property_name(self) -> str:
        """
        The name of the D-Bus property.
        """
        return self._property_name


class DisplayNotFoundError(Exception):
    """
    Raised when the display is not found (e.g., a Wayland compositor is not running).
    """

    def __init__(self, *args: object) -> None:
        super().__init__(
            "Display not found! Ensure you are running a Wayland compositor", *args
        )


@deprecated(
    "StylePathNotFoundError is deprecated, use the new CssManager API and CssInfoNotFoundError."
)
class StylePathNotFoundError(Exception):
    """
    Raised when the style path is not found / not applied to the application.

    Args:
        style_path: Path to the .css/.scss/.sass file.

    .. deprecated:: 0.6
        Use the new :class:`~ignis.css_manager.CssManager` API and :class:`CssInfoNotFoundError`.
    """

    def __init__(self, style_path: str, *args: object) -> None:
        self._style_path = style_path
        super().__init__(f'Style path is not found: "{style_path}"', *args)

    @property
    def style_path(self) -> str:
        """
        Path to the .css/.scss/.sass file.
        """
        return self._style_path


@deprecated(
    "StylePathAppliedError is deprecated, use the new CssManager API and CssInfoAlreadyAppliedError."
)
class StylePathAppliedError(Exception):
    """
    Raised when the style path is already applied to the application.

    Args:
        style_path: Path to the .css/.scss/.sass file.

    .. deprecated:: 0.6
        Use the new :class:`~ignis.css_manager.CssManager` API and :class:`CssInfoAlreadyAppliedError`.
    """

    def __init__(self, style_path: str, *args: object) -> None:
        self._style_path = style_path
        super().__init__(f'Style path is already added: "{style_path}"', *args)

    @property
    def style_path(self) -> str:
        """
        Path to the .css/.scss/.sass file.
        """
        return self._style_path


class Gtk4LayerShellNotFoundError(Exception):
    """
    Raised when GTK4 Layer Shell is not found.
    """

    def __init__(self, *args: object) -> None:
        super().__init__(
            "GTK4 Layer Shell is not found! To use Ignis, first install it", *args
        )


class CssParsingError(Exception):
    """
    Raised when a CSS parsing error occurs.

    Args:
        section: The section the error happened in.
        gerror: The parsing error.
    """

    def __init__(
        self, section: Gtk.CssSection, gerror: GLib.Error, *args: object
    ) -> None:
        self._section = section
        self._gerror = gerror
        super().__init__(f"{section.to_string()}: {gerror.message}", *args)

    @property
    def section(self) -> Gtk.CssSection:
        """
        The section the error happened in.
        """
        return self._section

    @property
    def gerror(self) -> GLib.Error:
        """
        The parsing error.
        """
        return self._gerror


class AnotherNotificationDaemonRunningError(Exception):
    """
    Raised when another notification daemon is running.

    Args:
        name: The name of the currenly running notification daemon.
    """

    def __init__(self, name: str, *args: object) -> None:
        self._name = name
        super().__init__(
            f"Another notification daemon is already running: {name}", *args
        )

    @property
    def name(self) -> str:
        """
        The name of the currenly running notification daemon.
        """
        return self._name


class AnotherSystemTrayRunningError(Exception):
    """
    Raised when another system tray is running.

    Args:
        name: The name of the currenly running notification daemon.
    """

    def __init__(self, name: str, *args: object) -> None:
        self._name = name
        super().__init__(f"Another system tray is already running: {name}", *args)

    @property
    def name(self) -> str:
        """
        The name of the currenly running system tray.
        """
        return self._name


class UPowerNotRunningError(Exception):
    """
    Raised when UPower is not running.
    """

    def __init__(self, *args: object) -> None:
        super().__init__(
            "UPower is not running! To use the UPower Service, install UPower and run it",
            *args,
        )


class GnomeBluetoothNotFoundError(Exception):
    """
    Raised when GnomeBluetooth-3.0 is not found.
    """

    def __init__(self, *args: object) -> None:
        super().__init__(
            "GnomeBluetooth-3.0 is not found! To use the Bluetooth Service, install GnomeBluetooth-3.0",
            *args,
        )


class GpuScreenRecorderError(Exception):
    """
    Raised when ``gpu-screen-recorder`` exits with an error.
    """

    def __init__(self, returncode: int | None, stderr: str, *args):
        self._returncode = returncode
        self._stderr = stderr

        super().__init__(
            f"gpu-screen-recorder exited with returncode {returncode}:\n{stderr}", *args
        )

    @property
    def returncode(self) -> int | None:
        """
        The returncode.
        """
        return self._returncode

    @property
    def stderr(self) -> str:
        """
        The stderr.
        """
        return self._stderr


class GpuScreenRecorderNotFoundError(Exception):
    """
    Raised when ``gpu-screen-recorder`` is not found.
    """

    def __init__(self, *args):
        super().__init__(
            "gpu-screen-recorder is not found! To use the Recorder Service, install gpu-screen-recorder",
            *args,
        )


class RecorderPortalCaptureCanceled(Exception):
    """
    Raised when the desktop portal capture is canceled by the user (e.g., by closing the “Select Sources” window).
    """

    def __init__(self, *args):
        super().__init__("The desktop portal capture was canceled by the user", *args)


class CssInfoNotFoundError(Exception):
    """
    Raised when a CSS info with the given name is not found.
    """

    def __init__(self, name: str, *args: object) -> None:
        self._name = name
        super().__init__(f'CSS info with the given name is not found: "{name}"', *args)

    @property
    def name(self) -> str:
        """
        The name of the CSS info.
        """
        return self._name


class CssInfoAlreadyAppliedError(Exception):
    """
    Raised when a CSS info with the given name is already applied.
    """

    def __init__(self, name: str, *args: object) -> None:
        self._name = name
        super().__init__(
            f'CSS info with the given name is already applied: "{name}"', *args
        )

    @property
    def name(self) -> str:
        """
        The name of the CSS info.
        """
        return self._name


class AppNotInitializedError(Exception):
    """
    Raised when the application is not initialized.
    """

    def __init__(self, *args: object) -> None:
        super().__init__(
            "Called IgnisApp.get_initialized(), but IgnisApp is not initialized!", *args
        )
