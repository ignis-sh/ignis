from ignis.gobject import IgnisGObject, IgnisProperty
from gi.repository import Gio  # type: ignore
from collections.abc import Callable
from ignis.app import IgnisApp
from typing import TypeAlias


ItemsType: TypeAlias = "list[IgnisMenuItem | IgnisMenuModel | IgnisMenuSeparator]"


class IgnisMenuItem(IgnisGObject):
    """
    A menu item.

    Args:
        label: The label of item.
        enabled: Whether the item is enabled. If ``False``, the item cannot be selected.
        on_activate: The function to call when the user clicks on the item.
    """

    def __init__(
        self,
        label: str,
        enabled: bool = True,
        on_activate: Callable | None = None,
    ):
        super().__init__()
        self._label = label
        self._enabled = enabled
        self._on_activate = on_activate
        self._uniq_name = hex(id(self))

        self._action = Gio.SimpleAction.new(self._uniq_name, None)
        self._action.set_enabled(enabled)
        self._activate_id = self._action.connect("activate", self.__on_activate)

        IgnisApp.get_initialized().add_action(self._action)

    @IgnisProperty
    def label(self) -> str:
        """
        The label of item.
        """
        return self._label

    @IgnisProperty
    def uniq_name(self) -> str:
        """
        The unique name of the ``Gio.Action``.
        """
        return self._uniq_name

    @IgnisProperty
    def action_name(self) -> str:
        """
        The full action name (``app.UNIQ_NAME``).
        """
        return f"app.{self.uniq_name}"

    @IgnisProperty
    def enabled(self) -> bool:
        """
        Whether the item is enabled. If ``False``, the item cannot be selected.
        """
        return self._enabled

    @IgnisProperty
    def on_activate(self) -> Callable:
        """
        The function to call when the user clicks on the item.
        """
        return self._on_activate

    @on_activate.setter
    def on_activate(self, value: Callable) -> None:
        self._on_activate = value

    def __on_activate(self, *args) -> None:
        if self.on_activate:
            self.on_activate(self)

    def _destroy(self) -> None:
        IgnisApp.get_initialized().remove_action(self._uniq_name)
        self._action.disconnect(self._activate_id)
        self._action = None  # type: ignore


class IgnisMenuSeparator:
    """
    A simple object representing a menu separator.
    """


class IgnisMenuModel(IgnisGObject):
    """
    A helper class that provides a convenient way to construct a :class:`Gio.Menu`.

    Args:
        *args: Items to add.
        label: The label of the submenu. Only works if this model passed as an item of the parent model. Must be provided only as a **keyword** argument.

    .. code-block:: python

        from ignis.menu_model import IgnisMenuModel, IgnisMenuItem, IgnisMenuSeparator

        model = IgnisMenuModel(
            IgnisMenuItem(
                label="Item 1",
                on_activate=lambda x: print("item 1 activated!"),
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
        )

        # Access built Gio.Menu
        print(model.gmenu)
    """

    def __init__(
        self,
        *args: "IgnisMenuItem | IgnisMenuModel | IgnisMenuSeparator",
        label: str | None = None,
    ):
        super().__init__()
        self._gmenu: Gio.Menu | None = None
        self._items: ItemsType = []
        self._links: list[Gio.MenuItem] = []

        self._label = label
        self.items = list(args)

    @IgnisProperty
    def items(self) -> ItemsType:
        """
        A list of items.
        """
        return self._items

    @items.setter
    def items(self, value: ItemsType) -> None:
        self._items = value
        self.__generate_gmenu(value)

    @IgnisProperty
    def gmenu(self) -> "Gio.Menu | None":
        """
        The `Gio.Menu` built from the contents of :attr:`items`, or ``None`` if no items are present.
        """
        return self._gmenu

    @IgnisProperty
    def label(self) -> str | None:
        """
        The label of the submenu. Only Works if this model passed as an item of the parent model.
        """
        return self._label

    def __add_section(self, root_menu: Gio.Menu) -> Gio.Menu:
        current_section = Gio.Menu()
        gitem = Gio.MenuItem.new_section(None, current_section)
        root_menu.append_item(gitem)
        self._links.append(gitem)

        return current_section

    def __add_item(self, current_section: Gio.Menu, item: IgnisMenuItem) -> None:
        gitem = Gio.MenuItem.new(item.label, item.action_name)
        current_section.append_item(gitem)

    def __add_submenu(
        self, current_section: Gio.Menu, submenu: "IgnisMenuModel"
    ) -> None:
        gitem = Gio.MenuItem.new_submenu(submenu.label, submenu.gmenu)
        current_section.append_item(gitem)
        self._links.append(gitem)

    def __generate_gmenu(self, items: ItemsType) -> None:
        root_menu = Gio.Menu()
        current_section = self.__add_section(root_menu)

        for item in items:
            if isinstance(item, IgnisMenuItem):
                self.__add_item(current_section, item)

            elif isinstance(item, IgnisMenuModel):
                self.__add_submenu(current_section, item)

            elif isinstance(item, IgnisMenuSeparator):
                current_section = self.__add_section(root_menu)

        self._gmenu = root_menu
        self.notify("gmenu")

    def clean_gmenu(self) -> None:
        """
        Clean :attr:`gmenu`. This will gracefully destroy it, avoiding a memory leak.
        """
        for item in self._items:
            if isinstance(item, IgnisMenuItem):
                item._destroy()

            elif isinstance(item, IgnisMenuModel):
                item.clean_gmenu()

        self._items.clear()

        for menu_item in self._links:
            for link in (Gio.MENU_LINK_SECTION, Gio.MENU_LINK_SUBMENU):
                menu: Gio.Menu | None = menu_item.get_link(link)  # type: ignore
                if menu:
                    menu_item.set_link(link)  # remove Gio.Memu links from Gio.MenuItem
                    menu.remove_all()  # remove menu items from linked Gio.Menu

        self._links.clear()

        if self._gmenu:
            self._gmenu.remove_all()

        self._gmenu = None

        self.notify("items")
        self.notify("gmenu")
