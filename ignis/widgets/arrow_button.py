from ignis.widgets.button import Button
from ignis.widgets.arrow import Arrow
from ignis.gobject import IgnisProperty


class ArrowButton(Button):
    """
    Bases: :class:`~ignis.widgets.button.Button`

    A simple button with an arrow. On click, it will toggle (rotate) the arrow.

    Args:
        arrow: An instance of an arrow.
        **kwargs: Properties to set.

    .. code-block:: python

        widgets.ArrowButton(
            arrow=widgets.Arrow(
                ... # Arrow-specific properties go here
            )
        )
    """

    __gtype_name__ = "IgnisArrowButton"

    def __init__(self, arrow: Arrow, **kwargs):
        self._arrow = arrow

        super().__init__(child=self._arrow, **kwargs)
        self.connect("clicked", lambda x: self._arrow.toggle())

    @IgnisProperty
    def arrow(self) -> Arrow:
        """
        An instance of an arrow.
        """
        return self._arrow

    def toggle(self) -> None:
        """
        Same as :func:`~ignis.widgets.Arrow.toggle`
        """
        self._arrow.toggle()
