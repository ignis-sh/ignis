import os
from gi.repository import Gio  # type: ignore
from ignis.gobject import IgnisGObject, IgnisProperty, IgnisSignal
from collections.abc import Callable

EVENT = {
    Gio.FileMonitorEvent.CHANGED: "changed",
    Gio.FileMonitorEvent.CHANGES_DONE_HINT: "changes_done_hint",
    Gio.FileMonitorEvent.MOVED_OUT: "moved_out",
    Gio.FileMonitorEvent.DELETED: "deleted",
    Gio.FileMonitorEvent.CREATED: "created",
    Gio.FileMonitorEvent.ATTRIBUTE_CHANGED: "attribute_changed",
    Gio.FileMonitorEvent.PRE_UNMOUNT: "pre_unmount",
    Gio.FileMonitorEvent.UNMOUNTED: "unmounted",
    Gio.FileMonitorEvent.MOVED: "moved",
    Gio.FileMonitorEvent.RENAMED: "renamed",
    Gio.FileMonitorEvent.MOVED_IN: "moved_in",
}

file_monitors = []


class FileMonitor(IgnisGObject):
    """
    Monitor changes of the file or directory.

    Args:
        path: The path to the file or directory to be monitored.
        recursive: Whether monitoring is recursive (monitor all subdirectories and files).
        flags: What the monitor will watch for. See :class:`Gio.FileMonitorFlags` for more info.
        callback: A function to call when the file or directory changes. See :attr:`callback` for more info.
        prevent_gc: Whether to prevent the garbage collector from collecting this file monitor.

    Example usage:

    .. code-block::

        utils.FileMonitor(
            path="path/to/something",
            recursive=False,
            callback=lambda path, event_type: print(path, event_type),
        )
    """

    def __init__(
        self,
        path: str,
        recursive: bool = False,
        flags: Gio.FileMonitorFlags = Gio.FileMonitorFlags.NONE,
        callback: Callable | None = None,
        prevent_gc: bool = True,
    ):
        super().__init__()
        self._file = Gio.File.new_for_path(path)
        self._monitor = self._file.monitor(flags, None)
        self._monitor.connect("changed", self.__on_change)

        self._path = path
        self._flags = flags
        self._callback = callback
        self._recursive = recursive
        self._prevent_gc = prevent_gc

        self._sub_monitors: list[Gio.FileMonitor] = []
        self._sub_paths: list[str] = []

        if recursive:
            for root, dirs, _files in os.walk(path):
                for d in dirs:
                    subdir_path = os.path.join(root, d)
                    self.__add_submonitor(subdir_path)

        if prevent_gc:
            file_monitors.append(self)

        self.connect(
            "changed", lambda *args: self._callback(*args) if self._callback else None
        )

    @IgnisSignal
    def changed(self, path: str, event_type: str):
        """
        Emitted when the file or directory changed.

        Args:
            path: The path to the changed file or directory.
            event_type: The event type. A list of all event types described in :attr:`callback`.
        """
        pass

    def __on_change(self, file_monitor, file, other_file, event_type) -> None:
        path = file.get_path()
        self.emit("changed", path, EVENT[event_type])

        if self.recursive and os.path.isdir(path):
            self.__add_submonitor(path)

    def __add_submonitor(self, path: str) -> None:
        if path in self._sub_paths:
            return

        sub_gfile = Gio.File.new_for_path(path)
        monitor = sub_gfile.monitor(self.flags, None)
        monitor.connect("changed", self.__on_change)
        self._sub_monitors.append(monitor)
        self._sub_paths.append(path)

    @IgnisProperty
    def path(self) -> str:
        """
        The path to the file or directory to be monitored.
        """
        return self._path

    @IgnisProperty
    def flags(self) -> Gio.FileMonitorFlags:
        """
        What the monitor will watch for.

        See :class:`Gio.FileMonitorFlags` for more info.
        """
        return self._flags

    @IgnisProperty
    def callback(self) -> Callable | None:
        """
        A function to call when the file or directory changes.
        It should take two arguments:
        1. The path to the changed file or directory
        2. The event type.

        Event types:

        - changed
        - changes_done_hint
        - moved_out
        - deleted
        - created
        - attribute_changed
        - pre_unmount
        - unmounted
        - moved
        - renamed
        - moved_in

        See :class:`Gio.FileMonitorEvent` for more info.

        """
        return self._callback

    @callback.setter
    def callback(self, value: Callable) -> None:
        self._callback = value

    @IgnisProperty
    def recursive(self) -> bool:
        """
        Whether monitoring is recursive (monitor all subdirectories and files).
        """
        return self._recursive

    @IgnisProperty
    def prevent_gc(self) -> bool:
        """
        Whether to prevent the garbage collector from collecting this file monitor.
        """
        return self._prevent_gc

    def cancel(self) -> None:
        """
        Cancel the monitoring process.
        """
        self._monitor.cancel()
