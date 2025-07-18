from ignis.dbus import DBusProxy
from ignis import utils
from ignis.exceptions import WindowNotFoundError, IgnisNotRunningError
from typing import Any


class IgnisClient:
    """
    Class for interacting with Ignis D-Bus interface.
    Provides the same functionality as the CLI.

    Useful for scripts that run outside the Ignis process.

    All methods will raise :class:`~ignis.exceptions.IgnisNotRunningError` if Ignis is not running.

    .. warning::
        Do not use this class inside the main Ignis process (e.g., in the config file).
        It's unnecessary; use :class:`~ignis.app.IgnisApp` instead.

    Example usage:

    .. code-block:: python

        from ignis.client import IgnisClient

        client = IgnisClient()
        print(client.list_windows())

        client.reload()
    """

    def __init__(self, instance_id: str = "com.github.linkfrg.ignis"):
        self.__dbus = DBusProxy.new(
            name=instance_id,
            object_path="/com/github/linkfrg/ignis",
            interface_name="com.github.linkfrg.ignis",
            info=utils.load_interface_xml("com.github.linkfrg.ignis"),
        )

    @property
    def has_owner(self) -> bool:
        """
        Whether D-Bus name has the owner (Whether Ignis is running).
        """
        return self.__dbus.has_owner

    def __call_dbus_method(self, method_name: str, *args) -> Any:
        if not self.has_owner:
            raise IgnisNotRunningError

        return getattr(self.__dbus, method_name)(*args)

    def __call_window_method(self, method_name: str, window_name: str) -> None:
        window_found = self.__call_dbus_method(method_name, "(s)", window_name)
        if not window_found:
            raise WindowNotFoundError(window_name)

    def open_window(self, window_name: str) -> None:
        """
        Same as :func:`~ignis.window_manager.WindowManager.open_window`.
        """
        self.__call_window_method("OpenWindow", window_name)

    def close_window(self, window_name: str) -> None:
        """
        Same as :func:`~ignis.window_manager.WindowManager.close_window`.
        """
        self.__call_window_method("CloseWindow", window_name)

    def toggle_window(self, window_name: str) -> None:
        """
        Same as :func:`~ignis.window_manager.WindowManager.toggle_window`.
        """
        self.__call_window_method("ToggleWindow", window_name)

    def list_windows(self) -> list[str]:
        """
        Get a list of all window names.

        Returns:
            list[str]: A list of all window names.
        """
        return self.__call_dbus_method("ListWindows")

    def quit(self) -> None:
        """
        Same as :func:`~ignis.app.IgnisApp.quit`.
        """
        self.__call_dbus_method("Quit")

    def inspector(self) -> None:
        """
        Same as :func:`~ignis.app.IgnisApp.inspector`.
        """
        self.__call_dbus_method("Inspector")

    def run_python(self, code: str) -> None:
        """
        Run a Python code inside the Ignis process.

        Args:
            code: The Python code to execute.
        """
        self.__call_dbus_method("RunPython", "(s)", code)

    def run_file(self, path: str) -> None:
        """
        Run a Python file inside Ignis daemon.

        Args:
            path: The path to the Python file to execute.
        """
        self.__call_dbus_method("RunFile", "(s)", path)

    def reload(self) -> None:
        """
        Same as :func:`~ignis.app.IgnisApp.reload`.
        """
        self.__call_dbus_method("Reload")
