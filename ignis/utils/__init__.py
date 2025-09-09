from typing import TypeAlias
from .debounce import DebounceTask, debounce
from .file_monitor import FileMonitor
from .file import read_file, read_file_async, write_file, write_file_async
from .icon import get_paintable, get_file_icon_name, get_app_icon_name
from .misc import load_interface_xml, get_current_dir, get_gdk_display, open_inspector
from .monitor import get_monitor, get_n_monitors, get_monitors
from .pixbuf import scale_pixbuf, crop_pixbuf
from .poll import Poll
from .sass import sass_compile
from .shell import exec_sh, exec_sh_async, AsyncCompletedProcess
from .socket import send_socket, listen_socket
from .str_cases import snake_to_pascal, pascal_to_snake
from .thread import thread, run_in_thread, ThreadTask
from .timeout import Timeout
from .version import (
    get_ignis_version,
    get_ignis_commit,
    get_ignis_branch,
    get_ignis_commit_msg,
)
from ignis._deprecation import deprecated_getattribute


@deprecated_getattribute(
    """The "Utils" class is deprecated, please use "from ignis import utils" instead."""
)
class Utils:
    exec_sh = exec_sh
    exec_sh_async = exec_sh_async
    AsyncCompletedProcess: TypeAlias = AsyncCompletedProcess
    load_interface_xml = load_interface_xml
    Poll: TypeAlias = Poll
    get_monitor = get_monitor
    get_n_monitors = get_n_monitors
    Timeout: TypeAlias = Timeout
    FileMonitor: TypeAlias = FileMonitor
    thread = thread
    run_in_thread = run_in_thread
    sass_compile = sass_compile
    get_ignis_version = get_ignis_version
    scale_pixbuf = scale_pixbuf
    crop_pixbuf = crop_pixbuf
    get_paintable = get_paintable
    get_file_icon_name = get_file_icon_name
    ThreadTask: TypeAlias = ThreadTask
    get_ignis_commit = get_ignis_commit
    get_current_dir = get_current_dir
    get_ignis_branch = get_ignis_branch
    get_ignis_commit_msg = get_ignis_commit_msg
    send_socket = send_socket
    listen_socket = listen_socket
    DebounceTask = DebounceTask
    debounce = debounce
    get_monitors = get_monitors
    snake_to_pascal = snake_to_pascal
    pascal_to_snake = pascal_to_snake
    read_file = read_file
    read_file_async = read_file_async
    write_file = write_file
    write_file_async = write_file_async
    get_app_icon_name = get_app_icon_name


__all__ = [
    "AsyncCompletedProcess",
    "DebounceTask",
    "FileMonitor",
    "Poll",
    "ThreadTask",
    "Timeout",
    "crop_pixbuf",
    "debounce",
    "exec_sh",
    "exec_sh_async",
    "get_app_icon_name",
    "get_current_dir",
    "get_file_icon_name",
    "get_ignis_branch",
    "get_ignis_commit",
    "get_ignis_commit_msg",
    "get_ignis_version",
    "get_monitor",
    "get_monitors",
    "get_n_monitors",
    "get_paintable",
    "get_gdk_display",
    "listen_socket",
    "load_interface_xml",
    "pascal_to_snake",
    "read_file",
    "read_file_async",
    "run_in_thread",
    "sass_compile",
    "scale_pixbuf",
    "send_socket",
    "snake_to_pascal",
    "thread",
    "write_file",
    "write_file_async",
    "open_inspector",
]
