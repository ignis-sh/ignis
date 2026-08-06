from gi.repository import GioUnix  # type: ignore
from ignis.gobject import IgnisGObject
from ignis.gobject import IgnisProperty


class ApplicationAction(IgnisGObject):
    """
    Application action.
    """

    def __init__(self, app: GioUnix.DesktopAppInfo, action: str):
        super().__init__()

        self._app = app
        self._action = action
        self._name: str = app.get_action_name(action)

    @IgnisProperty
    def action(self) -> str:
        """
        The ID of the action.
        """
        return self._action

    @IgnisProperty
    def name(self) -> str:
        """
        The human-readable name of the action.
        """
        return self._name

    def launch(self) -> None:
        """
        Launch this action.
        """
        self._app.launch_action(self.action, None)
