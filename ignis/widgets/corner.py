import cairo
from typing import Literal
from gi.repository import Gtk  # type: ignore
from ignis.base_widget import BaseWidget
from ignis.gobject import IgnisProperty

Orientation = Literal["top-left", "top-right", "bottom-left", "bottom-right"]


class Corner(Gtk.DrawingArea, BaseWidget):
    """
    Bases: :class:`Gtk.DrawingArea`

    A corner widget that renders rounded corners.
    Useful in bars and panels.

    Args:
        **kwargs: Properties to set.

    .. code-block:: python

        from ignis import widgets

        widgets.Corner(
            orientation="top-left",
            # It's mandatory to explicitly set the width and the height
            # Otherwise, the widget will be invisible
            # Alternativly, you can set them in CSS using `min-width` and `min-height` properties
            width_request=30,
            height_request=30,
        )
    """

    __gtype_name__ = "IgnisCorner"
    __gproperties__ = {**BaseWidget.gproperties}

    def __init__(self, **kwargs):
        Gtk.DrawingArea.__init__(self)
        self._orientation: Orientation = "top-left"
        BaseWidget.__init__(self, **kwargs)

        self.set_draw_func(self.__on_draw)

    @IgnisProperty
    def orientation(self) -> Orientation:
        """
        The corner orientation.

        Orientation:
            - top-left
            - top-right
            - bottom-left
            - bottom-right

        Default: ``top-left``
        """
        return self._orientation

    @orientation.setter
    def orientation(self, value: Orientation) -> None:
        self._orientation = value
        self.queue_draw()

    def __on_draw(
        self,
        drawing_area: Gtk.DrawingArea,
        cr: cairo.Context,
        width: int,
        height: int,
        *_,
    ) -> None:
        cr.save()

        match self._orientation:
            case "top-left":
                cr.move_to(0, height)
                cr.line_to(0, 0)
                cr.line_to(width, 0)
                cr.curve_to(0, 0, 0, height, 0, height)
            case "top-right":
                cr.move_to(width, height)
                cr.line_to(width, 0)
                cr.line_to(0, 0)
                cr.curve_to(width, 0, width, height, width, height)
            case "bottom-left":
                cr.move_to(0, 0)
                cr.line_to(0, height)
                cr.line_to(width, height)
                cr.curve_to(0, height, 0, 0, 0, 0)
            case "bottom-right":
                cr.move_to(width, 0)
                cr.line_to(width, height)
                cr.line_to(0, height)
                cr.curve_to(width, height, width, 0, width, 0)

        cr.close_path()
        cr.clip()

        if color := self.get_color():
            cr.set_source_rgba(color.red, color.green, color.blue, color.alpha)

        cr.paint()
        cr.restore()
