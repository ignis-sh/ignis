from gi.repository import Gtk, Gdk  # type: ignore
from ignis.base_widget import BaseWidget
from collections.abc import Callable
from ignis.gobject import IgnisProperty


class Scale(Gtk.Scale, BaseWidget):
    """
    Bases: :class:`Gtk.Scale`

    A slider widget.

    Overrided properties:
        - value_pos: Position where the current value is displayed. Works only if ``draw_value`` is set to ``True``. Default: ``top``.

    Value position:
        - left
        - right
        - top
        - bottom

    Args:
        **kwargs: Properties to set.

    .. code-block:: python

        widgets.Scale(
            vertical=False,
            min=0,
            max=100,
            step=1,
            value=20,
            on_change=lambda x: print(x.value),
            on_release=lambda x: print(x.value),
            draw_value=True,
            value_pos='top'
        )
    """

    __gtype_name__ = "IgnisScale"
    __gproperties__ = {**BaseWidget.gproperties}

    def __init__(self, **kwargs):
        Gtk.Scale.__init__(self)
        self.adjustment = Gtk.Adjustment(
            value=0, lower=0, upper=100, step_increment=1, page_increment=0, page_size=0
        )
        self._dragging: bool = False
        self._on_change: Callable | None = None
        self._on_release: Callable | None = None
        self.override_enum("value_pos", Gtk.PositionType)
        BaseWidget.__init__(self, **kwargs)

        self.connect("value-changed", lambda x: self.__invoke_on_change())

        legacy_controller = (
            Gtk.EventControllerLegacy()
        )  # Gtk.GestureClick() don't emit released signal on scale
        self.add_controller(legacy_controller)
        legacy_controller.connect("event", self.__on_button_event)

        key_controller = Gtk.EventControllerKey()
        self.add_controller(key_controller)
        key_controller.connect("key-pressed", self.__on_key_press)
        key_controller.connect("key-released", self.__on_key_release)

        scroll_controller = Gtk.EventControllerScroll.new(
            Gtk.EventControllerScrollFlags.BOTH_AXES
        )
        self.add_controller(scroll_controller)
        scroll_controller.connect("scroll", self.__on_scroll)

    @IgnisProperty
    def value(self) -> float:
        """
        The current value.
        """
        return super().get_value()

    @value.setter
    def value(self, value: float) -> None:
        if value is None:
            return

        if not self._dragging:
            self.adjustment.set_value(value)

    @IgnisProperty
    def min(self) -> float:
        """
        Minimum value.
        """
        return self.adjustment.props.lower

    @min.setter
    def min(self, value: float) -> None:
        self.adjustment.props.lower = value

    @IgnisProperty
    def max(self) -> float:
        """
        Maximum value.
        """
        return self.adjustment.props.upper

    @max.setter
    def max(self, value: float) -> None:
        self.adjustment.props.upper = value

    @IgnisProperty
    def on_change(self) -> Callable:
        """
        The function to call when the value changes.
        """
        return self._on_change

    @on_change.setter
    def on_change(self, value: Callable) -> None:
        self._on_change = value

    @IgnisProperty
    def on_release(self) -> Callable:
        """
        The function to call when any user action ends.
        """
        return self._on_release

    @on_release.setter
    def on_release(self, value: Callable) -> None:
        self._on_release = value

    @IgnisProperty
    def step(self) -> float:
        """
        Step increment.
        """
        return self.adjustment.props.step_increment

    @step.setter
    def step(self, value: float) -> None:
        self.adjustment.props.step_increment = value

    @IgnisProperty
    def vertical(self) -> bool:
        """
        Whether the scale is vertical.
        """
        return self.get_orientation() == Gtk.Orientation.VERTICAL

    @vertical.setter
    def vertical(self, value: bool) -> None:
        if value:
            self.set_property("orientation", Gtk.Orientation.VERTICAL)
        else:
            self.set_property("orientation", Gtk.Orientation.HORIZONTAL)

    def __invoke_on_release(self):
        if self.on_release:
            self.on_release(self)

    def __invoke_on_change(self):
        if self._dragging and self.on_change:
            self.on_change(self)

    def __on_button_event(self, controller: Gtk.EventControllerLegacy, *args):
        event = controller.get_current_event()
        if not event:
            return

        match event.get_event_type():
            case Gdk.EventType.BUTTON_PRESS | Gdk.EventType.TOUCH_BEGIN:
                self._dragging = True
            case Gdk.EventType.BUTTON_RELEASE | Gdk.EventType.TOUCH_END:
                self._dragging = False
                self.__invoke_on_release()

    def __on_key_press(self, *args):
        self._dragging = True

    def __on_key_release(self, *args):
        self._dragging = False
        self.__invoke_on_release()

    def __on_scroll(
        self, event_controller: Gtk.EventControllerScroll, dx: float, dy: float
    ):
        self._dragging = True
        if dy > 0:
            super().set_value(self.value - self.step)
        else:
            super().set_value(self.value + self.step)

        self._dragging = False
        self.__invoke_on_release()
