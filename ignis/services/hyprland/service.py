import json
import os
import socket
from gi.repository import GObject  # type: ignore
from ignis.utils import Utils
from typing import Any
from ignis.exceptions import HyprlandIPCNotFoundError
from ignis.base_service import BaseService
from .constants import HYPR_SOCKET_DIR


class HyprlandService(BaseService):
    """
    Hyprland IPC client.

    .. note::
        The contents of ``dict`` properties are not described here.
        To find out their contents just print them into the terminal.

        >>> print(hyprland.workspaces)
        [
            {
                "id": 1,
                "name": "1",
                "monitor": "DP-1",
                "monitorID": 1,
                "windows": 1,
                "hasfullscreen": False,
                "lastwindow": "0x561dc35d2e80",
                "lastwindowtitle": "hyprland.py - ignis - Visual Studio Code",
            },
            {
                "id": 10,
                "name": "10",
                "monitor": "HDMI-A-1",
                "monitorID": 0,
                "windows": 1,
                "hasfullscreen": False,
                "lastwindow": "0x561dc3845f30",
                "lastwindowtitle": "Type hints cheat sheet - mypy 1.11.2 documentation — Mozilla Firefox",
            },
        ]

        >>> print(hyprland.active_window)
        {
            "address": "0x561dc35d2e80",
            "mapped": True,
            "hidden": False,
            "at": [1942, 22],
            "size": [1876, 1036],
            "workspace": {"id": 1, "name": "1"},
            "floating": False,
            "pseudo": False,
            "monitor": 1,
            "class": "code-url-handler",
            "title": "hyprland.py - ignis - Visual Studio Code",
            "initialClass": "code-url-handler",
            "initialTitle": "Visual Studio Code",
            "pid": 1674,
            "xwayland": False,
            "pinned": False,
            "fullscreen": 0,
            "fullscreenClient": 0,
            "grouped": [],
            "tags": [],
            "swallowing": "0x0",
            "focusHistoryID": 0,
        }

    Example usage:

    .. code-block:: python

        from ignis.services.hyprland import HyprlandService

        hyprland = HyprlandService.get_default()

        print(hyprland.workspaces)
        print(hyprland.kb_layout)

        hyprland.connect("notify::kb-layout", lambda x, y: print(hyprland.kb_layout))
    """

    def __init__(self):
        super().__init__()

        self._workspaces: list[dict[str, Any]] = []
        self._active_workspace: dict[str, Any] = {}
        self._kb_layout: str = ""
        self._active_window: dict[str, Any] = {}
        self._urgent_windows: set[str] = set()

        if self.is_available:
            self.__listen_events()

            self.__sync_kb_layout()
            self.__sync_workspaces()
            self.__sync_active_window()

    @GObject.Property
    def is_available(self) -> bool:
        """
        - read-only

        Whether Hyprland IPC is available.
        """
        return os.path.exists(HYPR_SOCKET_DIR)

    @GObject.Property
    def workspaces(self) -> list[dict[str, Any]]:
        """
        - read-only

        A list of workspaces.
        """
        return self._workspaces

    @GObject.Property
    def urgent_windows(self) -> list[str]:
        """
        - read-only

        A list of urgent windows.
        """
        return list(self._urgent_windows)

    @GObject.Property
    def urgent_workspaces(self) -> list[str]:
        """
        - read-only

        A list of urgent workspaces.
        """
        clients = json.loads(self.send_command("j/clients"))
        urgent_workspaces = []
        for i in clients:
            if i["address"][len("0x"):] in self._urgent_windows:
                urgent_workspaces.append(i["workspace"]["id"])
        return urgent_workspaces

    @GObject.Property
    def active_workspace(self) -> dict[str, Any]:
        """
        - read-only

        The currently active workspace.
        """
        return self._active_workspace

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

    @Utils.run_in_thread
    def __listen_events(self) -> None:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.connect(f"{HYPR_SOCKET_DIR}/.socket2.sock")
            for event in Utils.listen_socket(sock, errors="ignore"):
                self.__on_event_received(event)

    def __on_event_received(self, event: str) -> None:
        if (
            event.startswith("workspace>>")
            or event.startswith("destroyworkspace>>")
            or event.startswith("focusedmon>>")
        ):
            self.__sync_workspaces()
        elif event.startswith("activelayout>>"):
            self.__sync_kb_layout()

        elif event.startswith("activewindow>>"):
            self.__sync_active_window()

        elif event.startswith("urgent>>"):
            self.__sync_urgent(event[len("urgent>>"):])

    def __sync_workspaces(self) -> None:
        self._workspaces = sorted(
            json.loads(self.send_command("j/workspaces")), key=lambda x: x["id"]
        )
        self._active_workspace = json.loads(self.send_command("j/activeworkspace"))
        self.notify("workspaces")
        self.notify("active-workspace")

    def __sync_kb_layout(self) -> None:
        for kb in json.loads(self.send_command("j/devices"))["keyboards"]:
            if kb["main"]:
                self._kb_layout = kb["active_keymap"]
                self.notify("kb_layout")

    def __sync_active_window(self) -> None:
        self._active_window = json.loads(self.send_command("j/activewindow"))
        if self._active_window:
            active_window_id = self._active_window["address"][len("0x"):]
            if active_window_id in self._urgent_windows:
                self._urgent_windows.remove(active_window_id)
        self.notify("active_window")
        self.notify("urgent_windows")
        self.notify("urgent_workspaces")

    def __sync_urgent(self, urgent_window) -> None:
        self._urgent_windows.add(urgent_window)
        self.notify("urgent_windows")
        self.notify("urgent_workspaces")

    def send_command(self, cmd: str) -> str:
        """
        Send a command to the Hyprland IPC.
        Supports the same commands as ``hyprctl``.
        If you want to receive the response in JSON format, use this syntax: ``j/COMMAND``.

        Args:
            cmd: The command to send.

        Returns:
            Response from Hyprland IPC.

        Raises:
            HyprlandIPCNotFoundError: If Hyprland IPC is not found.
        """
        if not self.is_available:
            raise HyprlandIPCNotFoundError()

        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.connect(f"{HYPR_SOCKET_DIR}/.socket.sock")
            return Utils.send_socket(sock, cmd, errors="ignore")

    def switch_kb_layout(self) -> None:
        """
        Switch to the next keyboard layout.
        """
        for kb in json.loads(self.send_command("j/devices"))["keyboards"]:
            if kb["main"]:
                self.send_command(f"switchxkblayout {kb['name']} next")

    def switch_to_workspace(self, workspace_id: int) -> None:
        """
        Switch to a workspace by its ID.

        Args:
            workspace_id: The ID of the workspace to switch to.
        """
        self.send_command(f"dispatch workspace {workspace_id}")
