from gi.repository import Gtk  # type: ignore
from ignis.base_widget import BaseWidget
from ignis.gobject import IgnisProperty


class CenterBox(Gtk.CenterBox, BaseWidget):
    """
    Bases: :class:`Gtk.CenterBox`

    A box widget that contains three widgets, which are placed at the start, center, and end of the container.

    Args:
        **kwargs: Properties to set.

    .. code-block:: python

        widgets.CenterBox(
            vertical=False,
            start_widget=widgets.Label(label='start'),
            center_widget=widgets.Label(label='center'),
            end_widget=widgets.Label(label='end'),
        )
    """

    __gtype_name__ = "IgnisCenterBox"
    __gproperties__ = {**BaseWidget.gproperties}

    def __init__(self, **kwargs):
        Gtk.CenterBox.__init__(self)
        BaseWidget.__init__(self, **kwargs)

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
