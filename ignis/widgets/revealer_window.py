from .window import Window
from .revealer import Revealer
from ignis import utils
from typing import Any
from ignis.gobject import IgnisProperty


class RevealerWindow(Window):
    """
    Bases: :class:`~ignis.widgets.Window`

    A window with animation.

    Args:
        revealer: An instance of :class:`~ignis.widgets.Revealer`.
        **kwargs: Properties to set.

    .. warning::
        Do not set ``widgets.Revealer`` as a direct child,
        as this can lead to various graphical bugs.
        Instead, place `widgets.Revealer` inside a container (e.g., `widgets.Box`) and then set the container as a child.

    Example usage:

    .. code-block:: python

        from ignis import widgets

        revealer = widgets.Revealer(
            transition_type="slide_left",
            child=widgets.Button(label="test"),
            transition_duration=300,
            reveal_child=True,
        )

        box = widgets.Box(child=[revealer])

        widgets.RevealerWindow(
            visible=False,
            popup=True,
            layer="top",
            namespace="revealer-window",
            child=box,  # do not set widgets.Revealer as a direct child!
            revealer=revealer,
        )

    """

    def __init__(self, revealer: Revealer, **kwargs) -> None:
        self._revealer = revealer
        super().__init__(**kwargs)

    def set_property(self, prop_name: str, value: Any) -> None:
        if prop_name == "visible":
            if value:
                super().set_property(prop_name, value)
            else:
                utils.Timeout(
                    ms=self._revealer.transition_duration,
                    target=lambda x=super(): x.set_property(prop_name, value),
                )
            self._revealer.reveal_child = value
            self.notify("visible")
        else:
            super().set_property(prop_name, value)

    @IgnisProperty
    def visible(self) -> bool:
        return self._revealer.reveal_child

    @visible.setter
    def visible(self, value: bool) -> None:
        super().set_visible(value)

    @IgnisProperty
    def revealer(self) -> Revealer:
        """
        An instance of :class:`~ignis.widgets.Revealer`.
        """
        return self._revealer

    @revealer.setter
    def revealer(self, value: Revealer) -> None:
        self._revealer = value
