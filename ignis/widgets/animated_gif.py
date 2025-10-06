from gi.repository import GdkPixbuf, GLib, Gtk  # type: ignore

from ignis.base_widget import BaseWidget
from ignis.gobject import IgnisProperty


class AnimatedGif(Gtk.Picture, BaseWidget):
    """
    Bases: :class:`Gtk.Picture`

    A widget that displays animated GIF files.

    The widget automatically scales each frame to the specified dimensions and provides
    control over animation duration, looping behavior.

    Args:
        **kwargs: Properties to set.

    .. code-block:: python

        widgets.AnimatedGif(
            image="path/to/animation.gif",
            width_request=200,
            height_request=150,
            duration_ms=5000,  # Auto-stop after 5 seconds
            loop=False,        # Play once only
        )
    """

    __gtype_name__ = "IgnisAnimatedGif"
    __gproperties__ = {**BaseWidget.gproperties}

    def __init__(self, **kwargs):
        Gtk.Picture.__init__(self)

        self._image: str | None = None
        self._duration_ms: int = 0
        self._loop: bool = False

        # Animation state
        self.__interp = GdkPixbuf.InterpType.BILINEAR
        self.__anim: GdkPixbuf.PixbufAnimation | None = None
        self.__iter: GdkPixbuf.PixbufAnimationIter | None = None
        self.__timeout_id: int | None = None
        self.__start_time = 0

        BaseWidget.__init__(self, **kwargs)

    @IgnisProperty
    def image(self) -> str | None:
        """
        Path to the GIF file.
        """
        return self._image

    @image.setter
    def image(self, value: str) -> None:
        if self._image != value:
            self._image = value
            self.__load_animation()

    @IgnisProperty
    def duration_ms(self) -> int:
        """
        Duration in milliseconds before auto-stopping animation.

        Set to 0 for infinite animation.
        """
        return self._duration_ms

    @duration_ms.setter
    def duration_ms(self, value: int) -> None:
        self._duration_ms = value

    @IgnisProperty
    def loop(self) -> bool:
        """
        Whether to loop the animation continuously.
        """
        return self._loop

    @loop.setter
    def loop(self, value: bool) -> None:
        self._loop = value

    def start(self) -> None:
        """
        Start the animation.
        """
        if self.__anim and not self.__timeout_id:
            self.__start_time = GLib.get_monotonic_time() // 1000
            if self.__iter:
                self.__tick()

    def stop(self) -> None:
        """
        Stop the animation.
        """
        if self.__timeout_id:
            GLib.source_remove(self.__timeout_id)
            self.__timeout_id = None

    def restart(self) -> None:
        """
        Restart the animation from the beginning.
        """
        if self.__anim:
            self.stop()
            self.__iter = self.__anim.get_iter()
            self.start()

    def __load_animation(self) -> None:
        if not self._image:
            return

        self.stop()  # Stop any existing animation

        try:
            self.__anim = GdkPixbuf.PixbufAnimation.new_from_file(self._image)
            if self.__anim is not None:
                self.__iter = self.__anim.get_iter()
            self.start()
        except Exception:
            # If loading fails, clear the animation state
            self.__anim = None
            self.__iter = None

    @staticmethod
    def __get_current_time() -> GLib.TimeVal:
        usec = GLib.get_monotonic_time()
        tv = GLib.TimeVal()
        tv.tv_sec, tv.tv_usec = divmod(usec, 1_000_000)
        return tv

    def __elapsed_ms(self) -> int:
        return (GLib.get_monotonic_time() // 1000) - self.__start_time

    def __scale_pixbuf(self, pixbuf: GdkPixbuf.Pixbuf) -> GdkPixbuf.Pixbuf:
        if self.width_request <= 0 or self.height_request <= 0:
            return pixbuf

        current_width = pixbuf.get_width()
        current_height = pixbuf.get_height()

        if (
            current_width == self.width_request
            and current_height == self.height_request
        ):
            return pixbuf

        scaled = pixbuf.scale_simple(
            self.width_request, self.height_request, self.__interp
        )
        return scaled if scaled is not None else pixbuf

    def __tick(self) -> bool:
        """Animation tick - update current frame and schedule next."""
        if not self.__iter:
            return False

        # Update the displayed frame
        current_pixbuf = self.__iter.get_pixbuf()
        scaled_pixbuf = self.__scale_pixbuf(current_pixbuf)
        self.set_pixbuf(scaled_pixbuf)

        # Check duration limit
        if self._duration_ms > 0 and self.__elapsed_ms() >= self._duration_ms:
            self.__timeout_id = None
            return False

        # Advance to next frame
        at_end = not self.__iter.advance(self.__get_current_time())

        # Check if animation ended and shouldn't loop
        if at_end and not self._loop:
            self.__timeout_id = None
            return False

        # Schedule next frame update
        delay = max(20, self.__iter.get_delay_time())  # Minimum 20ms delay
        self.__timeout_id = GLib.timeout_add(delay, self.__tick)

        return False  # Don't repeat this timeout (new one scheduled)

    def do_unroot(self) -> None:
        # Clean up animation when widget is removed.
        self.stop()
        super().do_unroot()
