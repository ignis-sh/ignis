from gi.repository import Gtk  # type: ignore
from ignis.base_widget import BaseWidget
from ignis.gobject import IgnisProperty


class Separator(Gtk.Separator, BaseWidget):
    """
    Bases: :class:`Gtk.Separator`

    A separator widget.

    Args:
        **kwargs: Properties to set.

    .. code-block:: python

        widgets.Separator(
            vertical=False,
        )
    """

    __gtype_name__ = "IgnisSeparator"
    __gproperties__ = {**BaseWidget.gproperties}

    def __init__(self, **kwargs):
        Gtk.Separator.__init__(self)
        BaseWidget.__init__(self, **kwargs)

    @IgnisProperty
    def vertical(self) -> bool:
        """
        Whether the separator is vertical.
        """
        return self.get_orientation() == Gtk.Orientation.VERTICAL

    @vertical.setter
    def vertical(self, value: bool) -> None:
        if value:
            self.set_property("orientation", Gtk.Orientation.VERTICAL)
        else:
            self.set_property("orientation", Gtk.Orientation.HORIZONTAL)
