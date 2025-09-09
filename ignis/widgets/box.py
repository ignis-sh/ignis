from gi.repository import Gtk  # type: ignore
from ignis.base_widget import BaseWidget
from ignis.gobject import IgnisProperty


class Box(Gtk.Box, BaseWidget):
    """
    Bases: :class:`Gtk.Box`.

    The main layout widget.

    Args:
        **kwargs: Properties to set.

    .. hint::
        You can use generators to set children.

        .. code-block::

            widgets.Box(
                child=[widgets.Label(label=str(i)) for i in range(10)]
            )

    .. code-block:: python

        widgets.Box(
            child=[widgets.Label(label='heh'), widgets.Label(label='heh2')],
            vertical=False,
            homogeneous=False,
            spacing=52
        )
    """

    __gtype_name__ = "IgnisBox"
    __gproperties__ = {**BaseWidget.gproperties}

    def __init__(self, **kwargs):
        Gtk.Box.__init__(self)
        self._child: list[Gtk.Widget] = []
        BaseWidget.__init__(self, **kwargs)

    @IgnisProperty
    def child(self) -> list[Gtk.Widget]:
        """
        A list of child widgets.
        """
        return self._child

    @child.setter
    def child(self, child: list[Gtk.Widget]) -> None:
        for c in self._child:
            super().remove(c)

        self._child = []
        for c in child:
            if c:
                self.append(c)

    def append(self, child: Gtk.Widget) -> None:
        _orig_unparent = child.unparent

        def unparent_wrapper(*args, **kwargs):
            self.remove(child)
            _orig_unparent(*args, **kwargs)
            child.unparent = _orig_unparent

        child.unparent = unparent_wrapper
        self._child.append(child)
        super().append(child)
        self.notify("child")

    def remove(self, child: Gtk.Widget) -> None:
        self._child.remove(child)
        super().remove(child)
        self.notify("child")

    def prepend(self, child: Gtk.Widget) -> None:
        self._child.insert(0, child)
        super().prepend(child)
        self.notify("child")

    @IgnisProperty
    def vertical(self) -> bool:
        """
        Whether the box arranges children vertically.

        Default: ``False``.
        """
        return self.get_orientation() == Gtk.Orientation.VERTICAL

    @vertical.setter
    def vertical(self, value: bool) -> None:
        if value:
            self.set_property("orientation", Gtk.Orientation.VERTICAL)
        else:
            self.set_property("orientation", Gtk.Orientation.HORIZONTAL)
