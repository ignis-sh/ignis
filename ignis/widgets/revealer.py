from gi.repository import Gtk  # type: ignore
from ignis.base_widget import BaseWidget


class Revealer(Gtk.Revealer, BaseWidget):
    """
    Bases: :class:`Gtk.Revealer`

    A container that animates the transition of its child from invisible to visible.

    Overrided properties:
        - transition_type: The type of transition. Default: ``slide_down``.

    Transition type:
        - none: No transition.
        - crossfade: Fade in.
        - slide_right: Slide in from the left.
        - slide_left: Slide in from the right.
        - slide_up: Slide in from the bottom.
        - slide_down: Slide in from the top.
        - swing_right: Floop in from the left
        - swing_left: Floop in from the right
        - swing_up: Floop in from the bottom
        - swing_down: Floop in from the top

    Args:
        **kwargs: Properties to set.

    .. code-block:: python

        widgets.Revealer(
            child=widgets.Label(label='animation!!!'),
            transition_type='slideright',
            transition_duration=500,
            reveal_child=True, # Whether child is revealed.
        )
    """

    __gtype_name__ = "IgnisRevealer"
    __gproperties__ = {**BaseWidget.gproperties}

    def __init__(self, **kwargs):
        Gtk.Revealer.__init__(self)
        self.override_enum("transition_type", Gtk.RevealerTransitionType)
        BaseWidget.__init__(self, **kwargs)

    def toggle(self):
        if self.get_reveal_child():
            self.set_reveal_child(False)
        else:
            self.set_reveal_child(True)
