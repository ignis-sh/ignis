from gi.repository import Gtk  # type: ignore
from ignis.base_widget import BaseWidget


class Calendar(Gtk.Calendar, BaseWidget):
    """
    Bases: :class:`Gtk.Calendar`

    A calendar.

    Args:
        **kwargs: Properties to set.

    .. code-block:: python

        widgets.Calendar(
            day=1,
            month=1,
            year=2024,
            no_month_change=False,
            show_day_names=True,
            show_details=True,
            show_heading=True,
            show_week_numbers=True
        )

    """

    __gtype_name__ = "IgnisCalendar"
    __gproperties__ = {**BaseWidget.gproperties}

    def __init__(self, **kwargs):
        Gtk.Calendar.__init__(self)
        BaseWidget.__init__(self, **kwargs)
