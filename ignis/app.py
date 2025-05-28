from __future__ import annotations
import os
import sys
import datetime
from dataclasses import dataclass
from typing import Literal
from ignis.dbus import DBusService
from ignis.utils import Utils
from loguru import logger
from gi.repository import Gtk, Gdk, Gio, GLib  # type: ignore
from ignis.gobject import IgnisGObject, IgnisProperty, IgnisSignal
from ignis.exceptions import (
    WindowAddedError,
    WindowNotFoundError,
    DisplayNotFoundError,
    StylePathNotFoundError,
    StylePathAppliedError,
    CssParsingError,
)
from ignis.logging import configure_logger

StylePriority = Literal["application", "fallback", "settings", "theme", "user"]

GTK_STYLE_PRIORITIES: dict[StylePriority, int] = {
    "application": Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
    "fallback": Gtk.STYLE_PROVIDER_PRIORITY_FALLBACK,
    "settings": Gtk.STYLE_PROVIDER_PRIORITY_SETTINGS,
    "theme": Gtk.STYLE_PROVIDER_PRIORITY_THEME,
    "user": Gtk.STYLE_PROVIDER_PRIORITY_USER,
}


def raise_css_parsing_error(
    css_provider: Gtk.CssProvider, section: Gtk.CssSection, gerror: GLib.Error
) -> None:
    raise CssParsingError(section, gerror)


@dataclass
class _CssProviderInfo:
    provider: Gtk.CssProvider
    path: str
    priority: StylePriority
    compiler: Literal["sass", "grass"] | None = None


