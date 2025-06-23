from gi.repository import Gtk, GObject  # type: ignore
from typing import Any
from collections.abc import Callable
from ignis.gobject import IgnisGObject, IgnisProperty
from ignis._deprecation import ignore_deprecation_warnings
from ignis.css_manager import (
    CssManager,
    StylePriority,
    _raise_css_parsing_error,
    GTK_STYLE_PRIORITIES,
)

css_manager = CssManager.get_default()


class BaseWidget(Gtk.Widget, IgnisGObject):
    """
    Bases: :class:`~ignis.gobject.IgnisGObject`.

    The base class for all widgets.
    Provides ``style`` property and allows overriding enums.
    """

    gproperties = __gproperties__ = {}  # type: ignore
    _overrided_enums: dict[str, GObject.GEnum] = {}

    def __init__(
        self,
        setup: Callable | None = None,
        style_priority: StylePriority | None = None,
        vexpand: bool = False,
        hexpand: bool = False,
        visible: bool = True,
        **kwargs,
    ):
        Gtk.Widget.__init__(self)

        self._style: str | None = None
        self._css_provider: Gtk.CssProvider | None = None
        self._style_priority: StylePriority = (
            css_manager.widgets_style_priority
            if style_priority is None
            else style_priority
        )

        self.vexpand = vexpand
        self.hexpand = hexpand
        self.visible = visible

        self.override_enum("halign", Gtk.Align)
        self.override_enum("valign", Gtk.Align)

        IgnisGObject.__init__(self, **kwargs)

        if setup:
            setup(self)

    @IgnisProperty
    def style(self) -> str | None:
        return self._style

    @style.setter
    def style(self, value: str) -> None:
        if self._css_provider:
            with ignore_deprecation_warnings():
                self.get_style_context().remove_provider(self._css_provider)

        if "{" not in value and "}" not in value:
            value = "* {" + value + "}"

        css_provider = Gtk.CssProvider()
        css_provider.connect("parsing-error", _raise_css_parsing_error)

        css_provider.load_from_string(value)

        with ignore_deprecation_warnings():
            self.get_style_context().add_provider(
                css_provider, GTK_STYLE_PRIORITIES[self._style_priority]
            )

        self._css_provider = css_provider
        self._style = value

    @IgnisProperty
    def style_priority(self) -> StylePriority:
        """
        The style priority for this widget.
        Overrides :attr:`~ignis.app.IgnisApp.widgets_style_priority`.

        More info about style priorities: :obj:`Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION`.

        .. warning::
            Changing this property won't affect an already applied style!

            .. code-block:: python

                some_widget = WIDGET_NAME(
                    style="some style",
                    style_priority="user"
                )
                some_widget.style_priority = "application"  # nothing change for current style
                some_widget.style = "new style"  # this style will have "application" priority
        """
        return self._style_priority

    @style_priority.setter
    def style_priority(self, value: StylePriority) -> None:
        self._style_priority = value

    def set_property(self, property_name: str, value: Any) -> None:
        """
        :meta private:
        """
        if property_name in self._overrided_enums:
            super().set_property(
                property_name,
                getattr(self._overrided_enums[property_name], value.upper()),
            )
        else:
            super().set_property(property_name, value)

    def get_property(self, property_name: str) -> Any:
        """
        :meta private:
        """
        if property_name in self._overrided_enums:
            return super().get_property(property_name).value_nick
        else:
            return super().get_property(property_name)

    def __setattr__(self, name: str, value: Any) -> None:
        if self.find_property(name):
            self.set_property(name, value)
        else:
            super().__setattr__(name, value)

    def __getattr__(self, name: str) -> Any:
        if self.find_property(name):
            return self.get_property(name)
        else:
            super().__getattribute__(name)

    def override_enum(self, property_name: str, enum: Any) -> None:
        """
        Override an enum.

        Args:
            property_name: The name of the property to override.
            enum(``GObject.GEnum``): An enum that accepts the property to be overridden. For example, for ``valign`` it will be ``Gtk.Align``.
        """
        self._overrided_enums[property_name] = enum
