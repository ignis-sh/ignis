import json
import os
import socket
from gi.repository import GObject  # type: ignore
from ignis.utils import Utils
from typing import Any
from ignis.exceptions import NiriIPCNotFoundError
from ignis.base_service import BaseService
from ignis.logging import logger
from .constants import NIRI_SOCKET


class NiriService(BaseService):
    """
    Niri IPC client.

    Example usage:

    .. code-block:: python

        from ignis.services.niri import NiriService

        niri = NiriService.get_default()

        print(niri.workspaces)
        print(niri.kb_layout)

        niri.connect("notify::kb-layout", lambda x, y: print(niri.kb_layout))
    """

    def __init__(self):
        super().__init__()

        self._workspaces: list[dict[str, Any]] = []
        self._active_workspaces: list[dict[str, Any]] = []
        self._kb_layout: str = ""
        self._active_window: dict[str, Any] = {}
        self._active_output: dict[str, Any] = {}

        if self.is_available:
            self.__listen_events()

            self.__sync_kb_layout()
            self.__sync_workspaces()
            self.__sync_active_window()
            self.__sync_active_output()

    @GObject.Property
    def is_available(self) -> bool:
        """
        - read-only

        Whether Niri IPC is available.
        """
        if NIRI_SOCKET is not None:
            return os.path.exists(NIRI_SOCKET)
        else:
            return False

    @GObject.Property
    def workspaces(self) -> list[dict[str, Any]]:
        """
        - read-only

        A list of workspaces.
        """
        return self._workspaces

    @GObject.Property
    def active_workspaces(self) -> list[dict[str, Any]]:
        """
        - read-only

        The currently active workspaces.
        """
        return self._active_workspaces

    @GObject.Property
    def kb_layout(self) -> str:
        """
        - read-only

        The currenly active keyboard layout.
        """
        return self._kb_layout

    @GObject.Property
    def active_window(self) -> dict[str, Any]:
        """
        - read-only

        The currenly focused window.
        """
        return self._active_window

    @GObject.Property
    def active_output(self) -> dict[str, Any]:
        """
        - read-only

        The currenly focused output.
        """
        return self._active_output

    @Utils.run_in_thread
    def __listen_events(self) -> None:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.connect(str(NIRI_SOCKET))
            sock.send(b'"EventStream"\n')
            for event in Utils.listen_socket(sock):
                self.__on_event_received(event)

    def __on_event_received(self, event: str) -> None:
        try:
            eventtype = list(json.loads(event).keys())[0]
            if eventtype.startswith("WorkspaceActivated") or eventtype.startswith(
                "WorkspacesChanged"
            ):
                self.__sync_workspaces()
            elif eventtype.startswith("KeyboardLayoutsChanged") or eventtype.startswith(
                "KeyboardLayoutSwitched"
            ):
                self.__sync_kb_layout()

            elif eventtype.startswith(
                "WorkspaceActiveWindowChanged"
            ) or eventtype.startswith("WindowFocusChanged"):
                self.__sync_active_window()
                self.__sync_active_output()
            elif eventtype.startswith("WindowOpenedOrChanged"):
                self.__sync_active_window()

        except KeyError:
            logger.warning(f"[Niri Service] non matching event: {event}")

    def __sync_workspaces(self) -> None:
        w = json.loads(self.send_command('"Workspaces"\n'))["Ok"]["Workspaces"]
        self._workspaces = sorted(w, key=lambda x: x["idx"])
        self._active_workspaces = list(filter(lambda w: w["is_active"], w))
        self.notify("workspaces")
        self.notify("active-workspaces")

    def __sync_kb_layout(self) -> None:
        k = json.loads(self.send_command('"KeyboardLayouts"\n'))["Ok"][
            "KeyboardLayouts"
        ]
        self._kb_layout = k["names"][k["current_idx"]]
        self.notify("kb-layout")

    def __sync_active_window(self) -> None:
        self._active_window = json.loads(self.send_command('"FocusedWindow"\n'))["Ok"][
            "FocusedWindow"
        ]
        self.notify("active-window")

    def __sync_active_output(self) -> None:
        self._active_output = json.loads(self.send_command('"FocusedOutput"\n'))["Ok"][
            "FocusedOutput"
        ]
        self.notify("active-output")

    def send_command(self, cmd: str) -> str:
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
            return Utils.send_socket(sock, cmd)

    def switch_kb_layout(self) -> None:
        """
        Switch to the next keyboard layout.
        """
        self.send_command('{"Action":{"SwitchLayout":{"layout":"Next"}}}\n')

    def switch_to_workspace(self, workspace_id: int) -> None:
        """
        Switch to a workspace by its ID.

        Args:
            workspace_id: The ID of the workspace to switch to.
        """
        cmd = {"Action": {"FocusWorkspace": {"reference": {"Index": workspace_id}}}}
        self.send_command(json.dumps(cmd) + "\n")
