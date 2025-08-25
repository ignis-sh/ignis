import json
import os
import socket
from ignis import utils
from ignis.exceptions import NiriIPCNotFoundError
from ignis.base_service import BaseService
from ignis.gobject import IgnisProperty, IgnisSignal
from ignis.app import IgnisApp
from .constants import NIRI_SOCKET
from .keyboard import NiriKeyboardLayouts
from .window import NiriWindow
from .workspace import NiriWorkspace


class NiriService(BaseService):
    """
    Niri IPC client.

    Example usage:

    .. code-block:: python

        from ignis.services.niri import NiriService

        niri = NiriService.get_default()

        # Get IDs of all workspaces
        print([i.id for i in niri.workspaces])

        # Get the ID of the active workspace on eDP-1
        print([i.id for i in niri.workspaces if i.is_active and i.output == "eDP-1"])

        # Get the currently active keyboard layout
        print(niri.keyboard_layouts.current_name)

        # Get the title of the active window
        print(niri.active_window.title)
    """

    def __init__(self):
        super().__init__()

        self._keyboard_layouts: NiriKeyboardLayouts = NiriKeyboardLayouts(self)
        self._windows: dict[int, NiriWindow] = {}
        self._active_window: NiriWindow = NiriWindow(self)
        self._workspaces: dict[int, NiriWorkspace] = {}
        self._active_output: str = ""
        self._overview_opened = False

        if self.is_available:
            self.__start_event_stream()

    @IgnisSignal
    def workspace_added(self, workspace: NiriWorkspace):
        """
        Emitted when a new workspace has been added.

        Args:
            workspace: The instance of the workspace.
        """

    @IgnisProperty
    def is_available(self) -> bool:
        """
        Whether Niri IPC is available.
        """
        if NIRI_SOCKET is not None:
            return os.path.exists(NIRI_SOCKET)
        else:
            return False

    @IgnisProperty
    def keyboard_layouts(self) -> NiriKeyboardLayouts:
        """
        The currenly configured keyboard layouts.
        """
        return self._keyboard_layouts

    @IgnisProperty
    def windows(self) -> list[NiriWindow]:
        """
        A list of windows.
        """
        return list(self._windows.values())

    @IgnisProperty
    def active_window(self) -> NiriWindow:
        """
        The currently focused window.

        .. note::
            If there is no window is focused, it will return an "empty" :class:`NiriWindow`, where:

            - all ``int``-properties are ``-1``
            - all ``str``-properties are ``""``
            - all ``bool``-properties are ``False``.
        """
        return self._active_window

    @IgnisProperty
    def workspaces(self) -> list[NiriWorkspace]:
        """
        A list of workspaces.
        """
        return list(self._workspaces.values())

    @IgnisProperty
    def active_output(self) -> str:
        """
        The currenly focused output.
        """
        return self._active_output

    @IgnisProperty
    def overview_opened(self) -> bool:
        """
        The current state of the overview.
        """
        return self._overview_opened

    def __start_event_stream(self) -> None:
        # Initialize socket connection
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(str(NIRI_SOCKET))
        sock.send(b'"EventStream"\n')

        # Close socket gracefully on app quit
        IgnisApp.get_initialized().connect("shutdown", lambda *_: sock.close())

        # Launch an unthreaded event stream to ensure all variables get initialized
        # before returning from __init__ . OverviewOpenedOrClosed is the last
        # event to be sent during initialization of the Niri event stream, so once
        # it is received, we are ready to launch a threaded (non blocking) version.
        self.__listen_events(sock=sock, break_on="OverviewOpenedOrClosed")

        utils.thread(lambda: self.__listen_events(sock=sock))
        # No need to send any other commands after event stream initialization:
        #
        #  "The event stream IPC is designed to give you the complete current
        #  state up-front, then follow up with updates to that state. This way,
        #  your state can never "desync" from niri, and you don't need to make
        #  any other IPC information requests."
        #   - https://github.com/YaLTeR/niri/wiki/IPC

    def __listen_events(self, sock: socket.socket, break_on: str = "") -> None:
        for event in utils.listen_socket(sock, errors="ignore"):
            json_data = json.loads(event)
            event_type = list(json_data.keys())[0]
            event_data = list(json_data.values())[0]

            self.__on_event_received(event_type, event_data)
            if break_on and break_on == event_type:
                return

    def __on_event_received(self, event_type: dict, event_data: dict) -> None:
        match event_type:
            case "KeyboardLayoutSwitched":
                self.__update_current_layout(event_data)
            case "KeyboardLayoutsChanged":
                self.__update_keyboard_layouts(event_data)
            case "WindowClosed":
                self.__destroy_window(event_data)
            case "WindowFocusChanged":
                self.__update_window_focus(event_data)
            case "WindowOpenedOrChanged":
                self.__update_window(event_data)
            case "WindowsChanged":
                self.__update_windows(event_data)
            case "WindowLayoutsChanged":
                self.__update_window_layouts(event_data)
            case "WorkspaceActivated":
                self.__update_active_workspace(event_data)
            case "WorkspaceActiveWindowChanged":
                self.__update_workspace_active_window(event_data)
            case "WorkspacesChanged":
                self.__update_workspaces(event_data)
            case "OverviewOpenedOrClosed":
                self.__update_overview_opened(event_data)

    def __update_current_layout(self, data: dict) -> None:
        self._keyboard_layouts.sync({"current_idx": data["idx"]})
        self.notify("keyboard_layouts")
        self._keyboard_layouts.notify("current_name")

    def __update_keyboard_layouts(self, data: dict) -> None:
        self._keyboard_layouts.sync(data["keyboard_layouts"])
        self.notify("keyboard_layouts")
        self._keyboard_layouts.notify("current_name")

    def __sort_windows(self) -> None:
        self._windows = dict(sorted(self._windows.items()))

    def __destroy_window(self, data: dict) -> None:
        window = self._windows.pop(data["id"])
        if window:
            window.emit("destroyed")
            self.__sort_windows()
            self.notify("windows")

    def __update_window(self, data: dict) -> None:
        window_data = data["window"]
        window = self._windows.get(window_data["id"], None)
        if window is None:
            window = NiriWindow(self)

        window.sync(window_data)
        self._windows[window_data["id"]] = window

        if window.is_focused:
            self._active_window.sync(window_data)

        self.__sort_windows()

        self.notify("active-window")
        self.notify("windows")

    def __update_window_focus(self, data: dict) -> None:
        # Id of the newly focused window, or None if no window is now focused.
        focused_id = data["id"]
        for window in self._windows.values():
            # If a window became focused, it implies that all other windows
            # are no longer focused. Go through existing windows and
            # update their state accordingly.
            window.sync({"is_focused": (window.id == focused_id)})

        if focused_id:
            self._active_window.sync(self._windows[focused_id].data)
        else:
            window_skeleton = NiriWindow(self)
            self._active_window.sync(window_skeleton.data)

        self.notify("active-window")
        self.notify("windows")

    def __update_niri_obj(
        self,
        niri_obj: dict,
        fresh_data: list,
        obj_type: type[NiriWindow] | type[NiriWorkspace],
    ) -> None:
        for fresh_item in fresh_data:
            obj = niri_obj.get(fresh_item["id"], None)
            if obj is None:
                obj = obj_type(self)

            obj.sync(fresh_item)
            niri_obj[fresh_item["id"]] = obj

    def __cleanup_niri_obj(self, niri_obj: dict, fresh_data: list) -> None:
        for id_, item in niri_obj.copy().items():
            still_exists = False
            for fresh_item in fresh_data:
                if fresh_item["id"] == id_:
                    still_exists = True
                    break

            if not still_exists:
                niri_obj.pop(id_)
                item.emit("destroyed")

    def __update_windows(self, data: dict) -> None:
        windows = data["windows"]
        # WindowsChanged means a full replacement of window configuration.
        # Update every window accordingly.
        self.__update_niri_obj(self._windows, windows, NiriWindow)

        for window_data in windows:
            if window_data["is_focused"]:
                self._active_window.sync(window_data)

        # Drop windows that don't exist anymore.
        self.__cleanup_niri_obj(self._windows, windows)

        self.__sort_windows()

        self.notify("active-window")
        self.notify("windows")

    def __update_window_layouts(self, data: dict) -> None:
        changes = data["changes"]
        for item in changes:
            id, layout = item
            self._windows[id].sync({"layout": layout})

            if id == self._active_window.id:
                self._active_window.sync({"layout": layout})
                self.notify("active-window")

        self.notify("windows")

    def __sort_workspaces(self) -> None:
        self._workspaces = dict(
            sorted(self._workspaces.items(), key=lambda w: w[1].idx)
        )

    def __update_workspaces(self, data: dict) -> None:
        workspaces = data["workspaces"]
        # WorkspacesChanged means a full replacement of workspace configuration.
        # Update every workspace accordingly.
        self.__update_niri_obj(self._workspaces, workspaces, NiriWorkspace)

        # Drop workspaces that don't exist anymore.
        self.__cleanup_niri_obj(self._workspaces, workspaces)

        self.__sort_workspaces()

        self._active_output = [w for w in self._workspaces.values() if w.is_focused][
            0
        ].output
        self.notify("active-output")
        self.notify("workspaces")

    def __update_active_workspace(self, data: dict) -> None:
        active_ws_id = data["id"]
        is_focused = data["focused"]
        output = self._workspaces[active_ws_id].output

        for workspace in self._workspaces.values():
            data = {}
            # If a workspace became active, it implies that all other workspaces
            # on the same monitor became inactive. Go through existing workspaces
            # and update their state accordingly.
            got_activated = workspace.id == active_ws_id

            if workspace.output == output:
                data["is_active"] = got_activated
            if is_focused:
                data["is_focused"] = got_activated

            workspace.sync(data)

        if is_focused:
            self._active_output = output

        self.notify("active-output")
        self.notify("workspaces")

    def __update_workspace_active_window(self, data: dict) -> None:
        self._workspaces[data["workspace_id"]].sync(
            {"active_window_id": data["active_window_id"]}
        )

    def __update_overview_opened(self, data: dict) -> None:
        self._overview_opened = data["is_open"]
        self.notify("overview_opened")

    def send_command(self, cmd: dict | str) -> str:
        """
        Send a command to the Niri IPC.

        Args:
            cmd: The command to send.

        Returns:
            Response from Niri IPC.

        Raises:
            NiriIPCNotFoundError: If Niri IPC is not found.
        """
        if not self.is_available or NIRI_SOCKET is None:
            raise NiriIPCNotFoundError()

        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.connect(NIRI_SOCKET)
            return utils.send_socket(
                sock, json.dumps(cmd) + "\n", errors="ignore", end_char="\n"
            )

    def switch_kb_layout(self) -> None:
        """
        Switch to the next keyboard layout.
        """
        cmd = {"Action": {"SwitchLayout": {"layout": "Next"}}}
        self.send_command(cmd)

    def switch_to_workspace(self, workspace_id: int) -> None:
        """
        Switch to a workspace by its ``idx``.

        .. note::
            This function switches to the workspace on the currently active monitor.

            If you have multiple monitors and want to switch to a workspace
            by its unique ID (not by ``idx``), use :func:`switch_to_workspace_by_id`.

        Args:
            workspace_id: The ``idx`` of the workspace to switch to.
        """
        cmd = {"Action": {"FocusWorkspace": {"reference": {"Index": workspace_id}}}}
        self.send_command(cmd)

    def switch_to_workspace_by_id(self, workspace_id: int) -> None:
        """
        Switch to a workspace by its unique ID.

        Args:
            workspace_id: The unique ID of the workspace to switch to.
        """
        cmd = {"Action": {"FocusWorkspace": {"reference": {"Id": workspace_id}}}}
        self.send_command(cmd)

    def get_workspace_by_id(self, workspace_id: int) -> NiriWorkspace | None:
        """
        Get a workspace by its ID.

        Args:
            workspace_id: The ID of the workspace.
        Returns:
            The workspace instance, or ``None`` if the workspace with the given ID doesn't exist.
        """
        return self._workspaces.get(workspace_id, None)
