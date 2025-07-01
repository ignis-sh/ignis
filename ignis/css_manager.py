import os
from gi.repository import Gtk, GLib  # type: ignore
from dataclasses import dataclass
from ignis.gobject import IgnisGObjectSingleton, IgnisProperty, IgnisSignal
from collections.abc import Callable
from typing import Literal
from ignis.exceptions import (
    CssParsingError,
    CssInfoNotFoundError,
    CssInfoAlreadyAppliedError,
)
from ignis import utils
from loguru import logger


StylePriority = Literal["application", "fallback", "settings", "theme", "user"]

GTK_STYLE_PRIORITIES: dict[StylePriority, int] = {
    "application": Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
    "fallback": Gtk.STYLE_PROVIDER_PRIORITY_FALLBACK,
    "settings": Gtk.STYLE_PROVIDER_PRIORITY_SETTINGS,
    "theme": Gtk.STYLE_PROVIDER_PRIORITY_THEME,
    "user": Gtk.STYLE_PROVIDER_PRIORITY_USER,
}


def _raise_css_parsing_error(_, section: Gtk.CssSection, gerror: GLib.Error) -> None:
    raise CssParsingError(section, gerror)


@dataclass(kw_only=True)
class CssInfoBase:
    """
    The base class for CSS infos.

    You shouldn't use it, use :class:`CssInfoString` or :class:`CssInfoPath` instead.
    """

    #: The name of the info by which you will be able to use :class:`CssManager` functions.
    name: str

    #: The style priority.
    #: Most likely you should use either ``"application"`` or ``"user"``.
    #:
    #: * ``"user"`` - you want to override styles defined in ``~/.config/gtk-4.0/gtk.css``
    #: * ``"application"`` (the default one) - you do **not** want to override it.
    priority: StylePriority = "application"

    #: A custom compiler function. It should receive only one argument:
    #:
    #: - :class:`CssInfoString` - the string
    #: - :class:`CssInfoPath` - the path
    #:
    #: It must return a string containing a valid CSS code.
    compiler_function: Callable[[str], str] | None = None

    def _get_type(self) -> str:
        raise NotImplementedError()

    def _get_string(self) -> str:
        raise NotImplementedError()


@dataclass(kw_only=True)
class CssInfoString(CssInfoBase):
    """
    CSS info for a string.
    """

    #: A string containing CSS code.
    string: str

    def _get_type(self) -> str:
        return "string"

    def _get_string(self) -> str:
        if self.compiler_function:
            return self.compiler_function(self.string)

        return self.string


@dataclass(kw_only=True)
class CssInfoPath(CssInfoBase):
    """
    CSS info for a path.
    """

    #: The path to the CSS file.
    path: str

    #: Whether to automatically reload this info when the file changes.
    autoreload: bool = True

    #: Whether to additionally watch for the changes of the directory where the file is placed.
    watch_dir: bool = True

    #: Whether to watch the directory recursively.
    watch_recursively: bool = True

    def _get_type(self) -> str:
        return "path"

    def _get_string(self) -> str:
        if self.compiler_function:
            return self.compiler_function(self.path)

        with open(self.path) as f:
            return f.read()


