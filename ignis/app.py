from __future__ import annotations
import os
import sys
import ignis
import shutil
from typing import Literal
from ignis import utils
from loguru import logger
from gi.repository import Gtk, Gio  # type: ignore
from ignis.gobject import IgnisGObject, IgnisProperty, IgnisSignal
from ignis.exceptions import (
    StylePathNotFoundError,
    StylePathAppliedError,
    CssInfoNotFoundError,
    CssInfoAlreadyAppliedError,
    AppNotInitializedError,
)
from ignis.window_manager import WindowManager
from ignis.icon_manager import IconManager
from ignis.css_manager import CssManager, StylePriority, CssInfoPath
from ignis.config_manager import ConfigManager
from ignis._deprecation import (
    deprecated,
    deprecation_warning,
)
from ignis._ignis_ipc import IgnisIpc

window_manager = WindowManager.get_default()
config_manager = ConfigManager.get_default()


def _get_wm_depr_msg(name: str):
    return f"IgnisApp.{name}() is deprecated, use WindowManager.{name}() instead."


def _is_elf_file(path: str) -> bool:
    with open(path, "rb") as f:
        magic = f.read(4)
        return magic == b"\x7fELF"


class IgnisApp(Gtk.Application, IgnisGObject):
    """
    Bases: :class:`Gtk.Application`.

    The application class.

    .. danger::

        Do not initialize this class!
        Instead, use the already initialized instance as shown below.

        .. code-block:: python

            from ignis.app import IgnisApp

            app = IgnisApp.get_initialized()
    """

    _instance: IgnisApp | None = None  # type: ignore

    def __init__(self):
        Gtk.Application.__init__(
            self,
            application_id="com.github.linkfrg.ignis",
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
        )
        IgnisGObject.__init__(self)

        IgnisIpc(name="com.github.linkfrg.ignis", app=self)

        self._reload_on_monitors_change: bool = True

        # FIXME: deprecated
        self._autoreload_css: bool = True
        IgnisApp._instance = self

        # Put here because sphinx complains (as always)
        self._css_manager = CssManager.get_default()

    def __watch_monitors(self) -> None:
        def callback(*_) -> None:
            if self._reload_on_monitors_change is True:
                logger.info("Monitors have changed, reloading.")
                self.reload()

        monitors = utils.get_monitors()
        monitors.connect("items-changed", callback)

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

    @classmethod
    def get_initialized(cls) -> IgnisApp:
        """
        Guaranteed to return the default instance of the application for this process.
        If the application is not initialized, raises :class:`AppNotInitializedError`.

        Raises:
            AppNotInitializedError: If the application is not initialized yet.
            TypeError: If the default application is not an instance of :class:`IgnisApp`.
        """
        gapp = Gtk.Application.get_default()

        if not gapp:
            raise AppNotInitializedError()

        if not isinstance(gapp, IgnisApp):
            raise TypeError(
                "The default Gtk.Application is not an instance of IgnisApp"
            )

        return gapp

    def do_activate(self) -> None:
        """
        :meta private:
        """
        self.hold()
        self.__watch_monitors()

    def reload(self) -> None:
        """
        Reload Ignis.
        """
        self.quit()

        # https://github.com/linkfrg/ignis/issues/267
        # Nix wraps the Ignis executable, so bin/ignis is not python file anymore, but a binary file (ELF)
        # So, we launch this binary directly (it's always the first in sys.argv)
        if _is_elf_file(sys.argv[0]):
            os.execl(sys.argv[0], sys.argv[0], *sys.argv[1:])
        else:
            os.execl(sys.executable, sys.executable, *sys.argv)

    def quit(self) -> None:
        """
        Quit Ignis.
        """
        if ignis._temp_dir:
            logger.debug(f"Removing temp dir: {ignis._temp_dir}")
            try:
                shutil.rmtree(ignis._temp_dir)
            except FileNotFoundError:
                pass

        super().quit()
        logger.info("Quitting.")

    # =========================== DEPRECATED ZONE START ===========================

    @IgnisSignal
    def ready(self):
        """
        Emitted when the configuration has been parsed.

        .. hint::
            To handle shutdown of the application use the ``shutdown`` signal.

        .. deprecated:: 0.6
            Use :attr:`ignis.config_manager.ConfigManager.config_parsed` instead.
        """

    @IgnisProperty
    def is_ready(self) -> bool:
        """
        Whether configuration is parsed and app is ready.

        .. deprecated:: 0.6
            Use :attr:`ignis.config_manager.ConfigManager.is_config_parsed` instead.
        """
        return config_manager.is_config_parsed

    @IgnisProperty
    def windows(self) -> list[Gtk.Window]:
        """
        .. deprecated:: 0.6
            Use :attr:`~ignis.window_manager.WindowManager.windows` instead.
        """
        deprecation_warning(
            "IgnisApp.windows is deprecated, use WindowManager.windows instead."
        )
        return window_manager.windows

    @IgnisProperty
    def autoreload_config(self) -> bool:
        """
        Whether to automatically reload the configuration when it changes (only .py files).

        Default: ``True``.

        .. deprecated:: 0.6
            Use :attr:`ignis.config_manager.ConfigManager.autoreload_config` instead.
        """
        deprecation_warning(
            "IgnisApp.autoreload_config is deprecated, use ConfigManager.autoreload_config instead."
        )
        return config_manager.autoreload_config

    @autoreload_config.setter
    def autoreload_config(self, value: bool) -> None:
        config_manager.autoreload_config = value

    @IgnisProperty
    def autoreload_css(self) -> bool:
        """
        Whether to automatically reload the CSS style when it changes (only .css/.scss/.sass files).

        Default: ``True``.

        .. deprecated:: 0.6
            Use :attr:`ignis.css_manager.CssInfoPath.autoreload` instead.

        """
        deprecation_warning(
            "IgnisApp.autoreload_css is deprecated, use CssInfoPath.autoreload instead."
        )
        return self._autoreload_css

    @autoreload_css.setter
    def autoreload_css(self, value: bool) -> None:
        self._autoreload_css = value

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

        .. deprecated:: 0.6
            Use :attr:`ignis.css_manager.CssManager.widgets_style_priority` instead.
        """
        deprecation_warning(
            "IgnisApp.widgets_style_priority is deprecated, use CssManager.widgets_style_priority instead."
        )
        return self._css_manager.widgets_style_priority

    @widgets_style_priority.setter
    def widgets_style_priority(self, value: StylePriority) -> None:
        self._css_manager.widgets_style_priority = value

    @classmethod
    @deprecated(
        "IgnisApp.get_default() is deprecated, use IgnisApp.get_initialized() instead."
    )
    def get_default(cls: type[IgnisApp]) -> IgnisApp:
        """
        Get the default Application object for this process.

        .. deprecated::
            This function initializes the application if it hasn't been done already,
            which is not the intended behavior.
            Use :func:`get_initialized` instead.
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @deprecated(
        "IgnisApp.add_icons() is deprecated, use IconManager.add_icons() instead."
    )
    def add_icons(self, path: str) -> None:
        """
        .. deprecated:: 0.6
            Use :func:`ignis.icon_manager.IconManager.add_icons` instead.
        """
        IconManager.get_default().add_icons(path)

    @deprecated(
        "IgnisApp.apply_css() is deprecated, use CssManager.apply_css() instead."
    )
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

        .. deprecated:: 0.6
            Use :func:`ignis.css_manager.CssManager.apply_css` instead.
        """

        if style_path.endswith((".scss", ".sass")):

            def compiler_function(path: str) -> str:
                return utils.sass_compile(path=path, compiler=compiler)
        else:
            compiler_function = None  # type: ignore

        try:
            self._css_manager.apply_css(
                CssInfoPath(
                    name=style_path,
                    priority=style_priority,
                    compiler_function=compiler_function,
                    path=style_path,
                    autoreload=self.autoreload_css,
                )
            )
        except CssInfoAlreadyAppliedError:
            raise StylePathAppliedError(style_path) from None

    @deprecated(
        "IgnisApp.remove_css() is deprecated, use CssManager.remove_css() instead."
    )
    def remove_css(self, style_path: str) -> None:
        """
        Remove the applied CSS/SCSS/SASS style by its path.

        Args:
            style_path: Path to the applied .css/.scss/.sass file.

        Raises:
            StylePathNotFoundError: if the given style path is not applied to the application.
            DisplayNotFoundError

        .. deprecated:: 0.6
            Use :func:`ignis.css_manager.CssManager.remove_css` instead.
        """

        try:
            self._css_manager.remove_css(style_path)
        except CssInfoNotFoundError:
            raise StylePathNotFoundError(style_path) from None

    @deprecated(
        "IgnisApp.reset_css() is deprecated, use CssManager.reset_css() instead."
    )
    def reset_css(self) -> None:
        """
        Reset all applied CSS/SCSS/SASS styles.

        Raises:
            DisplayNotFoundError

        .. deprecated:: 0.6
            Use :func:`ignis.css_manager.CssManager.reset_css` instead.
        """
        try:
            self._css_manager.reset_css()
        except CssInfoNotFoundError as e:
            raise StylePathNotFoundError(e.name) from None

    @deprecated(
        "IgnisApp.reload_css() is deprecated, use CssManager.reload_css() or CssManager.reload_all_css() instead."
    )
    def reload_css(self) -> None:
        """
        Reload all applied CSS/SCSS/SASS styles.

        Raises:
            DisplayNotFoundError

        .. deprecated:: 0.6
            Use :func:`ignis.css_manager.CssManager.reload_css` or
            :func:`ignis.css_manager.CssManager.reload_all_css` instead.
        """
        self._css_manager.reload_all_css()

    @deprecated(_get_wm_depr_msg("get_window"))
    def get_window(self, window_name: str) -> Gtk.Window:
        """
        .. deprecated:: 0.6
            Use :func:`~ignis.window_manager.WindowManager.get_window` instead.
        """
        return window_manager.get_window(window_name)

    @deprecated(_get_wm_depr_msg("open_window"))
    def open_window(self, window_name: str) -> None:
        """
        .. deprecated:: 0.6
            Use :func:`~ignis.window_manager.WindowManager.open_window` instead.
        """
        window_manager.open_window(window_name)

    @deprecated(_get_wm_depr_msg("close_window"))
    def close_window(self, window_name: str) -> None:
        """
        .. deprecated:: 0.6
            Use :func:`~ignis.window_manager.WindowManager.close_window` instead.
        """
        window_manager.close_window(window_name)

    @deprecated(_get_wm_depr_msg("toggle_window"))
    def toggle_window(self, window_name: str) -> None:
        """
        .. deprecated:: 0.6
            Use :func:`~ignis.window_manager.WindowManager.toggle_window` instead.
        """
        window_manager.toggle_window(window_name)

    @deprecated(_get_wm_depr_msg("add_window"))
    def add_window(self, window_name: str, window: Gtk.Window) -> None:  # type: ignore
        """
        .. deprecated:: 0.6
            Use :func:`~ignis.window_manager.WindowManager.add_window` instead.
        """
        window_manager.add_window(window_name, window)

    @deprecated(_get_wm_depr_msg("remove_window"))
    def remove_window(self, window_name: str) -> None:  # type: ignore
        """
        .. deprecated:: 0.6
            Use :func:`~ignis.window_manager.WindowManager.remove_window` instead.
        """
        window_manager.remove_window(window_name)

    @deprecated(
        "IgnisApp.inspector() is deprecated, use utils.open_inspector() instead."
    )
    def inspector(self) -> None:
        """
        Open GTK Inspector.

        .. deprecated:: 0.6
            Use :func:`ignis.utils.open_inspector` instead.
        """
        utils.open_inspector()

    # ============================ DEPRECATED ZONE END ============================
