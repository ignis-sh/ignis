from gi.repository import Gtk, GObject  # type: ignore
from ignis.base_widget import BaseWidget


class Grid(Gtk.Grid, BaseWidget):
    """
    Bases: :class:`Gtk.Grid`

    A container that arranges its child widgets in rows and columns.

    .. code-block:: python

        Widget.Grid(
            child=[Widget.Button(label=str(i)), for i in range(100)],
            column_num=3
        )

    .. code-block:: python

        Widget.Grid(
            child=[Widget.Button(label=str(i)), for i in range(100)],
            row_num=3
        )
    """

    __gtype_name__ = "IgnisGrid"
    __gproperties__ = {**BaseWidget.gproperties}

    def __init__(self, **kwargs):
        Gtk.Grid.__init__(self)
        self._column_num: int | None = None
        self._row_num: int | None = None
        self._child: list[Gtk.Widget] = []
        BaseWidget.__init__(self, **kwargs)

    @GObject.Property
    def column_num(self) -> int:
        """
        - optional, read-write

        The number of columns.
        """
        return self._column_num

    @column_num.setter
    def column_num(self, value: int) -> None:
        self._column_num = value
        self.__apply()

    @GObject.Property
    def row_num(self) -> int:
        """
        - optional, read-write

        The number of rows. This will not take effect if ``column_num`` is specified.
        """
        return self._row_num

    @row_num.setter
    def row_num(self, value: int) -> None:
        self._row_num = value
        self.__apply()

    @GObject.Property
    def child(self) -> list[Gtk.Widget]:
        """
        - optional, read-write

        A list of child widgets.
        """
        return self._child

    @child.setter
    def child(self, child: list[Gtk.Widget]) -> None:
        for c in self._child:
            self.remove(c)
        self._child = child
        self.__apply()

    def __apply(self) -> None:
        if self.column_num:
            for i, c in enumerate(self.child):
                self.attach(c, i % self.column_num, i // self.column_num, 1, 1)
        elif self.row_num:
            for i, c in enumerate(self.child):
                self.attach(c, i // self.row_num, i % self.row_num, 1, 1)
        else:
            for c in self.child:
                self.attach(c, 1, 1, 1, 1)
