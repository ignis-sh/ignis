from gi.repository import Gtk  # type: ignore
from ignis.base_widget import BaseWidget
from collections.abc import Callable
from ignis.gobject import IgnisProperty


class Entry(Gtk.Entry, BaseWidget):  # type: ignore
    """
    Bases: :class:`Gtk.Entry`

    An input field. To make it work, set the ``kb_mode`` property of the window to ``on_demand`` or ``exclusive``.

    Args:
        **kwargs: Properties to set.

    .. code-block:: python

        widgets.Entry(
            placeholder_text="placeholder",
            on_accept=lambda x: print(x.text),
            on_change=lambda x: print(x.text),
        )
    """

    __gtype_name__ = "IgnisEntry"
    __gproperties__ = {**BaseWidget.gproperties}

    def __init__(self, **kwargs):
        Gtk.Entry.__init__(self)
        self._on_accept: Callable | None = None
        self._on_change: Callable | None = None
        BaseWidget.__init__(self, **kwargs)

        self.connect(
            "activate", lambda x: self.on_accept(x) if self.on_accept else None
        )
        self.connect(
            "notify::text", lambda x, y: self.on_change(x) if self.on_change else None
        )

    @IgnisProperty
    def on_accept(self) -> Callable:
        """
        The function that will be called when the user hits the Enter key.
        """
        return self._on_accept

    @on_accept.setter
    def on_accept(self, value: Callable) -> None:
        self._on_accept = value

    @IgnisProperty
    def on_change(self) -> Callable:
        """
        The function that will be called when the text in the widget is changed (e.g., when the user types something into the entry).
        """
        return self._on_change

    @on_change.setter
    def on_change(self, value: Callable) -> None:
        self._on_change = value
