from gi.repository import Gtk  # type: ignore
from ignis.base_widget import BaseWidget


class HeaderBar(Gtk.HeaderBar, BaseWidget):
    """
    Bases: :class:`Gtk.HeaderBar`

    A custom title bar with decorations like a close button and title.

    Args:
        **kwargs: Properties to set.

    .. code-block:: python

        widgets.HeaderBar(
            show_title_buttons=True,
        )
    """

    __gtype_name__ = "IgnisHeaderBar"
    __gproperties__ = {**BaseWidget.gproperties}

    def __init__(self, **kwargs):
        Gtk.HeaderBar.__init__(self)
        BaseWidget.__init__(self, **kwargs)
