import cairo
from gi.repository import Gtk  # type: ignore
from ignis.base_widget import BaseWidget
from ignis import utils
from gi.repository import Gtk4LayerShell as GtkLayerShell  # type: ignore
from ignis.exceptions import (
    MonitorNotFoundError,
    LayerShellNotSupportedError,
    WindowNotFoundError,
)
from ignis.gobject import IgnisProperty, IgnisSignal
from ignis.window_manager import WindowManager
from ignis.app import IgnisApp

window_manager = WindowManager.get_default()
LAYER = {
    "background": GtkLayerShell.Layer.BACKGROUND,
    "bottom": GtkLayerShell.Layer.BOTTOM,
    "top": GtkLayerShell.Layer.TOP,
    "overlay": GtkLayerShell.Layer.OVERLAY,
}

KB_MODE = {
    None: GtkLayerShell.KeyboardMode.NONE,
    "none": GtkLayerShell.KeyboardMode.NONE,
    "exclusive": GtkLayerShell.KeyboardMode.EXCLUSIVE,
    "on_demand": GtkLayerShell.KeyboardMode.ON_DEMAND,
}


ANCHOR = {
    "bottom": GtkLayerShell.Edge.BOTTOM,
    "left": GtkLayerShell.Edge.LEFT,
    "right": GtkLayerShell.Edge.RIGHT,
    "top": GtkLayerShell.Edge.TOP,
}

EXCLUSIVITY = {
    "ignore": -1,
    "normal": 0,
    "exclusive": 1,
}


