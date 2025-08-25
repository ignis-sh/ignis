from ignis.gobject import IgnisProperty, DataGObject


class NiriWindowLayout(DataGObject):
    """
    Layout of a window.
    """

    def __init__(self):
        super().__init__()

        self._pos_in_scrolling_layout: list | None = None
        self._tile_size: list = []
        self._window_size: list = []
        self._tile_pos_in_workspace_view: list | None = None
        self._window_offset_in_tile: list = []

    @IgnisProperty
    def pos_in_scrolling_layout(self) -> list | None:
        """
        Location of a tiled window within a workspace.
        """
        return self._pos_in_scrolling_layout

    @IgnisProperty
    def tile_size(self) -> list:
        """
        Size of the tile this window is in.
        """
        return self._tile_size

    @IgnisProperty
    def window_size(self) -> list:
        """
        Size of the window’s visual geometry itself.
        """
        return self._window_size

    @IgnisProperty
    def tile_pos_in_workspace_view(self) -> list | None:
        """
        Tile position within the current view of the workspace.
        """
        return self._tile_pos_in_workspace_view

    @IgnisProperty
    def window_offset_in_tile(self) -> list:
        """
        Location of the window’s visual geometry within its tile.
        """
        return self._window_offset_in_tile
