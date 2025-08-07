from gi.repository import Gtk  # type: ignore
from ignis.base_widget import BaseWidget
from ignis.window_manager import WindowManager
from ignis.exceptions import WindowNotFoundError
from ignis.gobject import IgnisProperty

window_manager = WindowManager.get_default()


class RegularWindow(Gtk.Window, BaseWidget):
    """
    Bases: :class:`Gtk.Window`

    A standard application window.

    Args:
        namespace: The name of the window, used for accessing it from the CLI and :class:`~ignis.app.IgnisApp`. It must be unique.
        **kwargs: Properties to set.

    .. code-block:: python

        widgets.RegularWindow(
            child=widgets.Label(label="this is regular window"),
            title="This is title",
            namespace='some-regular-window',
            titlebar=widgets.HeaderBar(show_title_buttons=True),
        )
    """

    __gtype_name__ = "IgnisRegularWindow"
    __gproperties__ = {**BaseWidget.gproperties}

    def __init__(self, namespace: str, **kwargs):
        Gtk.Window.__init__(self)
        BaseWidget.__init__(self, **kwargs)

        self._namespace = namespace

        window_manager.add_window(namespace, self)

        self.connect("close-request", self.__on_close_request)

    @IgnisProperty
    def namespace(self) -> str:
        """
        The name of the window, used for accessing it from the CLI and :class:`~ignis.app.IgnisApp`.
        It must be unique.
        """
        return self._namespace

    def __remove(self, *args) -> None:
        try:
            window_manager.remove_window(self.namespace)
        except WindowNotFoundError:
            pass

    def __on_close_request(self, *args) -> None:
        if not self.props.hide_on_close:
            self.__remove()

    def destroy(self):
        self.__remove()
        return super().destroy()

    def unrealize(self):
        self.__remove()
        return super().unrealize()
