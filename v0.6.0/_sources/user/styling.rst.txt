Styling
========

GTK uses CSS for styling widgets. 
Additionally, Ignis provides convenient utilities to easily apply, remove, and reload CSS.

Sass/SCSS compilation is also supported.

CSS Manager
-----------

The main class for managing CSS is :class:`~ignis.css_manager.CssManager`.

It supports two types of sources:

- a string containing CSS
- a path to a CSS file

Applying from a file
^^^^^^^^^^^^^^^^^^^^

To apply CSS from a file, create a file named ``style.css`` next to your ``config.py``, and add the following to your configuration:

.. code-block:: python

    import os
    from ignis import utils
    from ignis.css_manager import CssManager, CssInfoPath

    css_manager = CssManager.get_default()

    css_manager.apply_css(
        CssInfoPath(
            name="main",
            # Adjust the path as needed
            path=os.path.join(utils.get_current_dir(), "style.css")
        )
    )

.. note::
    By default, CSS will be reapplied automatically when ``style.css`` or other CSS/Sass/SCSS files in the directory are modified.
    See :class:`~ignis.css_manager.CssInfoPath` for more information.

Applying from a string
^^^^^^^^^^^^^^^^^^^^^^

To apply CSS from a string, use :class:`~ignis.css_manager.CssInfoString`:

.. code-block:: python

    from ignis import utils
    from ignis.css_manager import CssManager, CssInfoString

    css_manager = CssManager.get_default()

    css_manager.apply_css(
        CssInfoString(
            name="main",
            string="* { background-color: red; }"
        )
    )

CSS classes
------------

You can assign CSS classes to any widgets and style them in the CSS file (or string).

To add CSS classes to a widget, use the ``css_classes`` property:

.. code-block:: python

    from ignis import widgets
    
    widgets.Label(
        label="hello",
        css_classes=["my-label"]
    )

In ``style.css`` (or an applied string):

.. code-block:: css

    .my-label {
        background-color: red;
    }

Sass/SCSS
---------

`Sass <https://sass-lang.com>`_ is an extension to CSS that adds many useful features and utilities.

You can use :attr:`CssInfoBase.compiler_function` to compile Sass/SCSS:

.. code-block:: python

    from ignis.css_manager import CssManager, CssInfoString, CssInfoPath
    from ignis import utils

    css_manager = CssManager.get_default()

    # From file
    css_manager.apply_css(
        CssInfoPath(
            name="main",
            path="PATH/TO/style.scss",
            compiler_function=lambda path: utils.sass_compile(path=path),
        )
    )

    # From string
    css_manager.apply_css(
        CssInfoString(
            name="some-name",
            string="some Sass/SCSS string",
            compiler_function=lambda string: utils.sass_compile(string=string),
        )
    )

The widget's ``style`` property
-------------------------------

You can style widgets directly without using CSS classes.

Use the ``style`` property to apply a CSS string specifically to a widget:

.. code-block:: python

    from ignis import widgets

    widgets.Label(
        label="hello",
        style="background-color: black;"
    )

.. tip::
    You can use :func:`~ignis.utils.sass_compile` to compile a Sass/SCSS string.

    .. code-block:: python

        from ignis import widgets
        from ignis import utils

        widgets.Label(
            label="hello",
            style=utils.sass_compile("some Sass/SCSS string")
        )