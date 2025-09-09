from gi.repository import Gtk  # type: ignore
from ignis.base_widget import BaseWidget


class Scroll(Gtk.ScrolledWindow, BaseWidget):
    """
    Bases: :class:`Gtk.ScrolledWindow`

    A container that accepts a single child widget and makes it scrollable.

    Args:
        **kwargs: Properties to set.

    .. code-block:: python

        widgets.Scroll(
            child=widgets.Box(
                vertical=True,
                child=[widgets.Label(i) for i in range(30)]
            )
        )
    """

    __gtype_name__ = "IgnisScroll"
    __gproperties__ = {**BaseWidget.gproperties}

    def __init__(self, **kwargs):
        Gtk.ScrolledWindow.__init__(self)
        self.override_enum("hscrollbar_policy", Gtk.PolicyType)
        self.override_enum("vscrollbar_policy", Gtk.PolicyType)
        BaseWidget.__init__(self, **kwargs)
