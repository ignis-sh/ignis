from gi.repository import Gtk  # type: ignore
from ignis.base_widget import BaseWidget
from .stack_page import StackPage
from ignis.gobject import IgnisProperty


class Stack(Gtk.Stack, BaseWidget):
    """
    Bases: :class:`Gtk.Stack`

    Stack is a container which only shows one of its children at a time.

    It does not provide a means for users to change the visible child.
    Instead, a separate widget such as :class:`~ignis.widgets.StackSwitcher` can be used with Stack to provide this functionality.

    Args:
        **kwargs: Properties to set.

    Overrided properties:
        - transition_type: The type of animation used to transition between pages. Available values: :class:`Gtk.StackTransitionType`.

    .. code-block:: python

        from ignis import widgets

        stack = widgets.Stack(
            child=[
                widgets.StackPage(
                    title="page 1", child=widgets.Label(label="welcome to page 1!")
                ),
                widgets.StackPage(
                    title="page 2", child=widgets.Label(label="welcome to page 2!")
                ),
                widgets.StackPage(
                    title="page 3", child=widgets.Label(label="welcome to page 3!")
                ),
            ]
        )

        widgets.Box(
            vertical=True,
            # you should add both StackSwitcher and Stack.
            child=[widgets.StackSwitcher(stack=stack), stack],
        )
    """

    __gtype_name__ = "IgnisStack"
    __gproperties__ = {**BaseWidget.gproperties}

    def __init__(self, **kwargs):
        Gtk.Stack.__init__(self)
        self.override_enum("transition_type", Gtk.StackTransitionType)
        self._child: list[StackPage] = []
        BaseWidget.__init__(self, **kwargs)

    @IgnisProperty
    def child(self) -> list[StackPage]:
        """
        A list of pages.
        """
        return self._child

    @child.setter
    def child(self, value: list[StackPage]) -> None:
        for i in self._child:
            self.remove(i.child)

        for i in value:
            self.add_titled(i.child, None, i.title)
