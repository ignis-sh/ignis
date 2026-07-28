Services
==========
There is a list of built-in services that provide additional functionality to build various components of your desktop.

To access a service, import it and call the ``.get_default()`` method.

.. code-block:: python

   from ignis.services.audio import AudioService

   audio = AudioService.get_default()

Built-in services
-----------------

.. hint::
   If the service you need is not here, you can make your own.
   
   See `Creating Service <../../dev/creating_service.html>`_ for more info.

.. toctree:: 
   :glob:
   :maxdepth: 1

   ./*
