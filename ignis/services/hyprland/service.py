import json
import os
import socket
from typing import Any, Literal
from ignis import utils
from ignis.exceptions import HyprlandIPCNotFoundError
from ignis.base_service import BaseService
from ignis.gobject import IgnisProperty, IgnisSignal
from collections.abc import Callable
from dataclasses import dataclass
from .constants import HYPR_SOCKET_DIR
from .workspace import HyprlandWorkspace
from .keyboard import HyprlandKeyboard
from .window import HyprlandWindow
from .monitor import HyprlandMonitor


@dataclass
class _HyprlandObjDesc:
    cmd: str
    cr_func: Callable
    get_key_func: Callable
    added_signal: str
    destroy_signal: str
    prop_name: str
    sort_func: Callable | None = None


_SupportedTypes = Literal["workspace", "window", "monitor"]


class HyprlandService(BaseService):
    """
    Hyprland IPC client.

    Example usage:

    .. code-block:: python

        from ignis.services.hyprland import HyprlandService

        hyprland = HyprlandService.get_default()

        # Get IDs of all workspaces
        print([i.id for i in hyprland.workspaces])

        # Get the ID of the active workspace
        print(hyprland.active_workspace.id)

        # Get the currently active keyboard layout
        print(hyprland.main_keyboard.active_keymap)

        # Get the title of the active window
        print(hyprland.active_window.title)
    """

    def __init__(self):
        super().__init__()

        self._workspaces: dict[int, HyprlandWorkspace] = {}
        self._active_workspace: HyprlandWorkspace = HyprlandWorkspace(self)
        self._main_keyboard: HyprlandKeyboard = HyprlandKeyboard(self)
        self._windows: dict[str, HyprlandWindow] = {}
        self._active_window: HyprlandWindow = HyprlandWindow()
        self._monitors: dict[str, HyprlandMonitor] = {}

        self._OBJ_TYPES: dict[str, _HyprlandObjDesc] = {
            "workspace": _HyprlandObjDesc(
                cmd="j/workspaces",
                cr_func=lambda: HyprlandWorkspace(self),
                get_key_func=lambda data: data["id"],
                added_signal="workspace-added",
                destroy_signal="destroyed",
                prop_name="workspaces",
                sort_func=self.__sort_workspaces,
            ),
            "window": _HyprlandObjDesc(
                cmd="j/clients",
                cr_func=lambda: HyprlandWindow(),
                get_key_func=lambda data: data["address"],
                added_signal="window-added",
                destroy_signal="closed",
                prop_name="windows",
            ),
            "monitor": _HyprlandObjDesc(
                cmd="j/monitors",
                cr_func=lambda: HyprlandMonitor(),
                get_key_func=lambda data: data["name"],
                added_signal="monitor-added",
                destroy_signal="removed",
                prop_name="monitors",
            ),
        }

        if self.is_available:
            self.__listen_events()

            self.__initial_sync_obj_list(type_="workspace")
            self.__sync_active_workspace()
            self.__sync_main_keyboard()
            self.__sync_active_window()
            self.__initial_sync_obj_list(type_="window")
            self.__initial_sync_obj_list(type_="monitor")

    @IgnisSignal
    def workspace_added(self, workspace: HyprlandWorkspace):
        """
        Emitted when a new workspace has been added.

        Args:
            workspace: The instance of the workspace.
        """

    @IgnisSignal
    def window_added(self, window: HyprlandWindow):
        """
        Emitted when a new window has been added.

        Args:
            window: The instance of the window.
        """

    @IgnisSignal
    def monitor_added(self, monitor: HyprlandMonitor):
        """
        Emitted when a new monitor has been added.

        Args:
            monitor: The instance of the monitor.
        """

    @IgnisProperty
    def is_available(self) -> bool:
        """
        Whether Hyprland IPC is available.
        """
        return os.path.exists(HYPR_SOCKET_DIR)

    @IgnisProperty
    def workspaces(self) -> list[HyprlandWorkspace]:
        """
        A list of workspaces.
        """
        return list(self._workspaces.values())

    @IgnisProperty
    def urgent_windows(self) -> list[HyprlandWindow]:
        """
        A list of urgent windows.
        """
        return [i for i in self._windows.values() if i.is_urgent]

    @IgnisProperty
    def urgent_workspaces(self) -> list[HyprlandWorkspace]:
        """
        A list of urgent workspaces.
        """
        return [i for i in self._workspaces.values() if i.is_urgent]

    @IgnisProperty
    def active_workspace(self) -> HyprlandWorkspace:
        """
        The currently active workspace.
        """
        return self._active_workspace

    @IgnisProperty
    def main_keyboard(self) -> HyprlandKeyboard:
        """
        The main keyboard.
        """
        return self._main_keyboard

    @IgnisProperty
    def windows(self) -> list[HyprlandWindow]:
        """
        A list of windows.
        """
        return list(self._windows.values())

    @IgnisProperty
    def active_window(self) -> HyprlandWindow:
        """
        The currenly focused window.
        """
        return self._active_window

    @IgnisProperty
    def monitors(self) -> list[HyprlandMonitor]:
        """
        A list of monitors.
        """
        return list(self._monitors.values())

    @utils.run_in_thread
    def __listen_events(self) -> None:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.connect(f"{HYPR_SOCKET_DIR}/.socket2.sock")
            for event in utils.listen_socket(sock, errors="ignore"):
                self.__on_event_received(event)

    def __on_event_received(self, event: str) -> None:
        def get_full_w_addr(addr: str) -> str:
            return "0x" + addr

        event_data = event.split(">>", 1)
        event_type, event_value = event_data
        value_list = event_value.split(",")

        match event_type:
            case "urgent":
                self.__sync_urgent(get_full_w_addr(value_list[0]))
            case "destroyworkspacev2":
                self.__destroy_workspace(int(value_list[0]))
            case "createworkspacev2":
                self.__create_workspace(int(value_list[0]))
            case "workspace":
                self.__sync_active_workspace()
                self.__sync_monitor_active_ws()
            case "focusedmon":
                self.__sync_active_workspace()
            case "activelayout":
                self.__sync_active_layout(value_list[1])
            case "activewindow":
                self.__sync_active_window()
            case "renameworkspace":
                self.__rename_workspace(int(value_list[0]), value_list[1])
            case "openwindow":
                self.__open_window(get_full_w_addr(value_list[0]))
            case "closewindow":
                self.__close_window(get_full_w_addr(value_list[0]))
            case "movewindowv2":
                self.__move_window(
                    get_full_w_addr(value_list[0]), int(value_list[1]), value_list[0]
                )
            case "changefloatingmode":
                self.__change_window_floating_mode(
                    get_full_w_addr(value_list[0]), int(value_list[1])
                )
            case "windowtitlev2":
                # window title can contain comma (,)
                value_list = event_value.split(",", 1)
                self.__change_window_title(
                    get_full_w_addr(value_list[0]), value_list[1]
                )
            case "pin":
                self.__change_window_pin_state(
                    get_full_w_addr(value_list[0]), int(value_list[1])
                )
            case "monitoradded":
                self.__add_monitor(value_list[0])
            case "monitorremoved":
                self.__remove_monitor(value_list[0])
            case "focusedmonv2":
                self.__change_focused_monitor(value_list[0], int(value_list[1]))
            case "activespecialv2":
                if value_list[0] == "":
                    ws_id = 0
                else:
                    ws_id = int(value_list[0])

                self.__change_special_ws_on_monitor(ws_id, value_list[1], value_list[2])
            case "moveworkspacev2":
                self.__move_workspace(int(value_list[0]), value_list[2])
            case "togglegroup":
                self.__toggle_window_group(int(value_list[0]), value_list[1].split(","))
                self.__sync_active_window()
            case "fullscreen":
                self.__sync_active_window()

    def __get_self_dict(self, obj_desc: _HyprlandObjDesc) -> dict:
        return getattr(self, f"_{obj_desc.prop_name}")

    def __initial_sync_obj_list(self, type_: _SupportedTypes) -> None:
        obj_desc = self._OBJ_TYPES[type_]

        data_list = json.loads(self.send_command(obj_desc.cmd))

        for data in data_list:
            obj = obj_desc.cr_func()
            obj.sync(data)
            self.__get_self_dict(obj_desc)[obj_desc.get_key_func(data)] = obj

        if obj_desc.sort_func:
            obj_desc.sort_func()

        self.notify(obj_desc.prop_name)

    def __get_obj_data(self, type_: _SupportedTypes, key: Any) -> dict:
        obj_desc = self._OBJ_TYPES[type_]

        for data in json.loads(self.send_command(obj_desc.cmd)):
            if obj_desc.get_key_func(data) == key:
                return data

        return {}

    def __add_obj(self, type_: _SupportedTypes, key: Any) -> None:
        obj_desc = self._OBJ_TYPES[type_]

        data = self.__get_obj_data(type_=type_, key=key)

        if data == {}:
            return

        obj = obj_desc.cr_func()
        obj.sync(data)

        self.__get_self_dict(obj_desc)[obj_desc.get_key_func(data)] = obj
        if obj_desc.sort_func:
            obj_desc.sort_func()

        self.emit(obj_desc.added_signal, obj)
        self.notify(obj_desc.prop_name)

    def __remove_obj(self, type_: _SupportedTypes, key: Any) -> None:
        obj_desc = self._OBJ_TYPES[type_]

        obj = self.__get_self_dict(obj_desc).pop(key, None)
        if obj:
            obj.emit(obj_desc.destroy_signal)

            if obj_desc.sort_func:
                obj_desc.sort_func()

            self.notify(obj_desc.prop_name)

    def __sync_obj_data(
        self, type_: _SupportedTypes, key: Any, data: dict[str, Any]
    ) -> None:
        obj_desc = self._OBJ_TYPES[type_]

        obj = self.__get_self_dict(obj_desc).get(key, None)
        if obj:
            obj.sync(data)

    def __create_workspace(self, id_: int) -> None:
        self.__add_obj(type_="workspace", key=id_)

    def __destroy_workspace(self, id_: int) -> None:
        self.__remove_obj(type_="workspace", key=id_)

    def __rename_workspace(self, workspace_id: int, new_name: str) -> None:
        self.__sync_obj_data("workspace", workspace_id, {"name": new_name})

    def __move_workspace(self, workspace_id: int, monitor_name: str) -> None:
        monitor_obj = self.get_monitor_by_name(monitor_name)

        if monitor_obj:
            self.__sync_obj_data(
                "workspace",
                workspace_id,
                {"monitor": monitor_name, "monitor_id": monitor_obj.id},
            )

    def __sort_workspaces(self) -> None:
        self._workspaces = dict(sorted(self._workspaces.items()))

    def __sync_active_workspace(self) -> None:
        workspace_data = json.loads(self.send_command("j/activeworkspace"))
        self._active_workspace.sync(workspace_data)
        self.notify("active-workspace")

    def __sync_main_keyboard(self) -> None:
        data_list = json.loads(self.send_command("j/devices"))["keyboards"]

        for kb_data in data_list:
            if kb_data["main"] is True:
                self._main_keyboard.sync(kb_data)

        self.notify("main-keyboard")

    def __sync_active_layout(self, layout: str) -> None:
        self._main_keyboard.sync({"active_keymap": layout})

    def __sync_urgent(self, urgent_window) -> None:
        if urgent_window in self._windows:
            self._windows[urgent_window]._urgent = True
            self.notify("urgent_windows")
            self.notify("urgent_workspaces")

    def __sync_active_window(self) -> None:
        active_window_data = json.loads(self.send_command("j/activewindow"))
        if active_window_data == {}:
            active_window_data = HyprlandWindow().data

        self.active_window.sync(active_window_data)

        active_window_id = active_window_data["address"]
        if (
            active_window_id in self._windows
            and self._windows[active_window_id]._urgent
        ):
            self._windows[active_window_id]._urgent = False
            self.notify("urgent_windows")
            self.notify("urgent_workspaces")

        self.notify("active-window")

    def __open_window(self, address: str) -> None:
        self.__add_obj(type_="window", key=address)

    def __close_window(self, address: str) -> None:
        self.__remove_obj(type_="window", key=address)

    def __move_window(
        self, address: str, workspace_id: int, workspace_name: str
    ) -> None:
        self.__sync_obj_data(
            type_="window",
            key=address,
            data={"workspace": {"id": workspace_id, "name": workspace_name}},
        )

    def __change_window_floating_mode(self, address: str, floating: int) -> None:
        self.__sync_obj_data(
            type_="window", key=address, data={"floating": bool(floating)}
        )

    def __change_window_title(self, address: str, title: str) -> None:
        self.__sync_obj_data(type_="window", key=address, data={"title": title})

    def __change_window_pin_state(self, address: str, pin_state: int) -> None:
        self.__sync_obj_data(
            type_="window",
            key=address,
            data={"title": {"pinned": bool(pin_state)}},
        )

    def __toggle_window_group(self, state: int, addresses: list[str]) -> None:
        # To be honest, I can't understand at all how these window groups work
        # For some reason IPC always sends only one window address
        # even if there are several windows in a group (I add them there with the mouse, maybe that's the problem...)
        for addr in addresses:
            self.__sync_obj_data("window", addr, self.__get_obj_data("window", addr))

    def __add_monitor(self, monitor_name: str) -> None:
        self.__add_obj(type_="monitor", key=monitor_name)

    def __remove_monitor(self, monitor_name: str) -> None:
        self.__remove_obj(type_="monitor", key=monitor_name)

    def __sync_monitor_active_ws(self) -> None:
        self.__sync_obj_data(
            type_="monitor",
            key=self.active_workspace.monitor,
            data={
                "activeWorkspace": {
                    "id": self.active_workspace.id,
                    "name": self.active_workspace.name,
                }
            },
        )

    def __change_focused_monitor(self, monitor_name: str, workspace_id: int) -> None:
        ws = self.get_workspace_by_id(workspace_id)
        name = ws.name if ws else ""
        self.__sync_obj_data(
            type_="monitor",
            key=monitor_name,
            data={"activeWorkspace": {"id": workspace_id, "name": name}},
        )

    def __change_special_ws_on_monitor(
        self, workspace_id: int, workspace_name: str, monitor_name: str
    ) -> None:
        self.__sync_obj_data(
            type_="monitor",
            key=monitor_name,
            data={"specialWorkspace": {"id": workspace_id, "name": workspace_name}},
        )

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
            return utils.send_socket(sock, cmd, errors="ignore")

    def switch_to_workspace(self, workspace_id: int) -> None:
        """
        Switch to a workspace by its ID.

        Args:
            workspace_id: The ID of the workspace to switch to.
        """
        self.send_command(f"dispatch workspace {workspace_id}")

    def get_workspace_by_id(self, workspace_id: int) -> HyprlandWorkspace | None:
        """
        Get a workspace by its ID.

        Args:
            workspace_id: The ID of the workspace.
        Returns:
            The workspace instance, or ``None`` if the workspace with the given ID doesn't exist.
        """
        return self._workspaces.get(workspace_id, None)

    def get_window_by_address(self, address: str) -> HyprlandWindow | None:
        """
        Get a window by its address.

        Args:
            address: The address of the window.
        Returns:
            The window instance, or ``None`` if the window with the given address doesn't exist.
        """
        return self._windows.get(address, None)

    def get_monitor_by_name(self, name: str) -> HyprlandMonitor | None:
        """
        Get a monitor by its name.

        Args:
            name: The name of the monitor.
        Returns:
            The monitor instance, or ``None`` if the monitor with the given name doesn't exist.
        """
        return self._monitors.get(name, None)

    def get_windows_on_workspace(self, workspace_id: int) -> list[HyprlandWindow]:
        """
        Get a list of windows on a workspace by its ID.

        Args:
            workspace_id: The ID of the workspace.

        Returns:
            A list of windows on the workspace.
        """
        return [
            window
            for window in self._windows.values()
            if window.workspace_id == workspace_id
        ]
