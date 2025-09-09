from ignis.widgets.picture import Picture
from gi.repository import Gtk, Gdk  # type: ignore
from gi.repository import Gtk4LayerShell as GtkLayerShell  # type: ignore
from ignis.exceptions import LayerShellNotSupportedError
from ignis.app import IgnisApp


class WallpaperLayerWindow(Gtk.Window):
    def __init__(
        self, wallpaper_path: str, gdkmonitor: Gdk.Monitor, width: int, height: int
    ) -> None:
        if not GtkLayerShell.is_supported():
            raise LayerShellNotSupportedError()

        app = IgnisApp.get_initialized()

        Gtk.Window.__init__(self, application=app)
        GtkLayerShell.init_for_window(self)

        for anchor in ["LEFT", "RIGHT", "TOP", "BOTTOM"]:
            GtkLayerShell.set_anchor(self, getattr(GtkLayerShell.Edge, anchor), True)

        GtkLayerShell.set_exclusive_zone(self, -1)  # ignore other layers

        GtkLayerShell.set_namespace(
            self, name_space=f"ignis_wallpaper_service_{gdkmonitor.get_model()}"
        )

        GtkLayerShell.set_layer(self, GtkLayerShell.Layer.BACKGROUND)

        GtkLayerShell.set_monitor(self, gdkmonitor)

        self.set_child(
            Picture(
                image=wallpaper_path,
                content_fit="cover",
                width=width,
                height=height,
            )
        )

        self.set_visible(True)
