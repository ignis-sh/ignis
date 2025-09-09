from gi.repository import Gtk  # type: ignore
from ignis.base_widget import BaseWidget
from collections.abc import Callable
from ignis.gobject import IgnisProperty


class ListBoxRow(Gtk.ListBoxRow, BaseWidget):
    """
    Bases: :class:`Gtk.ListBoxRow`

    A row for :class:`~ignis.widgets.listbox.ListBox`.

    Args:
        **kwargs: Properties to set.

    .. code-block:: python

        widgets.ListBoxRow(
            child=widgets.Label(label="row 1"),
            on_activate=lambda x: print("selected row 1"),
            selected=True
        )
    """

    __gtype_name__ = "IgnisListBoxRow"
    __gproperties__ = {**BaseWidget.gproperties}

    def __init__(self, **kwargs):
        Gtk.ListBoxRow.__init__(self)
        self._on_activate: Callable | None = None
        self._selected: bool = False
        BaseWidget.__init__(self, **kwargs)

    @IgnisProperty
    def on_activate(self) -> Callable:
        """
        The function to call when the user selects the row.
        """
        return self._on_activate

    @on_activate.setter
    def on_activate(self, value: Callable) -> None:
        self._on_activate = value

    @IgnisProperty
    def selected(self) -> bool:
        """
        Whether the row is selected by default.
        """
        return self._selected

    @selected.setter
    def selected(self, value: bool) -> None:
        self._selected = value