class Window(Gtk.Window, BaseWidget):
    """
    Bases: :class:`Gtk.Window`

    The top-level widget that contains everything.

    Args:
        namespace: The name of the window, used to access it from the CLI and :class:`~ignis.app.IgnisApp`. It must be unique. It is also the name of the layer.
        dynamic_input_region: Whether to dynamically update the input region depending on the :attr:`child` size.
        **kwargs: Properties to set.

    .. warning::
        Applying CSS styles directly to ``widgets.Window`` can cause various graphical glitches/bugs.
        It's highly recommended to set some container (for example, ``widgets.Box``) or widget as a child and apply styles to it.
        For example:

        .. code-block:: python

            from ignis import widgets

            widgets.Window(
                namespace="some-window",
                # css_classes=['test-window'],  # don't do this!
                child=widgets.Box(
                    css_classes=['test-window'],  # use this instead
                    child=[...]
                )
            )

    Raises:
        LayerShellNotSupportedError: If the compositor does not support the Layer Shell protocol.

    .. code-block:: python

        widgets.Window(
            namespace="example_window",
            child=widgets.Label(label='heh'),
            monitor=0,
            anchor=["top", "right"],
            exclusive=True,
            layer="top",
            kb_mode="none",
            popup=False
        )

    """

    __gtype_name__ = "IgnisWindow"
    __gproperties__ = {**BaseWidget.gproperties}

    def __init__(
        self,
        namespace: str,
        monitor: int | None = None,
        anchor: list[str] | None = None,
        exclusivity: str = "normal",
        layer: str = "top",
        kb_mode: str = "none",
        popup: bool = False,
        margin_bottom: int = 0,
        margin_left: int = 0,
        margin_right: int = 0,
        margin_top: int = 0,
        dynamic_input_region: bool = False,
        **kwargs,
    ):
        if not GtkLayerShell.is_supported():
            raise LayerShellNotSupportedError()

        app = IgnisApp.get_initialized()

        Gtk.Window.__init__(self, application=app)
        GtkLayerShell.init_for_window(self)

        self._anchor = None
        self._exclusivity = None
        self._namespace = namespace
        self._layer = None
        self._kb_mode = None
        self._popup = None
        self._monitor = None
        self._input_width = 0
        self._input_height = 0
        self._margin_bottom = 0
        self._margin_left = 0
        self._margin_right = 0
        self._margin_top = 0
        self._dynamic_input_region = dynamic_input_region

        self.anchor = anchor
        self.exclusivity = exclusivity
        self.layer = layer
        self.kb_mode = kb_mode
        if monitor is not None:
            self.monitor = monitor
        self.popup = popup
        self.default_width = 2
        self.default_height = 2
        self.margin_bottom = margin_bottom
        self.margin_left = margin_left
        self.margin_right = margin_right
        self.margin_top = margin_top

        GtkLayerShell.set_namespace(self, name_space=namespace)

        window_manager.add_window(namespace, self)

        key_controller = Gtk.EventControllerKey()
        self.add_controller(key_controller)
        key_controller.connect("key-pressed", self.__close_popup)

        BaseWidget.__init__(self, **kwargs)

        self.connect("close-request", self.__on_close_request)

        if dynamic_input_region is True:
            self.__set_dynamic_input_region()

    def __set_dynamic_input_region(self) -> None:
        child = self.get_child()
        if not child:
            raise TypeError(
                "Trying to set dynamic_input_region to True but the child is None"
            )

        def sync() -> None:
            self.input_width = child.get_width()
            self.input_height = child.get_height()

        self.connect("size-changed", lambda *_: sync())

        sync()

    def __close_popup(self, event_controller_key, keyval, keycode, state):
        if self._popup:
            if keyval == 65307:  # 65307 = ESC
                self.visible = False

    @IgnisSignal
    def size_changed(self):  # private signal
        ...

    @IgnisProperty
    def namespace(self) -> str:
        """
        The name of the window, used to access it from the CLI and :class:`~ignis.app.IgnisApp`.

        It must be unique.
        It is also the name of the layer.
        """
        return self._namespace

    @IgnisProperty
    def anchor(self) -> list[str] | None:
        """
        A list of anchors.
        If the list is empty, the window will be centered on the screen.
        ``None`` will unset all anchors.

        Default: ``None``.

        Anchors:
            - bottom
            - left
            - right
            - top
        """
        return self._anchor

    @anchor.setter
    def anchor(self, value: list[str] | None) -> None:
        self._anchor = value

        if value is None:
            for i in ANCHOR.values():
                GtkLayerShell.set_anchor(self, i, False)
        else:
            for i in value:
                GtkLayerShell.set_anchor(self, ANCHOR[i], True)

    @IgnisProperty
    def exclusivity(self) -> str:
        """
        Defines how the compositor should avoid occluding a window area with other surfaces/layers.

        Default: ``normal``.

        Exclusivity:
            - ignore: Completely ignore other surfaces. This allows you to overlap other surfaces.
            - normal: The window will have no extra space and do not overlap other surfaces.
            - exclusive: The compositor will reserve extra space for this window.
        """
        return self._exclusivity

    @exclusivity.setter
    def exclusivity(self, value: str) -> None:
        self._exclusivity = value
        if value == "exclusive":
            GtkLayerShell.auto_exclusive_zone_enable(self)
        else:
            GtkLayerShell.set_exclusive_zone(self, EXCLUSIVITY[value])

    @IgnisProperty
    def layer(self) -> str:
        """
        The layer of the surface.

        Default: ``top``.

        Layer:
            - background
            - bottom
            - top
            - overlay
        """
        return self._layer

    @layer.setter
    def layer(self, value: str) -> None:
        self._layer = value
        GtkLayerShell.set_layer(self, LAYER[value])

    @IgnisProperty
    def kb_mode(self) -> str:
        """
        Whether the window should receive keyboard events from the compositor.

        Default: ``none``.

        Keyboard mode:
            - none: This window should not receive keyboard events.
            - exclusive: This window should have exclusive focus if it is on the top or overlay layer.
            - on_demand: The user should be able to focus and unfocus this window.
        """
        return self._kb_mode

    @kb_mode.setter
    def kb_mode(self, value: str) -> None:
        self._kb_mode = value
        GtkLayerShell.set_keyboard_mode(self, KB_MODE[value])

    @IgnisProperty
    def popup(self) -> bool:
        """
        Whether the window should close on ESC.

        Works only if ``kb_mode`` is set to ``exclusive`` or ``on_demand``.
        """
        return self._popup

    @popup.setter
    def popup(self, value: bool) -> None:
        self._popup = value

    @IgnisProperty
    def monitor(self) -> int:
        """
        The monitor number on which to display the window.

        Raises:
            :class:`~ignis.exceptions.MonitorNotFoundError` if the monitor with the given ID is not found.
        """
        return self._monitor

    @monitor.setter
    def monitor(self, value: int) -> None:
        if value is None:
            return

        gdkmonitor = utils.get_monitor(value)
        if gdkmonitor is None:
            raise MonitorNotFoundError(value)

        GtkLayerShell.set_monitor(self, gdkmonitor)
        self._monitor = value

    @IgnisProperty
    def input_width(self) -> int:
        """
        The width at which the window can receive keyboard and mouse input. Must be > 0.
        """
        return self._input_width

    @input_width.setter
    def input_width(self, value: int) -> None:
        self._input_width = value
        self.__change_input_region()

    @IgnisProperty
    def input_height(self) -> int:
        """
        The height at which the window can receive keyboard and mouse input. Must be > 0.
        """
        return self._input_height

    @input_height.setter
    def input_height(self, value: int) -> None:
        self._input_height = value
        self.__change_input_region()

    @IgnisProperty
    def dynamic_input_region(self) -> bool:
        """
        Whether to dynamically update the input region depending on the :attr:`child` size.
        """
        return self._dynamic_input_region

    @IgnisProperty
    def margin_bottom(self) -> int:
        """
        The bottom margin.

        Default: ``0``.
        """
        return self._margin_bottom

    @margin_bottom.setter
    def margin_bottom(self, value: int) -> None:
        self._margin_bottom = value
        GtkLayerShell.set_margin(self, GtkLayerShell.Edge.BOTTOM, value)

    @IgnisProperty
    def margin_left(self) -> int:
        """
        The left margin.

        Default: ``0``.
        """
        return self._margin_left

    @margin_left.setter
    def margin_left(self, value: int) -> None:
        self._margin_left = value
        GtkLayerShell.set_margin(self, GtkLayerShell.Edge.LEFT, value)

    @IgnisProperty
    def margin_right(self) -> int:
        """
        The right margin.

        Default: ``0``.
        """
        return self._margin_right

    @margin_right.setter
    def margin_right(self, value: int) -> None:
        self._margin_right = value
        GtkLayerShell.set_margin(self, GtkLayerShell.Edge.RIGHT, value)

    @IgnisProperty
    def margin_top(self) -> int:
        """
        The top margin.

        Default: ``0``.
        """
        return self._margin_top

    @margin_top.setter
    def margin_top(self, value: int) -> None:
        self._margin_top = value
        GtkLayerShell.set_margin(self, GtkLayerShell.Edge.TOP, value)

    def __change_input_region(self) -> None:
        if self.input_width < 0:
            raise ValueError("The input_width property must be greater than 0")

        if self.input_height < 0:
            raise ValueError("The input_height property must be greater than 0")

        rectangle = cairo.RectangleInt(0, 0, self.input_width, self.input_height)
        region = cairo.Region(rectangle)
        surface = self.get_surface()
        if not surface:
            self.connect("realize", lambda *args: self.__change_input_region())
            return

        surface.set_input_region(region)

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

    def do_size_allocate(self, width: int, height: int, baseline: int) -> None:
        self.emit("size-changed")
        return Gtk.Window.do_size_allocate(self, width, height, baseline)
