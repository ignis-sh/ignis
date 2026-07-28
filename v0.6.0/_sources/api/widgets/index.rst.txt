Widgets
==========

To access widgets, use the ``ignis.widgets`` package.

.. code-block:: python

   from ignis import widgets

   widgets.WIDGET_NAME()

Enums
----------------
GTK widgets use enums, which looks similar like this: ``Gtk.Align.START``.
Having to import Gtk and constantly write out the full enum name can be inconvenient.
Therefore, some widgets override their properties to allow using simple Python strings instead of enums.
For example, the ``valign`` property uses the ``Gtk.Align`` enum, 
but you can now pass a string with the actual value of the enum: ``"start"``, ``"center"``, ``"end"``, etc.

.. note::
   Overridden properties do not support enums.
   For example, you cannot pass an enum to the ``valign`` property.

The ``setup`` property
------------------------
You can pass a callback function to the widget costructor as the ``setup`` property.
The widget will be passed to the callback function as an argument.
This can be useful when you need to perform actions when the widget is initialized (for example, connect to signal).

.. code-block:: python

   from ignis import widgets

   widgets.Label(
      label="you will not see this text", 
      setup=lambda self: self.set_label("instead, you will see this")
   )

Common widget properties
-------------------------

+----------------+------------------------------------+---------------------------------------------------------------------------------------+
| Name           | Type                               | Description                                                                           |
+================+====================================+=======================================================================================+
| css_classes    | :py:class:`list`\[:py:class:`str`] | List of css classes.                                                                  |
+----------------+------------------------------------+---------------------------------------------------------------------------------------+
| valign         | :py:class:`str`                    | Vertical alignment. Default: ``"fill"``.                                              |
+----------------+------------------------------------+---------------------------------------------------------------------------------------+
| halign         | :py:class:`str`                    | Horizontal alignment. Default: ``"fill"``.                                            |
+----------------+------------------------------------+---------------------------------------------------------------------------------------+
| hexpand        | :py:class:`bool`                   | Whether the widget would like any available extra horizontal space.                   |
+----------------+------------------------------------+---------------------------------------------------------------------------------------+
| vexpand        | :py:class:`bool`                   | Whether the widget would like any available extra vertical space.                     |
+----------------+------------------------------------+---------------------------------------------------------------------------------------+
| tooltip_text   | :py:class:`str`                    | Tooltip text. Text that will be shown when the user hovers the mouse over the widget. |
+----------------+------------------------------------+---------------------------------------------------------------------------------------+
| sensitive      | :py:class:`bool`                   | Whether the widget responds to input.                                                 |
+----------------+------------------------------------+---------------------------------------------------------------------------------------+
| visible        | :py:class:`bool`                   | Whether the widget is visible.                                                        |
+----------------+------------------------------------+---------------------------------------------------------------------------------------+
| width_request  | :py:class:`int`                    | Minimum width of the widget.                                                          |
+----------------+------------------------------------+---------------------------------------------------------------------------------------+
| height_request | :py:class:`int`                    | Minimum height of the widget.                                                         |
+----------------+------------------------------------+---------------------------------------------------------------------------------------+
| style          | :py:class:`str`                    | Inline CSS style that will be applied to this widget.                                 |
+----------------+------------------------------------+---------------------------------------------------------------------------------------+

**Alignment:**
   - **"start"** : Snap to left or top side, leaving space on right or bottom.
   - **"center"** : Center natural width of widget inside the allocation.
   - **"end"** : Snap to right or bottom side, leaving space on left or top.
   - **"fill"** : Stretch to fill all space if possible, center if no meaningful way to stretch.
   - **"baseline"** : Align the widget according to the baseline.
   - **"baseline_center"** : Stretch to fill all space, but align the baseline.

Built-in widgets
--------------------

Here is a list of built-in widgets.

.. warning::
   The widget pages only describe the properties that Ignis adds.
   For more information about widget, each page contains a corresponding link to the widget in the PyGObject API reference.

.. hint::
   If the widget you need is not here, you can use it directly from GTK. 
   Please note that it will not support ``style`` property, bindings, and other Ignis features.
   Or, you can manually subclass it, see `Subclassing widgets <../../dev/subclassing_widgets.html>`_ for more info.


.. toctree:: 
   :glob:
   :maxdepth: 1

   ./*