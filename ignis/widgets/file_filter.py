from gi.repository import Gtk  # type: ignore
from ignis.gobject import IgnisGObject
from ignis.gobject import IgnisProperty


class FileFilter(Gtk.FileFilter, IgnisGObject):
    """
    Bases: :class:`Gtk.FileFilter`

    .. note::
        This is not a regular widget.
        It doesn't support common widget properties and cannot be added as a child to a container.

    A file filter.
    Intended for use in :class:`~ignis.widgets.FileDialog`.
    Uses MIME types, `here <https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types/Common_types>`_ is a list of common MIME types.

    Args:
        mime_types: A list of MIME types.
        **kwargs: Properties to set.

    .. code-block :: python

        widgets.FileFilter(
            mime_types=["image/jpeg", "image/png"],
            default=True,
            name="Images JPEG/PNG",
        )
    """

    __gtype_name__ = "IgnisFileFilter"

    def __init__(self, mime_types: list[str], **kwargs):
        Gtk.FileFilter.__init__(self)
        self._default: bool = False
        self._mime_types = mime_types
        IgnisGObject.__init__(self, **kwargs)

        for i in mime_types:
            self.add_mime_type(i)

    @IgnisProperty
    def mime_types(self) -> list[str]:
        """
        A list of MIME types.
        """
        return self._mime_types

    @IgnisProperty
    def default(self) -> bool:
        """
        Whether the filter will be selected by default.
        """
        return self._default

    @default.setter
    def default(self, value: bool) -> None:
        self._default = value
