Creating a Service
====================

Standard Service Structure
---------------------------

There is the standard service directory structure.

.. code-block:: bash

    SERVICE_NAME/
    ├── __init__.py
    ├── _imports.py
    ├── service.py
    ├── constants.py
    ├── util.py
    ├── related_class.py
    └── related_class2.py

``_imports.py``
----------------

If the service requires additional imports from ``gi.repository``,
which, in turn, requires installing dependencies by an user, define them here.

It should look like this:

.. code-block:: python

    import gi
    import sys
    from ignis.exceptions import GvcNotFoundError
    from ignis import is_sphinx_build

    # Gvc is here just for example.
    try:
        if not is_sphinx_build:  # prevent possible errors while building docs
            gi.require_version("Gvc", "1.0")
        from gi.repository import Gvc  # type: ignore
    except (ImportError, ValueError):
        raise GvcNotFoundError() from None

    __all__ = ["Gvc"]

And then, import them ONLY from this file:

.. code-block:: python

    from ._imports import Gvc
    # ... rest of code


``service.py``
---------------

Place the service class itself in this file.

All services should inherit from the :class:`~ignis.base_service.BaseService` class.

Here is simple template for service.

.. code-block:: python

    from ignis.base_service import BaseService

    class ExampleService(BaseService):
        def __init__(self):
            super().__init__()
            # do other stuff here


``constants.py``
-----------------

Define here constants for the service (if they are).

.. code-block:: python

    SOME_CONSTANT = 1
    ANOTHER_CONSTANT = "30"

``util.py``
-------------

If the service have additional non-class functions/utilities, define them here.

.. code-block:: python

    def useful_func(x: int, y: int) -> int:
        # ... do something
        return x + y

``related_class.py`` and others
--------------------------------

If the service manages other objects, define them in the appropriate files.

For example, ``AudioService`` manages ``Stream`` class, so we create separate file for it:

``stream.py``

.. code-block:: python

    class Stream(...):
        ...

``__init__.py``
----------------

Don't forget to add the service class, related classes and constants to the ``__all__`` list here.

.. code-block:: python

    from .service import ExampleService
    from .related_class import RelatedClass1
    from .related_class2 import RelatedClass2
    from .constants import SOME_CONSTANT

    __all__ = [
        "ExampleService",
        "RelatedClass1",
        "RelatedClass2",
        "SOME_CONSTANT"
    ]

Creating D-Bus Service
--------------------------

We will use :class:`~ignis.dbus.DBusService` in this template.

- Use ``PascalCase`` for D-Bus methods and properties naming.
- Also make D-Bus methods/properties private (add ``__`` before name).

.. code-block:: python

    from gi.repository import Gio, GLib
    from ignis.base_service import BaseService
    from ignis.dbus import DBusService

    class ExampleService(BaseService):
        def __init__(self):
            super().__init__()
            self.__dbus = DBusService(...)
            self.__dbus.register_dbus_method("MyMethod", self.__MyMethod)
            self.__dbus.register_dbus_property("MyProperty", self.__MyProperty)

        def __MyMethod(self, invocation: Gio.DBusMethodInvocation, param1: str, param2: int, *args) -> GLib.Variant:
            print("do something")
            return GLib.Variant("(is)", (42, "Hello world!"))

        def __MyProperty(self) -> GLib.Variant:
            return GLib.Variant("(b)", (False,))
