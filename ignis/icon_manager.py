from ignis import utils
from ignis.gobject import IgnisGObjectSingleton, IgnisProperty, IgnisSignal
from gi.repository import Gtk  # type: ignore


class IconManager(IgnisGObjectSingleton):
    """
    A simple class to add and remove custom icons.
    """

    def __init__(self):
        super().__init__()

        self._icon_theme = Gtk.IconTheme.get_for_display(utils.get_gdk_display())
        self._added_icons: list[str] = []

    @IgnisSignal
    def icons_added(self, path: str):
        """
        Emitted when a custom icons path has been added.

        Args:
            path: The path to icons.
        """

    @IgnisSignal
    def icons_removed(self, path: str):
        """
        Emitted when a custom icons path has been removed.

        Args:
            path: The path to icons.
        """

    @IgnisProperty
    def added_icons(self) -> list[str]:
        """
        The list of icon paths added via :func:`add_icons`.
        """
        return self._added_icons

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

        then, add this to your ``config.py``:

        .. code-block:: python

            import os
            from ignis import utils
            from ignis.icon_manager import IconManager

            icon_manager = IconManager.get_default()

            icon_manager.add_icons(os.path.join(utils.get_current_dir(), "icons"))
        """
        self._icon_theme.add_search_path(path)
        self._added_icons.append(path)

        self.notify("added-icons")
        self.emit("icons-added", path)

    def remove_icons(self, path: str) -> None:
        """
        Remove added icons by their path.

        Args:
            path: The path to the directory.
        """
        search_path = self._icon_theme.get_search_path()

        if not search_path:
            return

        search_path.remove(path)

        self._icon_theme.set_search_path(search_path)
        self._added_icons.remove(path)

        self.notify("added-icons")
        self.emit("icons-removed", path)
