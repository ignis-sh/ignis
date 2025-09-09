from gi.repository import Gtk  # type: ignore
from ignis.base_widget import BaseWidget
from typing import Any
from collections.abc import Callable
from ignis.gobject import IgnisProperty


class Switch(Gtk.Switch, BaseWidget):
    """
    Bases: :class:`Gtk.Switch`

    A switch widget.

    Args:
        **kwargs: Properties to set.

    .. code-block:: python

        widgets.Switch(
            active=True,
            on_change=lambda x, active: print(active),
        )
    """

    __gtype_name__ = "IgnisSwitch"
    __gproperties__ = {**BaseWidget.gproperties}

    def __init__(self, **kwargs):
        Gtk.Switch.__init__(self)
        self._on_change: Callable | None = None
        self._can_activate: bool = True
        BaseWidget.__init__(self, **kwargs)

        self.connect("state-set", self.__invoke_on_change)

    @IgnisProperty
    def on_change(self) -> Callable | None:
        """
        The function to call when the position of the switch changes (e.g., when the user toggles the switch).
        """
        return self._on_change

    @on_change.setter
    def on_change(self, value: Callable) -> None:
        self._on_change = value

    def __invoke_on_change(self, *args) -> None:
        if self._can_activate and self.on_change:
            self.on_change(self, self.active)

    def set_property(self, property_name: str, value: Any) -> None:
        if property_name == "active":
            self._can_activate = False
            super().set_property(property_name, value)
            self._can_activate = True
        else:
            super().set_property(property_name, value)