class CssManager(IgnisGObjectSingleton):
    """
    The CSS manager. Provides convenient utilities to apply, remove, and reload CSS.

    Example usage:

    .. code-block::

        import os
        from ignis.css_manager import CssManager, CssInfoString, CssInfoPath
        from ignis import utils

        css_manager = CssManager.get_default()

        # Apply from a path
        css_manager.apply_css(
            CssInfoPath(
                name="main",
                path="PATH/TO/style.css", # e.g., os.path.join(utils.get_current_dir(), "style.css"),
            )
        )

        # Apply from a string
        css_manager.apply_css(
            CssInfoString(
                name="some-name",
                string="* { background-color: red; }",
            )
        )

        # Remove an applied info
        css_manager.remove_css("some-name")

        # Reload an applied info
        css_manager.reload_css("main")

    **Sass/SCSS compilation**

    You can use :attr:`CssInfoBase.compiler_function` to compile Sass/SCSS:

    .. code-block::

        from ignis.css_manager import CssManager, CssInfoString, CssInfoPath
        from ignis import utils

        css_manager = CssManager.get_default()

        # File
        css_manager.apply_css(
            CssInfoPath(
                name="main",
                path="PATH/TO/style.scss",
                compiler_function=lambda path: utils.sass_compile(path=path),
            )
        )

        # String
        css_manager.apply_css(
            CssInfoString(
                name="some-name",
                string="some sass/scss string",
                compiler_function=lambda string: utils.sass_compile(string=string),
            )
        )
    """

    def __init__(self):
        self._css_infos: dict[
            str, tuple[CssInfoString | CssInfoPath, Gtk.CssProvider]
        ] = {}

        self._watchers: dict[str, utils.FileMonitor] = {}

        self._widgets_style_priority: StylePriority = "application"

        super().__init__()

    def __watch_css_files(self, path: str, event_type: str, name: str) -> None:
        if event_type != "changes_done_hint":
            return

        if not os.path.isdir(path) and "__pycache__" not in path:
            extension = os.path.splitext(path)[1]
            if extension in (".css", ".scss", ".sass"):
                self.reload_css(name)

    def __start_watching(self, info: CssInfoPath) -> None:
        watch_path: str

        if info.watch_dir:
            watch_path = os.path.dirname(info.path)
        else:
            watch_path = info.path

        self._watchers[info.name] = utils.FileMonitor(
            path=watch_path,
            recursive=info.watch_recursively,
            prevent_gc=False,
            callback=lambda _, path, event_type, name=info.name: self.__watch_css_files(
                path, event_type, name
            ),
        )

    def __stop_watching(self, name: str) -> None:
        file_monitor = self._watchers.pop(name, None)

        if not file_monitor:
            raise CssInfoNotFoundError(name)

        file_monitor.cancel()

    @IgnisSignal
    def applied_css(self, info: object):
        """
        Emitted when a CSS info has been applied.

        Args:
            info(CssInfoString | CssInfoPath): The applied CSS.
        """

    @IgnisSignal
    def removed_css(self, info: object):
        """
        Emitted when a CSS info has been removed.

        Args:
            info(CssInfoString | CssInfoPath): The removed CSS.
        """

    @IgnisSignal
    def resetted_css(self):
        """
        Emitted when all applied CSS infos have been resetted.
        """

    @IgnisSignal
    def reloaded_css(self, info: object):
        """
        Emitted when a CSS info has been reloaded.

        Args:
            info(CssInfoString | CssInfoPath): The reloaded CSS.
        """

    @IgnisSignal
    def reloaded_all_css(self):
        """
        Emitted when all applied CSS infos have been reloaded.
        """

    @IgnisProperty
    def widgets_style_priority(self) -> StylePriority:
        """
        The priority used for each widget style
        unless a widget specifies a custom style priority using :attr:`~ignis.base_widget.BaseWidget.style_priority`.
        More info about style priorities: :obj:`Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION`.

        Default: ``"application"``.

        .. warning::
            Changing this property won't affect already initialized widgets!
            If you want to set a custom global style priority for all widgets, do this before initializing them
            (e.g., at the start of your configuration).

        .. code-block:: python

            from ignis.css_manager import CssManager

            css_manager = CssManager.get_default()

            css_manager.widgets_style_priority = "user"

        """
        return self._widgets_style_priority

    @widgets_style_priority.setter
    def widgets_style_priority(self, value: StylePriority) -> None:
        self._widgets_style_priority = value

    def apply_css(self, info: CssInfoString | CssInfoPath) -> None:
        """
        Apply a CSS info.

        Args:
            info: The CSS info to apply.

        Raises:
            CssInfoAlreadyAppliedError
            CssParsingError
        """
        if info.name in self._css_infos:
            raise CssInfoAlreadyAppliedError(info.name)

        provider = Gtk.CssProvider()
        provider.connect("parsing-error", _raise_css_parsing_error)

        provider.load_from_string(info._get_string())

        Gtk.StyleContext.add_provider_for_display(
            utils.get_gdk_display(),
            provider,
            GTK_STYLE_PRIORITIES[info.priority],
        )

        self._css_infos[info.name] = info, provider

        if isinstance(info, CssInfoPath) and info.autoreload:
            self.__start_watching(info)

        self.emit("applied-css", info)
        logger.info(f'Applied CSS info: "{info.name}" | type: {info._get_type()}')

    def remove_css(self, name: str) -> None:
        """
        Remove CSS info by its name.

        Args:
            name: The name of the CSS info to remove.

        Raises:
            CssInfoNotFoundError
        """
        display = utils.get_gdk_display()

        info, provider = self._css_infos.pop(name, (None, None))

        if info is None or provider is None:
            raise CssInfoNotFoundError(name)

        if isinstance(info, CssInfoPath) and info.autoreload:
            self.__stop_watching(info.name)

        Gtk.StyleContext.remove_provider_for_display(
            display,
            provider,
        )

        self.emit("removed-css", info)
        logger.info(f'Removed CSS info: "{name}"')

    def reset_css(self) -> None:
        """
        Remove **all** applied CSS infos.
        """
        logger.info("Resetting all CSS infos...")

        for name in self._css_infos.copy().keys():
            self.remove_css(name)

        self.emit("resetted-css")

    def reload_css(self, name: str) -> None:
        """
        Reload a CSS info by its name.

        Args:
            name: The name of the CSS info to reload.
        """
        logger.info(f'Reloading CSS info: "{name}"')

        info, _ = self._css_infos.get(name, (None, None))

        if not info:
            raise CssInfoNotFoundError(name)

        self.remove_css(name)
        self.apply_css(info)

        self.emit("reloaded-css", info)

    def reload_all_css(self) -> None:
        """
        Reload **all** applied CSS infos.
        """
        logger.info("Reloading all CSS infos...")

        for name in self._css_infos.copy().keys():
            self.reload_css(name)

        self.emit("reloaded-all-css")

    def get_css_info_by_name(self, name: str) -> CssInfoPath | CssInfoString | None:
        """
        Get an applied CSS info by its name:

        Args:
            name: The name of the CSS info to get.

        Returns:
            The CSS info, or ``None`` if the CSS info with the given name is not applied.
        """
        return self._css_infos.get(name, (None, None))[0]

    def list_css_infos(self) -> list[CssInfoString | CssInfoPath]:
        """
        List all applied CSS infos.

        Returns:
            A list of all applied CSS infos.
        """
        return [info for info, _ in self._css_infos.values()]

    def list_css_info_names(self) -> list[str]:
        """
        List names of all applied CSS infos.

        Returns:
            A list of all applied CSS info names.
        """
        return list(self._css_infos.keys())
