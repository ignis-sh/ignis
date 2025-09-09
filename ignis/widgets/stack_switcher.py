from gi.repository import Gtk  # type: ignore
from ignis.base_widget import BaseWidget


class StackSwitcher(Gtk.StackSwitcher, BaseWidget):
    """
    Bases: :class:`Gtk.StackSwitcher`

    The StackSwitcher shows a row of buttons to switch between :class:`~ignis.widgets.Stack` pages.

    Args:
        **kwargs: Properties to set.
    """

    __gtype_name__ = "IgnisStackSwitcher"
    __gproperties__ = {**BaseWidget.gproperties}

    def __init__(self, **kwargs):
        Gtk.StackSwitcher.__init__(self)
        BaseWidget.__init__(self, **kwargs)
