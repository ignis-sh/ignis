from gi.repository import Gtk  # type: ignore
from ignis.base_widget import BaseWidget
from collections.abc import Callable
from ignis.gobject import IgnisProperty


class Button(Gtk.Button, BaseWidget):
    """
    Bases: :class:`Gtk.Button`

    A button.

    Args:
        **kwargs: Properties to set.

    .. code-block:: python

        widgets.Button(
            child=widgets.Label(label="button"),
            on_click=lambda self: print(self),
            on_right_click=lambda self: print(self),
            on_middle_click=lambda self: print(self),
        )
    """

    __gtype_name__ = "IgnisButton"
    __gproperties__ = {**BaseWidget.gproperties}

    def __init__(self, **kwargs):
        Gtk.Button.__init__(self)
        self._on_click: Callable | None = None
        self._on_right_click: Callable | None = None
        self._on_middle_click: Callable | None = None

        self.__right_click_controller: Gtk.GestureClick | None = None
        self.__middle_click_controller: Gtk.GestureClick | None = None

        BaseWidget.__init__(self, **kwargs)
        self.connect("clicked", lambda x: self.on_click(x) if self.on_click else None)

    def __init_controller(self, button: int, callback: Callable) -> Gtk.GestureClick:
        def on_pressed(gesture_click: Gtk.GestureClick, n_press, x, y) -> None:
            gesture_click.set_state(Gtk.EventSequenceState.CLAIMED)
            callback(self)

        controller = Gtk.GestureClick()
        controller.set_button(button)
        self.add_controller(controller)
        controller.connect("pressed", on_pressed)
        return controller

    @IgnisProperty
    def on_click(self) -> Callable | None:
        """
        The function to call on left click.
        """

        return self._on_click

    @on_click.setter
    def on_click(self, value: Callable) -> None:
        self._on_click = value

    @IgnisProperty
    def on_right_click(self) -> Callable:
        """
        The function to call on right click.
        """

        return self._on_right_click

    @on_right_click.setter
    def on_right_click(self, value: Callable) -> None:
        self._on_right_click = value
        if not self.__right_click_controller:
            self.__right_click_controller = self.__init_controller(
                3,
                lambda *args, **kwargs: self.on_right_click(*args, **kwargs),
            )

    @IgnisProperty
    def on_middle_click(self) -> Callable:
        """
        The function to call on middle click.
        """

        return self._on_middle_click

    @on_middle_click.setter
    def on_middle_click(self, value: Callable) -> None:
        self._on_middle_click = value
        if not self.__middle_click_controller:
            self.__middle_click_controller = self.__init_controller(
                2,
                lambda *args, **kwargs: self.on_middle_click(*args, **kwargs),
            )
