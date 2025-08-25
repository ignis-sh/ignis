from gi.repository import Gtk  # type: ignore
from ignis.widgets.box import Box
from collections.abc import Callable
from ignis.gobject import IgnisProperty


class EventBox(Box):
    """
    Bases: :class:`~ignis.widgets.box.Box`

    The same :class:`~ignis.widgets.box.Box`, but it can receive events.

    Args:
        scroll_flags: Flags affecting the :class:`Gtk.EventControllerScroll` behavior.
        **kwargs: Properties to set.

    .. code-block:: python

        widgets.EventBox(
            child=[widgets.Label(label='this is eventbox'), widgets.Label(label="It can contain multiple child as widgets.Box")],
            vertical=True,
            homogeneous=False,
            spacing=52,
            on_click=lambda self: print("clicked!"),
            on_right_click=lambda self: print("right clicked!"),
            on_middle_click=lambda self: print("middle clicked!"),
            on_hover=lambda self: print("hovered!"),
            on_hover_lost=lambda self: print("hover lost((("),
            on_scroll_up=lambda self: print("scrolled up!"),
            on_scroll_down=lambda self: print("scrolled down!")
            on_scroll_right=lambda self: print("scrolled right!")
            on_scroll_left=lambda self: print("scrolled left!"),
        )
    """

    __gtype_name__ = "IgnisEventBox"

    def __init__(
        self,
        scroll_flags: Gtk.EventControllerScrollFlags = Gtk.EventControllerScrollFlags.BOTH_AXES,
        **kwargs,
    ):
        self._on_click: Callable | None = None
        self._on_right_click: Callable | None = None
        self._on_middle_click: Callable | None = None
        self._on_hover: Callable | None = None
        self._on_hover_lost: Callable | None = None

        self._scroll_flags: Gtk.EventControllerScrollFlags = scroll_flags
        self._on_scroll_up: Callable | None = None
        self._on_scroll_down: Callable | None = None
        self._on_scroll_right: Callable | None = None
        self._on_scroll_left: Callable | None = None

        self.__click_controller: Gtk.GestureClick | None = None
        self.__right_click_controller: Gtk.GestureClick | None = None
        self.__middle_click_controller: Gtk.GestureClick | None = None

        self.__scroll_controller: Gtk.EventControllerScroll | None = None
        self.__motion_controller: Gtk.EventControllerMotion | None = None

        super().__init__(**kwargs)

    def __init_click_controller(
        self, button: int, callback: Callable
    ) -> Gtk.GestureClick:
        def on_pressed(gesture_click: Gtk.GestureClick, n_press, x, y) -> None:
            gesture_click.set_state(Gtk.EventSequenceState.CLAIMED)
            callback(self)

        controller = Gtk.GestureClick()
        controller.set_button(button)
        self.add_controller(controller)
        controller.connect("pressed", on_pressed)
        return controller

    def __init_scroll_controller(self) -> None:
        if self.__scroll_controller:
            return

        controller = Gtk.EventControllerScroll.new(self._scroll_flags)
        self.add_controller(controller)
        controller.connect("scroll", self.__on_scroll)
        self.__scroll_controller = controller

    def __init_motion_controller(self) -> None:
        if self.__motion_controller:
            return

        controller = Gtk.EventControllerMotion.new()
        self.add_controller(controller)
        controller.connect("enter", self.__pointer_enter)
        controller.connect("leave", self.__pointer_leave)
        self.__motion_controller = controller

    def __on_scroll(
        self, event_controller: Gtk.EventControllerScroll, dx: float, dy: float
    ):
        if dy > 0 and self.on_scroll_up:
            self.on_scroll_up(self)
        elif dy < 0 and self.on_scroll_down:
            self.on_scroll_down(self)
        if dx > 0 and self.on_scroll_right:
            self.on_scroll_right(self)
        elif dx < 0 and self.on_scroll_left:
            self.on_scroll_left(self)

    def __pointer_enter(self, event_controller_motion, x, y) -> None:
        if self.on_hover:
            self.on_hover(self)

    def __pointer_leave(self, event_controller_motion) -> None:
        if self.on_hover_lost:
            self.on_hover_lost(self)

    @IgnisProperty
    def on_click(self) -> Callable:
        """
        The function to call on left click.
        """

        return self._on_click

    @on_click.setter
    def on_click(self, value: Callable) -> None:
        self._on_click = value

        if not self.__click_controller:
            self.__click_controller = self.__init_click_controller(
                1,
                lambda *args, **kwargs: self.on_click(*args, **kwargs),
            )

    @IgnisProperty
    def on_right_click(self) -> Callable:
        """
        The function to call on right click.
        """

        return self._on_right_click

    @on_right_click.setter
    def on_right_click(self, value: Callable) -> None:
        self._on_right_click = value

        if not self.__right_click_controller:
            self.__right_click_controller = self.__init_click_controller(
                3,
                lambda *args, **kwargs: self.on_right_click(*args, **kwargs),
            )

    @IgnisProperty
    def on_middle_click(self) -> Callable:
        """
        The function to call on middle click.
        """

        return self._on_middle_click

    @on_middle_click.setter
    def on_middle_click(self, value: Callable) -> None:
        self._on_middle_click = value

        if not self.__middle_click_controller:
            self.__middle_click_controller = self.__init_click_controller(
                2,
                lambda *args, **kwargs: self._on_middle_click(*args, **kwargs),
            )

    @IgnisProperty
    def on_hover(self) -> Callable:
        """
        The function to call on hover.
        """
        return self._on_hover

    @on_hover.setter
    def on_hover(self, on_hover: Callable) -> None:
        self._on_hover = on_hover
        self.__init_motion_controller()

    @IgnisProperty
    def on_hover_lost(self) -> Callable:
        """
        The function to call on hover lost.
        """
        return self._on_hover_lost

    @on_hover_lost.setter
    def on_hover_lost(self, on_hover_lost: Callable) -> None:
        self._on_hover_lost = on_hover_lost
        self.__init_motion_controller()

    @IgnisProperty
    def scroll_flags(self) -> Gtk.EventControllerScrollFlags:
        """
        Flags affecting the :class:`Gtk.EventControllerScroll` behavior.
        """
        return self._scroll_flags

    @IgnisProperty
    def on_scroll_up(self) -> Callable:
        """
        The function to call on scroll up.
        """
        return self._on_scroll_up

    @on_scroll_up.setter
    def on_scroll_up(self, on_scroll_up: Callable) -> None:
        self._on_scroll_up = on_scroll_up
        self.__init_scroll_controller()

    @IgnisProperty
    def on_scroll_down(self) -> Callable:
        """
        The function to call on scroll down.
        """
        return self._on_scroll_down

    @on_scroll_down.setter
    def on_scroll_down(self, on_scroll_down: Callable) -> None:
        self._on_scroll_down = on_scroll_down
        self.__init_scroll_controller()

    @IgnisProperty
    def on_scroll_right(self) -> Callable:
        """
        The function to call on scroll right.
        """
        return self._on_scroll_right

    @on_scroll_right.setter
    def on_scroll_right(self, on_scroll_right: Callable) -> None:
        self._on_scroll_right = on_scroll_right
        self.__init_scroll_controller()

    @IgnisProperty
    def on_scroll_left(self) -> Callable:
        """
        The function to call on scroll left.
        """
        return self._on_scroll_left

    @on_scroll_left.setter
    def on_scroll_left(self, on_scroll_left: Callable) -> None:
        self._on_scroll_left = on_scroll_left
        self.__init_scroll_controller()
