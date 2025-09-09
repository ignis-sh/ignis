Documentation Guidelines
========================

Ignis uses the `Sphinx <https://www.sphinx-doc.org/en/master/>`_ documentation generator
with the `autodoc <https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html>`_ 
extension to generate documentation from Python docstrings.

.. hint::
    Sphinx uses the reStructuredText markup language.
    Here are some useful resources to learn more about it:

    - `reStructuredText guide by Sphinx <https://www.sphinx-doc.org/en/master/usage/restructuredtext/index.html>`_
    - `Example Google Style Python Docstrings <https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html>`_

Docstrings
-------------
Use the Google style for Python docstrings, with types included in them.
Here are some examples for functions and classes.

Functions
~~~~~~~~~~~~~~~~
For functions, use the standard Google docstring style.
Type hints will be added automatically.

.. code-block:: python

    def some_func(arg1: int, arg2: str) -> str:
        """
        Description of the function.

        Args:
            arg1: Description...
            arg2: Description 2...

        Returns:
            The description of the return value...
        
        Raises:
            SomeException: If this condition is true...
        """
        pass

General Classes
~~~~~~~~~~~~~~~~

- For classes that the user can initialize manually, explicitly define the constructor arguments in the `Args` section.

- Signals:

    If a class has custom signals, add docstrings to the functions decorated with ``@IgnisSignal`` respectively.

    Also, if the signal have custom arguments, define them in the ``Args`` section.

- Properties:

    If a class has custom properties, add docstrings to the functions decorated with ``@GObject.Object`` or ``@property`` respectively.

- If possible, please provide a code example.

.. code-block:: python

    from ignis.gobject import IgnisProperty, IgnisSignal

    class SomeClass:
        """
        This is an example docstring for a class.
        Further info goes here...
        """

    @IgnisSignal
    def some_signal(self):
        """
        Emitted when the something happens.
        """

    @IgnisSignal
    def arg_signal(self, some_arg: int):
        """
        Emitted when the something another happens.

        Args:
            some_arg: Description of the argument...
        """

    @IgnisProperty
    def some_prop(self) -> int:
        """
        The description of some_prop.
        """
        ...

    @IgnisProperty
    def rw_prop(self) -> str:
        """
        The description of rw_prop.
        """
        ...

    @rw_prop.setter
    def rw_prop(self, value: str) -> None:
        ...

.. code-block:: python
    
    class AnotherClass:
        """
        Description of the class...

        Args:
            arg1: desc for arg1
            arg2: desc for arg2
            some_arg: desc for some_arg
        """
        def __init__(self, arg1: int, arg2: str, some_arg: bool = True):
            ...

Widgets
~~~~~~~~~~~~~~~~

- Use the same patterns as described above for general classes.
- Specify the base widget using the ``:class:`` directive.
- If the widget can set properties using ``**kwargs``, you should mention it.

.. code-block:: python

    class SomeWidget:
        """
        Bases: :class:`Gtk.WIDGET_NAME`

        The description of the widget.

        Args:
            **kwargs: Properties to set.

        .. code-block:: python

            widgets.WIDGET_NAME(
                prop1="asd",
                prop2=12
            )
        """
        def __init__(self, **kwargs):
            ...

Building documentation
-------------------------

Install dependencies

.. code-block:: bash

    pip install -r docs/requirements.txt

Build

.. code-block:: bash

    cd docs
    make html

Built documentation will be stored at ``_build/html``.