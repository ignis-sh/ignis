from gi.repository import Gtk  # type: ignore
from ignis.gobject import IgnisGObject
from ignis.gobject import IgnisProperty


class StackPage(IgnisGObject):
    """
    Bases: :class:`~ignis.gobject.IgnisGObject`

    Intented to use with :class:`~ignis.widgets.Stack`.

    Args:
        title: The title. It will be used by :class:`~ignis.widgets.StackSwitcher` to display :attr:`child` in a tab bar.
        child: The child widget.

    .. warning::
        It is not a widget.
    """

    def __init__(self, title: str, child: Gtk.Widget):
        super().__init__()
        self._title = title
        self._child = child

    @IgnisProperty
    def title(self) -> str:
        """
        The title.
        It will be used by :class:`~ignis.widgets.StackSwitcher` to display :attr:`child` in a tab bar.
        """
        return self._title

    @IgnisProperty
    def child(self) -> Gtk.Widget:
        """
        The child widget.
        """
        return self._child
