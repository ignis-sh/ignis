from gi.repository import Gtk  # type: ignore
from ignis.base_widget import BaseWidget
from ignis.widgets.listboxrow import ListBoxRow
from ignis.gobject import IgnisProperty


class ListBox(Gtk.ListBox, BaseWidget):
    """
    Bases: :class:`Gtk.ListBox`

    A vertical list that allows selecting rows. Well suited, for example, for a navigation bar.

    Args:
        **kwargs: Properties to set.

    .. code-block:: python

        Widget.ListBox(
            rows=[
                Widget.ListBoxRow(
                    child=Widget.Label(label="row 1"),
                    on_activate=lambda x: print("selected row 1"),
                ),
                Widget.ListBoxRow(
                    child=Widget.Label(label="row 2"),
                    on_activate=lambda x: print("selected row 2"),
                ),
            ]
        )
    """

    __gtype_name__ = "IgnisListBox"
    __gproperties__ = {**BaseWidget.gproperties}

    def __init__(self, **kwargs):
        Gtk.ListBox.__init__(self)
        self._rows: list[Gtk.Widget] = []
        BaseWidget.__init__(self, **kwargs)

        self.connect("row_activated", self.__on_row_activated)

    def __on_row_activated(self, x, row):
        if isinstance(row, ListBoxRow):
            if row.on_activate:
                row.on_activate(row)

    def activate_row(self, row: ListBoxRow) -> None:
        """
        Manually trigger the activation of the row.

        Args:
            row: The row to activate.
        """
        self.select_row(row)
        self.emit("row-activated", row)

    @IgnisProperty
    def rows(self) -> list[Gtk.Widget]:
        """
        A list of rows.
        """
        return self._rows

    @rows.setter
    def rows(self, value: list[Gtk.Widget]) -> None:
        for i in self._rows:
            self.remove(i)

        for i in value:
            self.append(i)

            if isinstance(i, ListBoxRow):
                if i.selected:
                    self.select_row(i)

        self._rows = value
