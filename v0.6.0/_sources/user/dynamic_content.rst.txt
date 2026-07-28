Dynamic content
=================

Static text can be boring, so let's add some dynamic elements!

.. code-block:: python

    import datetime
    from ignis import widgets
    from ignis import utils

    def update_label(clock_label: widgets.Label) -> None:
        text = datetime.datetime.now().strftime("%H:%M:%S")
        clock_label.set_label(text)

    def bar(monitor: int) -> widgets.Window:
        clock_label = widgets.Label()

        utils.Poll(1000, lambda x: update_label(clock_label))

        return widgets.Window(
            namespace=f"some-window-{monitor}",
            monitor=monitor,
            child=widgets.Box(
                vertical=True,
                spacing=10,
                child=[clock_label],
            ),
        )

This code updates label every second with the current time (using built-in Python module ``datetime``).

Signals
-------------

Polling data every second isn't always ideal, as it can negatively impact performance.
This is where **signals** are useful. 
Signals let us call a callback only when an event occurs (like ``on_click`` in ``widgets.Button``).

Let's consider services, which often have both **signals** and **properties**.

Here's an example using the :class:`~ignis.services.mpris.MprisService`:

.. code-block:: python

    from ignis.services.mpris import MprisService

    mpris = MprisService.get_default()

    mpris.connect("player_added", lambda x, player: print(player.desktop_entry, player.title))
    #                                    ^    ^
    # Signals always pass the GObject they belong to as the first argument to the callback.
    # In this case, MprisPlayer is the second argument of the signal.

Now, open any media player (like a video on YouTube or music on Spotify). 
Magic! The player name and title will be printed.

.. hint::

    To manually emit (trigger) a signal, use the ``.emit()`` method and pass the signal name to it.

Binding
-----------

Next, let's **bind** a property.
Use the ``.bind()`` method, passing the property name as the first argument, and optionally a **transform** function.

.. code-block:: python

    from ignis.services.audio import AudioService
    from ignis import widgets

    audio = AudioService.get_default()

    def bar(monitor: int) -> widgets.Window:
        return widgets.Window(
            namespace=f"some-window-{monitor}",
            monitor=monitor,
            child=widgets.Box(
                child=[
                    widgets.Label(label="Current volume: "),
                    widgets.Label(
                        label=audio.speaker.bind("volume", lambda value: str(value))  # this function converts the value to a string
                    )
                ]
            ),
        )

Try changing the speaker volume using a tool like ``pavucontrol``.

When the property changes, the transform function (if provided) will be called with the new value, and it should return the processed result.

Multiple Binding
-----------------

You can bind multiple properties at the same time with ``bind_many()``.

.. code-block:: python

    widgets.Scale(
        value=audio.speaker.bind_many(
            ["volume", "is_muted"],
            lambda volume, is_muted: 0 if is_muted else volume,
        ),
    )

``notify`` signal
------------------
The ``notify`` is a special signal that emits when a property changes.
To connect to it, use the following syntax: ``"notify::PROPERTY-NAME"``.

.. danger::

    Make sure to use ``-`` instead of ``_`` in the property name. 
    Otherwise, the signal will not be triggered.

.. code-block:: python

    mpris.connect("notify::players", lambda x, y: print(x.players))