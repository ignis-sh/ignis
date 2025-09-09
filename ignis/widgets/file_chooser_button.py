import os
import asyncio
from gi.repository import Gtk  # type: ignore
from ignis.base_widget import BaseWidget
from ignis.widgets.label import Label
from ignis.widgets.box import Box
from ignis.widgets.icon import Icon
from ignis.widgets.file_dialog import FileDialog
from ignis import utils
from ignis.gobject import IgnisProperty


class FileChooserButton(Gtk.Button, BaseWidget):
    """
    Bases: :class:`Gtk.Button`

    A button that allows the user to select a file.

    Args:
        dialog: An instance of :class:`~ignis.widgets.FileDialog`.
        label: An instance of :class:`~ignis.widgets.Label`.
        **kwargs: Properties to set.

    .. code-block :: python

        widgets.FileChooserButton(
            dialog=widgets.FileDialog(
                initial_path=os.path.expanduser("~/.wallpaper"),
                filters=[
                    widgets.FileFilter(
                        mime_types=["image/jpeg", "image/png"],
                        default=True,
                        name="Images JPEG/PNG",
                    )
                ]
            ),
            label=widgets.Label(label='Select', ellipsize="end", max_width_chars=20)
        )
    """

    __gtype_name__ = "IgnisFileChooserButton"
    __gproperties__ = {**BaseWidget.gproperties}

    def __init__(
        self,
        dialog: FileDialog,
        label: Label,
        **kwargs,
    ):
        Gtk.Button.__init__(self)
        BaseWidget.__init__(self, **kwargs)

        self._dialog = dialog
        self._label = label

        self.__file_icon = Icon(visible=False, style="padding-right: 7px;")

        self.child = Box(
            child=[
                self.__file_icon,
                self.label,
                Icon(icon_name="document-open-symbolic", style="padding-left: 10px;"),
            ],
        )
        self.dialog.connect("file-set", lambda x, file: self.__sync(file.get_path()))

        if self.dialog.initial_path:
            self.__sync(self.dialog.initial_path)

        self.connect(
            "clicked",
            lambda *args: asyncio.create_task(self.dialog.open_dialog()),
        )

    @IgnisProperty
    def dialog(self) -> FileDialog:
        """
        An instance of :class:`~ignis.widgets.FileDialog`.
        """
        return self._dialog

    @IgnisProperty
    def label(self) -> Label:
        """
        An instance of :class:`~ignis.widgets.Label`.
        """
        return self._label

    def __sync(self, path: str) -> None:
        self.label.label = os.path.basename(path)
        try:
            self.__file_icon.icon_name = utils.get_file_icon_name(path, symbolic=True)
            self.__file_icon.visible = True
        except FileNotFoundError:
            pass
