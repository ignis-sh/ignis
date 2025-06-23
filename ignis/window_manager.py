from gi.repository import Gtk  # type: ignore
from ignis.gobject import IgnisGObjectSingleton, IgnisProperty
from ignis.exceptions import WindowAddedError, WindowNotFoundError


class WindowManager(IgnisGObjectSingleton):
    """
    A class for managing window objects.

    Example usage:

    .. code-block:: python

        from ignis.window_manager import WindowManager

        window_manager = WindowManager.get_default()

        # Open, close, or toggle a window
        window_manager.open_window("window-name")
        window_manager.close_window("window-name")
        window_manager.toggle_window("window-name")

        # Get an instance of a window
        some_window = window_manager.get_window("window-name")
    """

    def __init__(self):
        self._windows: dict[str, Gtk.Window] = {}
        super().__init__()

    @IgnisProperty
    def windows(self) -> list[Gtk.Window]:
        """
        A list of added windows.
        """
        return list(self._windows.values())

    def get_window(self, window_name: str) -> Gtk.Window:
        """
        Get a window by name.

        Args:
            window_name: The window's namespace.

        Returns:
            The window object.

        Raises:
            WindowNotFoundError: If a window with the given namespace does not exist.
        """
        window = self._windows.get(window_name, None)
        if window:
            return window
        else:
            raise WindowNotFoundError(window_name)

    def add_window(self, window_name: str, window: Gtk.Window) -> None:
        """
        Add a window.
        You typically shouldn't use this method, as windows are added automatically.

        Args:
            window_name: The window's namespace.
            window: The window instance.

        Raises:
            WindowAddedError: If a window with the given namespace already exists.
        """
        if window_name in self._windows:
            raise WindowAddedError(window_name)

        self._windows[window_name] = window

    def remove_window(self, window_name: str) -> None:
        """
        Remove a window by its name.
        This will **not** destroy the window.

        Args:
            window_name: The window's namespace.

        Raises:
            WindowNotFoundError: If a window with the given namespace does not exist.
        """
        window = self._windows.pop(window_name, None)
        if not window:
            raise WindowNotFoundError(window_name)

    def open_window(self, window_name: str) -> None:
        """
        Open (show) a window by its name.

        Args:
            window_name: The window's namespace.

        Raises:
            WindowNotFoundError: If a window with the given namespace does not exist.
        """
        window = self.get_window(window_name)
        window.set_visible(True)

    def close_window(self, window_name: str) -> None:
        """
        Close (hide) a window by its name.

        Args:
            window_name: The window's namespace.

        Raises:
            WindowNotFoundError: If a window with the given namespace does not exist.
        """
        window = self.get_window(window_name)
        window.set_visible(False)

    def toggle_window(self, window_name: str) -> None:
        """
        Toggle (change visibility to opposite state) a window by its name.

        Args:
            window_name: The window's namespace.

        Raises:
            WindowNotFoundError: If a window with the given namespace does not exist.
        """
        window = self.get_window(window_name)
        window.set_visible(not window.get_visible())

    def list_window_names(self) -> tuple[str, ...]:
        """
        List the names of windows.

        Returns:
            A tuple containing window names.
        """
        return tuple(self._windows.keys())
