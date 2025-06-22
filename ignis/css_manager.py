import os
from gi.repository import Gtk, GLib  # type: ignore
from dataclasses import dataclass
from ignis.gobject import IgnisGObjectSingleton
from collections.abc import Callable
from typing import Literal
from ignis.exceptions import CssParsingError, CssNotFoundError, CssAlreadyAppliedError
from ignis import utils


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
class _CssInfoBase:
    name: str
    priority: StylePriority = "application"
    compiler_function: Callable[[str], str] | None = None

    def get_string(self) -> str:
        raise NotImplementedError()


@dataclass(kw_only=True)
class CssInfoString(_CssInfoBase):
    string: str = ""

    def get_string(self) -> str:
        if self.compiler_function:
            return self.compiler_function(self.string)

        return self.string


@dataclass(kw_only=True)
class CssInfoPath(_CssInfoBase):
    path: str = ""
    autoreload: bool = True
    watch_dir: bool = True
    watch_recursively: bool = True

    custom_watch_paths: list[str] | None = None

    def get_string(self) -> str:
        if self.compiler_function:
            return self.compiler_function(self.path)

        with open(self.path) as f:
            return f.read()


class CssManager(IgnisGObjectSingleton):
    def __init__(self):
        self._css_infos: dict[
            str, tuple[CssInfoString | CssInfoPath, Gtk.CssProvider]
        ] = {}

        self._watchers: dict[str, utils.FileMonitor] = {}

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
            raise CssNotFoundError(name)

        file_monitor.cancel()

    def apply_css(self, info: CssInfoString | CssInfoPath) -> None:
        display = utils.get_gdk_display()

        if info.name in self._css_infos:
            raise CssAlreadyAppliedError(info.name)

        provider = Gtk.CssProvider()
        provider.connect("parsing-error", _raise_css_parsing_error)

        provider.load_from_string(info.get_string())

        Gtk.StyleContext.add_provider_for_display(
            display,
            provider,
            GTK_STYLE_PRIORITIES[info.priority],
        )

        self._css_infos[info.name] = info, provider

        if isinstance(info, CssInfoPath) and info.autoreload:
            self.__start_watching(info)

    def remove_css(self, name: str) -> None:
        display = utils.get_gdk_display()

        info, provider = self._css_infos.pop(name, (None, None))

        if info is None or provider is None:
            raise CssNotFoundError(name)

        if isinstance(info, CssInfoPath) and info.autoreload:
            self.__stop_watching(info.name)

        Gtk.StyleContext.remove_provider_for_display(
            display,
            provider,
        )

    def reset_css(self) -> None:
        """
        Reset all applied CSS/SCSS/SASS styles.

        Raises:
            DisplayNotFoundError
        """
        for name in self._css_infos.copy().keys():
            self.remove_css(name)

    def reload_css(self, name: str) -> None:
        """
        Reload CSS by its name.

        Args:
            name: The name of the applied css.

        Raises:
            DisplayNotFoundError
        """
        info, _ = self._css_infos.get(name, (None, None))

        if not info:
            raise CssNotFoundError(name)

        self.remove_css(name)
        self.apply_css(info)

    def reload_all_css(self) -> None:
        """
        Reload all applied CSS/SCSS/Sass styles.

        Raises:
            DisplayNotFoundError
        """
        for name in self._css_infos.copy().keys():
            self.reload_css(name)
