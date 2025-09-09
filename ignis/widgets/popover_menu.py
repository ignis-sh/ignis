from gi.repository import Gtk  # type: ignore
from ignis.base_widget import BaseWidget
from ignis.gobject import IgnisProperty
from ignis.menu_model import IgnisMenuModel


class PopoverMenu(Gtk.PopoverMenu, BaseWidget):
    """
    Bases: :class:`Gtk.PopoverMenu`

    A dropdown menu.
    It must be added as a child to a container.
    To display it, call the ``popup()`` method.

    .. note::
        The Popover Menu points to the widget to which it was added.

    Args:
        **kwargs: Properties to set.

    .. code-block:: python

        from ignis.menu_model import IgnisMenuModel, IgnisMenuItem, IgnisMenuSeparator

        widgets.PopoverMenu(
            model=IgnisMenuModel(
                IgnisMenuItem(
                    label="Just item",
                    on_activate=lambda x: print("item activated!"),
                ),
                IgnisMenuItem(
                    label="This is disabled item",
                    enabled=False,
                    on_activate=lambda x: print(
                        "you will not see this message in terminal hehehehehe"
                    ),
                ),
                IgnisMenuModel(
                    *(  # unpacking because items must be passed as *args
                        IgnisMenuItem(
                            label=str(i),
                            on_activate=lambda x, i=i: print(f"Clicked on item {i}!"),
                        )
                        for i in range(10)
                    ),
                    label="Submenu",  # pass label as keyword argument
                ),
            ),
        )
    """

    __gtype_name__ = "IgnisPopoverMenu"
    __gproperties__ = {**BaseWidget.gproperties}

    def __init__(self, **kwargs):
        Gtk.PopoverMenu.__init__(self)
        self._model: IgnisMenuModel | None = None
        BaseWidget.__init__(self, visible=False, **kwargs)

    @IgnisProperty
    def model(self) -> IgnisMenuModel | None:
        """
        A menu model.
        """
        return self._model

    @model.setter
    def model(self, value: IgnisMenuModel) -> None:
        if self._model:
            self._model.clean_gmenu()

        self._model = value
        self.set_menu_model(value.gmenu)

    def __del__(self) -> None:
        if self._model:
            self._model.clean_gmenu()
            self._model = None
