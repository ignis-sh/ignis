from gi.repository import GLib  # type: ignore
from ignis import utils
from ignis.dbus import DBusService
from ignis.gobject import IgnisGObject
from ignis.exceptions import WindowNotFoundError
from ignis.window_manager import WindowManager
from typing import TYPE_CHECKING

window_manager = WindowManager.get_default()

if TYPE_CHECKING:
    from ignis.app import IgnisApp


class IgnisIpc(IgnisGObject):
    def __init__(self, name: str, app: "IgnisApp"):
        super().__init__()

        self._name = name
        self._app = app

        self.__dbus = DBusService(
            name=name,
            object_path="/com/github/linkfrg/ignis",
            info=utils.load_interface_xml("com.github.linkfrg.ignis"),
        )

        self.__dbus.register_dbus_method(name="OpenWindow", method=self.__OpenWindow)
        self.__dbus.register_dbus_method(name="CloseWindow", method=self.__CloseWindow)
        self.__dbus.register_dbus_method(
            name="ToggleWindow", method=self.__ToggleWindow
        )
        self.__dbus.register_dbus_method(name="Quit", method=self.__Quit)
        self.__dbus.register_dbus_method(name="Inspector", method=self.__Inspector)
        self.__dbus.register_dbus_method(name="RunPython", method=self.__RunPython)
        self.__dbus.register_dbus_method(name="RunFile", method=self.__RunFile)
        self.__dbus.register_dbus_method(name="Reload", method=self.__Reload)
        self.__dbus.register_dbus_method(name="ListWindows", method=self.__ListWindows)

    def __call_window_method(self, type_: str, window_name: str) -> GLib.Variant:
        try:
            getattr(window_manager, f"{type_}_window")(window_name)
            return GLib.Variant("(b)", (True,))
        except WindowNotFoundError:
            return GLib.Variant("(b)", (False,))

    def __OpenWindow(self, invocation, window_name: str) -> GLib.Variant:
        return self.__call_window_method("open", window_name)

    def __CloseWindow(self, invocation, window_name: str) -> GLib.Variant:
        return self.__call_window_method("close", window_name)

    def __ToggleWindow(self, invocation, window_name: str) -> GLib.Variant:
        return self.__call_window_method("toggle", window_name)

    def __ListWindows(self, invocation) -> GLib.Variant:
        return GLib.Variant("(as)", (window_manager.list_window_names(),))

    def __RunPython(self, invocation, code: str) -> None:
        invocation.return_value(None)
        exec(code)

    def __RunFile(self, invocation, path: str) -> None:
        invocation.return_value(None)
        with open(path) as file:
            code = file.read()
            exec(code)

    def __Inspector(self, invocation) -> None:
        utils.open_inspector()

    def __Reload(self, invocation) -> None:
        invocation.return_value(None)
        self._app.reload()

    def __Quit(self, invocation) -> None:
        self._app.quit()
