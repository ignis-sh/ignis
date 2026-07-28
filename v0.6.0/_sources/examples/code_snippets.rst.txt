Code Snippets
==============

This page provides useful code snippets to help you implement additional functionality. 

Clicking outside of a window
----------------------------

A common use case is to close a window.

.. code-block:: python

    widgets.Window(
        namespace="my-window",
        anchor=["left", "right", "top", "bottom"],  # to make a window fullscreen
        child=widgets.Overlay(
            child=widgets.Button(
                vexpand=True,
                hexpand=True,
                can_focus=False,
                on_click=lambda x: CALLBACK, # e.g., window_manager.close_window("my-window")
            ),
            overlays=[ACTUAL_CONTENT],
        ),
    )

Replace ``ACTUAL_CONTENT`` with the actual widgets you want to put in the window.

.. warning::
    If ``ACTUAL_CONTENT`` fills all of the screen, 
    set ``valign`` and ``halign`` with values other than ``fill`` (e.g., ``center``).


Listen for key events
----------------------

Currently Ignis doesn't have a convenient API for this.
But you can always use GTK directly.

Use :class:`Gtk.EventControllerKey`:

.. code-block:: python

    from gi.repository import Gtk

    def handle_key_press(
        event_controller_key: Gtk.EventControllerKey,
        keyval: int,
        keycode: int,
        state: Gdk.ModifierType,
    ) -> None:
        print(keyval)

    key_controller = Gtk.EventControllerKey()
    WIDGET.add_controller(key_controller)
    # Listen for the pressed event
    # Gtk.EventControllerKey has other signals, e.g., "key-released"
    # Check out PyGObject docs for more info
    key_controller.connect("key-pressed", handle_key_press)

Replace ``WIDGET`` with the widget on which you want to listen for key events.

Display applications icons on Hyprland workspaces buttons
---------------------------------------------------------

.. code-block:: python

    # The code from the example bar

    def hyprland_workspace_button(workspace: HyprlandWorkspace) -> widgets.Button:
        widget = widgets.Button(
            css_classes=["workspace"],
            on_click=lambda x: workspace.switch_to(),
            child=widgets.Box(
                child=hyprland.bind(
                    "windows",
                    lambda _: [
                        # find the icon of the app by its class name
                        widgets.Icon(icon_name=utils.get_app_icon_name(window.class_name))
                        # get all windows on the current workspace
                        for window in hyprland.get_windows_on_workspace(
                            workspace_id=workspace.id
                        )
                    ],
                )
            ),
        )
        if workspace.id == hyprland.active_workspace.id:
            widget.add_css_class("active")

        return widget