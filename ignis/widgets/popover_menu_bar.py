from gi.repository import Gtk  # type: ignore
from ignis.base_widget import BaseWidget
from ignis.gobject import IgnisProperty
from ignis.menu_model import IgnisMenuModel


class PopoverMenuBar(Gtk.PopoverMenuBar, BaseWidget):
    """
    Bases: :class:`Gtk.PopoverMenuBar`

    A dropdown menu bar.

    Args:
        **kwargs: Properties to set.
    
    .. code-block:: python

        from ignis.menu_model import IgnisMenuModel, IgnisMenuItem, IgnisMenuSeparator

        widgets.PopoverMenuBar(
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

    __gtype_name__ = "IgnisPopoverMenuBar"
    __gproperties__ = {**BaseWidget.gproperties}

    def __init__(self, **kwargs):
        Gtk.PopoverMenuBar.__init__(self)
        self._model: IgnisMenuModel | None = None
        BaseWidget.__init__(self, **kwargs)

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
