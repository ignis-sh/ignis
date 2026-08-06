from gi.repository import Gtk  # type: ignore

from ignis.base_widget import BaseWidget


class LevelBar(Gtk.LevelBar, BaseWidget):
    """
    Bases: :class:`Gtk.LevelBar`

    An non-interactable progress/level bar.

    Overrided properties:
        - mode: The pattern with how the bar is rendered.  Default: ``continuous``

    Mode:
        - continuous: The value bar will be one single bar
        - discrete: The value bar will be broken into discrete chunks when rendered

    Args:
        **kwargs: Properties to set.

    .. code-block:: python

        widgets.LevelBar(
            max_value=100,
            mode="continuous",
            value=75,
        )
    """

    __gtype_name__ = "IgnisLevelBar"
    __gproperties__ = {**BaseWidget.gproperties}

    def __init__(self, **kwargs):
        Gtk.LevelBar.__init__(self)
        self.override_enum("mode", Gtk.LevelBarMode)
        BaseWidget.__init__(self, **kwargs)
