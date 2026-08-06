import os
from ignis.base_widget import BaseWidget
from gi.repository import Gtk, GdkPixbuf, Gdk  # type: ignore
from ignis import utils
from ignis.gobject import IgnisProperty


class Picture(Gtk.Picture, BaseWidget):
    """
    Bases: :class:`Gtk.Picture`

    A widget that displays an image at its native aspect ratio.

    Overrided properties:
        - content_fit: Controls how a content should be made to fit inside an allocation. Default: ``contain``.

    Content fit:
        - fill: Make the content fill the entire allocation, without taking its aspect ratio in consideration.
        - contain: Scale the content to fit the allocation, while taking its aspect ratio in consideration..
        - cover: Cover the entire allocation, while taking the content aspect ratio in consideration.
        - scale_down: The content is scaled down to fit the allocation, if needed, otherwise its original size is used.

        For more info, see :class:`Gtk.ContentFit`.

    Args:
        **kwargs: Properties to set.

    .. code-block:: python

        widgets.Picture(
            image='path/to/img',
            width=20,
            height=30
        )
    """

    __gtype_name__ = "IgnisPicture"
    __gproperties__ = {**BaseWidget.gproperties}

    def __init__(
        self,
        content_fit: str = "contain",
        width: int = -1,
        height: int = -1,
        blur_radius: int = 0,
        **kwargs,
    ):
        Gtk.Picture.__init__(self)
        self.override_enum("content_fit", Gtk.ContentFit)

        # avoid custom setters to avoid running the __draw function multiple times during initialization
        self._image: str | GdkPixbuf.Pixbuf | None = None
        self._width = width
        self._height = height
        self._blur_radius = blur_radius
        self.width_request = width
        self.height_request = height

        self.content_fit = content_fit

        BaseWidget.__init__(self, **kwargs)

    @IgnisProperty
    def image(self) -> "str | GdkPixbuf.Pixbuf | None":
        """
        The icon name, path to an image or ``GdkPixbuf.Pixbuf``.
        """
        return self._image

    @image.setter
    def image(self, value: "str | GdkPixbuf.Pixbuf") -> None:
        self._image = value
        self.__draw(value)

    @IgnisProperty
    def width(self) -> int:
        """
        Width of the image.
        """
        return self._width

    @width.setter
    def width(self, value: int) -> None:
        self._width = value
        self.width_request = value
        self.__draw(self.image)

    @IgnisProperty
    def height(self) -> int:
        """
        Height of the image.
        """
        return self._height

    @height.setter
    def height(self, value: int) -> None:
        self._height = value
        self.height_request = value
        self.__draw(self.image)

    @IgnisProperty
    def blur_radius(self) -> int:
        """
        The blur radius of the image in pixels.
        """
        return self._blur_radius

    @blur_radius.setter
    def blur_radius(self, value: int) -> None:
        self._blur_radius = value
        self.queue_draw()

    def do_snapshot(self, snapshot: Gtk.Snapshot) -> None:
        snapshot.push_blur(self._blur_radius)

        Gtk.Picture.do_snapshot(self, snapshot)

        snapshot.pop()

    def __draw(self, image: "str | GdkPixbuf.Pixbuf") -> None:
        if isinstance(image, GdkPixbuf.Pixbuf):
            self.__set_from_pixbuf(image)
        elif isinstance(image, str):
            if os.path.isfile(image):
                if os.path.splitext(image)[1] == ".svg":
                    self.__set_from_svg(image)
                else:
                    self.__set_from_file(image)
            else:
                self.__set_from_icon_name(image)

    def __set_from_pixbuf(self, pixbuf: GdkPixbuf.Pixbuf) -> None:
        scalled_pixbuf = self.__scale_pixbuf(pixbuf, self.width, self.height)
        if not scalled_pixbuf:
            return

        paintable = Gdk.Texture.new_for_pixbuf(scalled_pixbuf)
        self.set_paintable(paintable)

    def __set_from_file(self, filename: str) -> None:
        pixbuf = GdkPixbuf.Pixbuf.new_from_file(filename)
        if not pixbuf:
            return

        self.__set_from_pixbuf(pixbuf)

    def __set_from_svg(self, filename: str) -> None:
        if not filename:
            return
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
            filename, self.width, self.height, True
        )
        if not pixbuf:
            return

        paintable = Gdk.Texture.new_for_pixbuf(pixbuf)
        self.set_paintable(paintable)
        return

    def __set_from_icon_name(self, icon_name: str) -> None:
        size = max(self.height, self.width)
        if size <= 0:
            size = 16

        paintable = utils.get_paintable(self, icon_name, size)

        if not paintable:
            return

        gfile = paintable.get_file()

        if not gfile:
            return

        path = gfile.get_path()

        if not isinstance(path, str):
            return

        self.set_paintable(paintable)
        self.__set_from_svg(path)

    def __scale_pixbuf(
        self, pixbuf: GdkPixbuf.Pixbuf, width: int, height: int
    ) -> "GdkPixbuf.Pixbuf | None":
        if width <= 0:
            return pixbuf

        if height <= 0:
            return pixbuf

        if self.content_fit == "cover":
            pixbuf = utils.crop_pixbuf(pixbuf, width, height)

        return utils.scale_pixbuf(pixbuf, width, height)