class IgnisApp(Gtk.Application, IgnisGObject):
    """
    Application class.

    .. danger::

        Do not initialize this class!
        Instead, use the already initialized instance as shown below.

        .. code-block:: python

            from ignis.app import IgnisApp

            app = IgnisApp.get_default()
    """

    _instance: IgnisApp | None = None  # type: ignore

    def __init__(self):
        Gtk.Application.__init__(
            self,
            application_id="com.github.linkfrg.ignis",
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
        )
        IgnisGObject.__init__(self)

        self.__dbus = DBusService(
            name="com.github.linkfrg.ignis",
            object_path="/com/github/linkfrg/ignis",
            info=Utils.load_interface_xml("com.github.linkfrg.ignis"),
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

        self._config_path: str | None = None
        self._css_providers: dict[str, _CssProviderInfo] = {}
        self._windows: dict[str, Gtk.Window] = {}
        self._autoreload_config: bool = True
        self._autoreload_css: bool = True
        self._reload_on_monitors_change: bool = True
        self._is_ready = False
        self._widgets_style_priority: StylePriority = "application"

    def __watch_config(
        self, file_monitor: Utils.FileMonitor, path: str, event_type: str
    ) -> None:
        if event_type != "changes_done_hint":
            return

        if not os.path.isdir(path) and "__pycache__" not in path:
            extension = os.path.splitext(path)[1]
            if extension == ".py" and self.autoreload_config:
                self.reload()
            elif extension in (".css", ".scss", ".sass") and self.autoreload_css:
                self.reload_css()

    def __watch_monitors(self) -> None:
        def callback(*_) -> None:
            if self._reload_on_monitors_change is True:
                logger.info("Monitors have changed, reloading.")
                self.reload()

        monitors = Utils.get_monitors()
        monitors.connect("items-changed", callback)

    @classmethod
    def get_default(cls: type[IgnisApp]) -> IgnisApp:
        """
        Get the default Application object for this process.
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @IgnisSignal
    def ready(self):
        """
        Emitted when the configuration has been parsed.

        .. hint::
            To handle shutdown of the application use the ``shutdown`` signal.
        """

    @IgnisProperty
    def is_ready(self) -> bool:
        """
        Whether configuration is parsed and app is ready.
        """
        return self._is_ready

    @IgnisProperty
    def windows(self) -> list[Gtk.Window]:
        """
        A list of windows added to this application.
        """
        return list(self._windows.values())

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

    @IgnisProperty
    def autoreload_css(self) -> bool:
        """
        Whether to automatically reload the CSS style when it changes (only .css/.scss/.sass files).

        Default: ``True``.
        """
        return self._autoreload_css

    @autoreload_css.setter
    def autoreload_css(self, value: bool) -> None:
        self._autoreload_css = value

    @IgnisProperty
    def reload_on_monitors_change(self) -> bool:
        """
        Whether to reload Ignis on monitors change (connect/disconnect).

        Default: ``True``.
        """
        return self._reload_on_monitors_change

    @reload_on_monitors_change.setter
    def reload_on_monitors_change(self, value: bool) -> None:
        self._reload_on_monitors_change = value

    @IgnisProperty
    def widgets_style_priority(self) -> StylePriority:
        """
        The priority used for each widget style
        unless a widget specifies a custom style priority using :attr:`~ignis.base_widget.BaseWidget.style_priority`.
        More info about style priorities: :obj:`Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION`.

        Default: ``"application"``.

        .. warning::
            Changing this property won't affect already initialized widgets!
            If you want to set a custom global style priority for all widgets, do this at the start of the configuration.

            .. code-block:: python

                from ignis.app import IgnisApp

                app = IgnisApp.get_default()

                app.widgets_style_priority = "user"

                # ... rest of config goes here
        """
        return self._widgets_style_priority

    @widgets_style_priority.setter
    def widgets_style_priority(self, value: StylePriority) -> None:
        self._widgets_style_priority = value

    def _setup(self, config_path: str) -> None:
        """
        :meta private:
        """
        self._config_path = config_path

    def apply_css(
        self,
        style_path: str,
        style_priority: StylePriority = "application",
        compiler: Literal["sass", "grass"] | None = None,
    ) -> None:
        """
        Apply a CSS/SCSS/SASS style from a path.
        If ``style_path`` has a ``.sass`` or ``.scss`` extension, it will be automatically compiled.
        Requires either ``dart-sass`` or ``grass-sass`` for SASS/SCSS compilation.

        Args:
            style_path: Path to the .css/.scss/.sass file.
            style_priority: A priority of the CSS style. More info about style priorities: :obj:`Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION`.
            compiler: The desired Sass compiler.

        .. warning::
            ``style_priority`` won't affect a style applied to widgets using the ``style`` property,
            for these purposes use :attr:`widgets_style_priority` or :attr:`ignis.base_widget.BaseWidget.style_priority`.

        Raises:
            StylePathAppliedError: if the given style path is already to the application.
            DisplayNotFoundError
            CssParsingError: If an error occured while parsing the CSS/SCSS file. NOTE: If you compile a SASS/SCSS file, it will print the wrong section.
        """

        display = Gdk.Display.get_default()

        if not display:
            raise DisplayNotFoundError()

        if style_path in self._css_providers:
            raise StylePathAppliedError(style_path)

        if not os.path.exists(style_path):
            raise FileNotFoundError(
                f"Provided style path doesn't exists: '{style_path}'"
            )

        if style_path.endswith(".scss") or style_path.endswith(".sass"):
            css_style = Utils.sass_compile(path=style_path, compiler=compiler)
        elif style_path.endswith(".css"):
            with open(style_path) as file:
                css_style = file.read()
        else:
            raise ValueError(
                'The "style_path" argument must be a path to a CSS, SASS, or SCSS file'
            )

        provider = Gtk.CssProvider()
        provider.connect("parsing-error", raise_css_parsing_error)

        provider.load_from_string(css_style)

        Gtk.StyleContext.add_provider_for_display(
            display,
            provider,
            GTK_STYLE_PRIORITIES[style_priority],
        )

        self._css_providers[style_path] = _CssProviderInfo(
            provider=provider,
            path=style_path,
            priority=style_priority,
            compiler=compiler,
        )

        logger.info(f"Applied css: {style_path}")

    def remove_css(self, style_path: str) -> None:
        """
        Remove the applied CSS/SCSS/SASS style by its path.

        Args:
            style_path: Path to the applied .css/.scss/.sass file.

        Raises:
            StylePathNotFoundError: if the given style path is not applied to the application.
            DisplayNotFoundError
        """

        display = Gdk.Display.get_default()
        if not display:
            raise DisplayNotFoundError()

        provider_info = self._css_providers.pop(style_path, None)

        if provider_info is None:
            raise StylePathNotFoundError(style_path)

        Gtk.StyleContext.remove_provider_for_display(
            display,
            provider_info.provider,
        )

    def reset_css(self) -> None:
        """
        Reset all applied CSS/SCSS/SASS styles.

        Raises:
            DisplayNotFoundError
        """
        for style_path in self._css_providers.copy().keys():
            self.remove_css(style_path)

    def reload_css(self) -> None:
        """
        Reload all applied CSS/SCSS/SASS styles.

        Raises:
            DisplayNotFoundError
        """
        css_providers = self._css_providers.copy().values()
        self.reset_css()

        for provider_info in css_providers:
            self.apply_css(
                style_path=provider_info.path,
                style_priority=provider_info.priority,
                compiler=provider_info.compiler,
            )

    def add_icons(self, path: str) -> None:
        """
        Add custom SVG icons from a directory.

        The directory must contain ``hicolor/scalable/actions`` directory, icons must be inside ``actions`` directory.

        Args:
            path: Path to the directory.

        For example, place icons inside the Ignis config directory:

        .. code-block:: bash

            ~/.config/ignis
            ├── config.py
            ├── icons
            │   └── hicolor
            │       └── scalable
            │           └── actions
            │               ├── aaaa-symbolic.svg
            │               └── some-icon.svg

        .. note::
            To apply a CSS color to an icon, its name and filename must end with ``-symbolic``.

        then, add this to your ``config.py`` :

        .. code-block:: python

            from ignis.utils import Utils
            from ignis.app import IgnisApp

            app = IgnisApp.get_default()

            app.add_icons(f"{Utils.get_current_dir()}/icons")
        """
        display = Gdk.Display.get_default()

        if not display:
            raise DisplayNotFoundError()

        icon_theme = Gtk.IconTheme.get_for_display(display)
        icon_theme.add_search_path(path)

    def do_activate(self) -> None:
        """
        :meta private:
        """
        self.hold()
        self.__watch_monitors()

        if not self._config_path:
            raise ValueError("Set up config_path before trying to run application")

        if not os.path.exists(self._config_path):
            raise FileNotFoundError(
                f"Provided config path doesn't exists: {self._config_path}"
            )

        config_dir = os.path.dirname(self._config_path)
        config_filename = os.path.splitext(os.path.basename(self._config_path))[0]

        logger.info(f"Using configuration file: {self._config_path}")

        self._monitor = Utils.FileMonitor(
            path=config_dir, callback=self.__watch_config, recursive=True
        )

        sys.path.append(config_dir)
        __import__(config_filename)

        self._is_ready = True
        self.emit("ready")
        logger.info("Ready.")

        date = datetime.datetime.now()

        if date.month == 12 and date.day in [30, 31]:
            self.__happy_new_year()
        elif date.month == 1 and date.day in [1, 2]:
            self.__happy_new_year()

    def __happy_new_year(self) -> None:
        logger.success("Happy New Year!")

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

    def add_window(self, window_name: str, window: Gtk.Window) -> None:  # type: ignore
        """
        Add a window.
        You typically shouldn't use this method, as windows are added to the app automatically.

        Args:
            window_name: The window's namespace.
            window: The window instance.

        Raises:
            WindowAddedError: If a window with the given namespace already exists.
        """
        if window_name in self._windows:
            raise WindowAddedError(window_name)

        self._windows[window_name] = window

    def remove_window(self, window_name: str) -> None:  # type: ignore
        """
        Remove a window by its name.
        The window will be removed from the application.

        Args:
            window_name: The window's namespace.

        Raises:
            WindowNotFoundError: If a window with the given namespace does not exist.
        """
        window = self._windows.pop(window_name, None)
        if not window:
            raise WindowNotFoundError(window_name)

    def reload(self) -> None:
        """
        Reload Ignis.
        """
        self.quit()
        os.execl(sys.executable, sys.executable, *sys.argv)

    def quit(self) -> None:
        """
        Quit Ignis.
        """
        super().quit()
        logger.info("Quitting.")

    def inspector(self) -> None:
        """
        Open GTK Inspector.
        """
        Gtk.Window.set_interactive_debugging(True)

    def __call_window_method(self, _type: str, window_name: str) -> GLib.Variant:
        try:
            getattr(self, f"{_type}_window")(window_name)
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
        return GLib.Variant("(as)", (tuple(self._windows),))

    def __RunPython(self, invocation, code: str) -> None:
        invocation.return_value(None)
        exec(code)

    def __RunFile(self, invocation, path: str) -> None:
        invocation.return_value(None)
        with open(path) as file:
            code = file.read()
            exec(code)

    def __Inspector(self, invocation) -> None:
        self.inspector()

    def __Reload(self, invocation) -> None:
        invocation.return_value(None)
        self.reload()

    def __Quit(self, invocation) -> None:
        self.quit()


def run_app(config_path: str, debug: bool) -> None:
    configure_logger(debug)

    app = IgnisApp.get_default()

    app._setup(config_path)

    try:
        app.run(None)
    except KeyboardInterrupt:
        pass  # app.quit() will be called automatically
