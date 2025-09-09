from gi.repository import Gtk  # type: ignore
from ignis.base_widget import BaseWidget
from collections.abc import Callable
from ignis.gobject import IgnisProperty


class DropDown(Gtk.DropDown, BaseWidget):
    """
    Bases: :class:`Gtk.DropDown`

    A widget that allows the user to choose an item from a list of options.

    Args:
        **kwargs: Properties to set.

    .. code-block:: python

        widgets.DropDown(
            items=["option 1", "option 2", "option 3"],
            on_selected=lambda x, selected: print(selected)
        )
    """

    __gtype_name__ = "IgnisDropDown"
    __gproperties__ = {**BaseWidget.gproperties}

    def __init__(self, **kwargs):
        Gtk.DropDown.__init__(self)
        self._items: list[str] = []
        self._on_selected: Callable | None = None
        BaseWidget.__init__(self, **kwargs)

        self.connect("notify::selected-item", self.__invoke_on_selected)

    @IgnisProperty
    def items(self) -> list[str]:
        """
        A list of strings that can be selected in the popover.
        """
        return self._items

    @items.setter
    def items(self, value: list[str]) -> None:
        self._items = value
        model = Gtk.StringList()
        for i in value:
            model.append(i)

        self.model = model

    @IgnisProperty
    def on_selected(self) -> Callable | None:
        """
        The function to call when the user selects an item from the list.
        """
        return self._on_selected

    @on_selected.setter
    def on_selected(self, value: Callable) -> None:
        self._on_selected = value

    def __invoke_on_selected(self, *args) -> None:
        if self.on_selected:
            self.on_selected(self, self.selected)

    @IgnisProperty
    def selected(self) -> str:
        """
        The selected string. It is a shortcut for ``self.selected_item.props.string``.
        """
        return self.selected_item.props.string
