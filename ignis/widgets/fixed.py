from dataclasses import dataclass

from gi.repository import Gtk
from ignis.base_widget import BaseWidget
from ignis.gobject import IgnisProperty


@dataclass
class FixedChild:
    """
    A data class representing a child widget positioned in a Fixed container.

    Args:
        widget: The GTK widget to be positioned.
        x: The horizontal position (x-coordinate) in pixels.
        y: The vertical position (y-coordinate) in pixels.
    """

    widget: Gtk.Widget
    x: int
    y: int


class Fixed(Gtk.Fixed, BaseWidget):
    """
    Bases: :class:`Gtk.Fixed`

    A fixed container widget that allows positioning child widgets at specific coordinates.
    Unlike other container widgets that use automatic layout, Fixed positions children
    manually using absolute coordinates.

    Args:
        child: A list of FixedChild objects for positioned children.
        **kwargs: Properties to set.

    .. code-block:: python

        Fixed(
            child=[
                FixedChild(widget=Label(label="Top Left"), x=10, y=10),
                FixedChild(widget=Button(label="Center"), x=100, y=50),
                FixedChild(widget=Icon(image="settings"), x=200, y=200)
            ],
        )
    """

    __gtype_name__ = "IgnisFixed"
    __gproperties__ = {**BaseWidget.gproperties}

    def __init__(
        self,
        **kwargs,
    ):
        Gtk.Fixed.__init__(self)  # type: ignore
        self._child = []
        BaseWidget.__init__(
            self,
            **kwargs,
        )

    @IgnisProperty
    def child(self) -> list[FixedChild]:
        """The list of child widgets with their positions."""
        return self._child

    @child.setter
    def child(self, value: list[FixedChild] | None) -> None:
        for child_item in self._child:
            self.remove(child_item.widget)

        self._child = value or []
        for child_item in self._child:
            self.put(child_item.widget, child_item.x, child_item.y)
