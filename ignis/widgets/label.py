from gi.repository import Gtk, Pango  # type: ignore
from ignis.base_widget import BaseWidget


class Label(Gtk.Label, BaseWidget):
    """
    Bases: :class:`Gtk.Label`

    A widget that displays a small amount of text.

    Overrided properties:
        - justify: The alignment of the lines in the text of the label relative to each other. This does NOT affect the alignment of the label within its allocation.
        - ellipsize: The preferred place to ellipsize the string. Default: ``none``.
        - wrap_mode: If ``wrap`` is set to ``True``, controls how linewrapping is done. Default: ``word``.

    Justify:
        - left: The text is placed at the left edge of the label.
        - right: The text is placed at the right edge of the label.
        - center: The text is placed in the center of the label.
        - fill: The text is placed is distributed across the label.

    Ellipsize:
        - none: No ellipsization.
        - start: Omit characters at the start of the text.
        - middle: Omit characters in the middle of the text.
        - end: Omit characters at the end of the text.

    Wrap mode:
        - word: Wrap lines at word boundaries.
        - char: Wrap lines at character boundaries.
        - word_char: Wrap lines at word boundaries, but fall back to character boundaries if there is not enough space for a full word.

    Args:
        **kwargs: Properties to set.

    .. code-block:: python

        widgets.Label(
            label='heh',
            use_markup=False,
            justify='left',
            wrap=True,
            wrap_mode='word',
            ellipsize='end',
            max_width_chars=52
        )
    """

    __gtype_name__ = "IgnisLabel"
    __gproperties__ = {**BaseWidget.gproperties}

    def __init__(self, **kwargs):
        Gtk.Label.__init__(self)
        self.override_enum("justify", Gtk.Justification)
        self.override_enum("wrap_mode", Pango.WrapMode)
        self.override_enum("ellipsize", Pango.EllipsizeMode)
        BaseWidget.__init__(self, **kwargs)
