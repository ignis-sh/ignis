from gi.repository import Gtk  # type: ignore
from ignis.base_widget import BaseWidget
from collections.abc import Callable
from ignis.gobject import IgnisProperty


class SpinButton(Gtk.SpinButton, BaseWidget):  # type: ignore
    """
    Bases: :class:`Gtk.SpinButton`

    A widget that allows the user to increment or decrement the displayed value within a specified range.

    Args:
        **kwargs: Properties to set.

    .. code-block:: python

        widgets.SpinButton(
            min=0,
            max=100,
            step=1,
            value=50,
            on_change=lambda x, value: print(value)
        )
    """

    __gtype_name__ = "IgnisSpinButton"
    __gproperties__ = {**BaseWidget.gproperties}

    def __init__(self, min: int | None = None, max: int | None = None, **kwargs):
        Gtk.SpinButton.__init__(self)
        self._on_change: Callable | None = None
        self.adjustment = Gtk.Adjustment(
            value=0, lower=0, upper=100, step_increment=1, page_increment=0, page_size=0
        )
        self.min = min
        self.max = max
        BaseWidget.__init__(self, **kwargs)

        self.connect("value-changed", self.__invoke_on_change)

    @IgnisProperty
    def value(self) -> float:
        """
        The current value.
        """
        return super().get_value()

    @value.setter
    def value(self, value: float) -> None:
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
    def step(self) -> float:
        """
        Step increment.
        """
        return self.adjustment.props.step_increment

    @step.setter
    def step(self, value: float) -> None:
        self.adjustment.props.step_increment = value

    @IgnisProperty
    def on_change(self) -> Callable | None:
        """
        The function to call when the value changes.
        """
        return self._on_change

    @on_change.setter
    def on_change(self, value: Callable) -> None:
        self._on_change = value

    def __invoke_on_change(self, *args) -> None:
        if self.on_change:
            self.on_change(self, self.value)
