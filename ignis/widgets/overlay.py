from gi.repository import Gtk  # type: ignore
from ignis.base_widget import BaseWidget
from ignis.gobject import IgnisProperty


class Overlay(Gtk.Overlay, BaseWidget):
    """
    Bases: :class:`Gtk.Overlay`

    A container that places its children on top of each other.
    The ``child`` property is the main child, on which other widgets defined in ``overlays`` will be placed on top.

    Args:
        **kwargs: Properties to set.

    .. code-block:: python

        widgets.Overlay(
            child=widgets.Label(label="This is the main child"),
            overlays=[
                widgets.Label(label="Overlay child 1"),
                widgets.Label(label="Overlay child 2"),
                widgets.Label(label="Overlay child 3"),
            ]
        )
    """

    __gtype_name__ = "IgnisOverlay"
    __gproperties__ = {**BaseWidget.gproperties}

    def __init__(self, **kwargs):
        Gtk.Overlay.__init__(self)
        self._overlays: list[Gtk.Widget] = []
        BaseWidget.__init__(self, **kwargs)

    @IgnisProperty
    def overlays(self) -> list[Gtk.Widget]:
        """
        A list of overlay widgets.
        """
        return self._overlays

    @overlays.setter
    def overlays(self, value: list[Gtk.Widget]) -> None:
        for i in self._overlays:
            self.remove_overlay(i)

        self._overlays = value

        for i in value:
            self.add_overlay(i)
