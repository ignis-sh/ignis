Subclassing Widgets
=======================

All widgets should inherit from the :class:`~ignis.base_widget.BaseWidget` class.

Widget Class Template
-----------------------

Here is the template for the widget that you want to override.
Replace ``WIDGET_NAME`` with the actual name of the widget.

.. code-block:: python

    from gi.repository import Gtk
    from ignis.base_widget import BaseWidget
    from ignis.gobject import IgnisProperty


    class WIDGET_NAME(Gtk.WIDGET_NAME, BaseWidget):
        __gtype_name__ = "IgnisWIDGET_NAME"
        __gproperties__ = {**BaseWidget.gproperties}  # this need to inherit properties from BaseWidget

        def __init__(self, **kwargs):  # accept keyword arguments
            Gtk.Label.__init__(self)
            # if you want to override enums, do it BEFORE BaseWidget.__init__(self, **kwargs)
            # otherwise, the property will be set before it is overridden.
            self.override_enum("SOME_PROPERTY", SOME_ENUM)
            self._custom_property = None  # define protected/private variables for your custom properties BEFORE BaseWidget.__init__(self, **kwargs)
            BaseWidget.__init__(self, **kwargs)  # this sets all properties transferred to kwargs

        @IgnisProperty
        def custom_property(self) -> bool:
            return self._custom_property

        @custom_property.setter
        def custom_property(self, value: bool) -> None:
            self._custom_property = value
