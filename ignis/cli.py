import os
import click
import subprocess
import collections
from ignis.client import IgnisClient
from ignis import utils
from ignis.exceptions import WindowNotFoundError
from typing import Any
from gi.repository import GLib  # type: ignore
from ignis import is_editable_install

DEFAULT_CONFIG_PATH = f"{GLib.get_user_config_dir()}/ignis/config.py"


class OrderedGroup(click.Group):
    def __init__(self, name=None, commands=None, **attrs):
        super().__init__(name, commands, **attrs)
        self.commands = commands or collections.OrderedDict()

    def list_commands(self, ctx):
        return self.commands


def _run_git_cmd(args: str) -> str | None:
    try:
        repo_dir = os.path.abspath(os.path.join(__file__, "../.."))
        commit_hash = subprocess.run(
            f"git -C {repo_dir} {args}",
            shell=True,
            text=True,
            capture_output=True,
        ).stdout.strip()

        return commit_hash
    except subprocess.CalledProcessError:
        return None


def get_version_message() -> str:
    if not is_editable_install:
        return f"""Ignis {utils.get_ignis_version()}
Branch: {utils.get_ignis_branch()}
Commit: {utils.get_ignis_commit()} ({utils.get_ignis_commit_msg()})"""
    else:
        commit = _run_git_cmd("rev-parse HEAD")
        branch = _run_git_cmd("branch --show-current")
        commit_msg = _run_git_cmd("log -1 --pretty=%B")
        return f"""Ignis {utils.get_ignis_version()}
Editable install
Branch: {branch}
Commit: {commit} ({commit_msg})

Version at the moment of the installation:
Branch: {utils.get_ignis_branch()}
Commit: {utils.get_ignis_commit()} ({utils.get_ignis_commit_msg()})
"""


def get_systeminfo() -> str:
    current_desktop = os.getenv("XDG_CURRENT_DESKTOP")
    with open("/etc/os-release") as file:
        os_release = file.read().strip()

    return f"""{get_version_message()}
Current desktop: {current_desktop}

os-release:
{os_release}"""


def print_version(ctx, param, value):
    if value:
        ctx.exit(print(get_version_message()))


def call_client_func(name: str, *args) -> Any:
    client = IgnisClient()
    if not client.has_owner:
        print("Ignis is not running.")
        exit(1)

    try:
        return getattr(client, name)(*args)
    except WindowNotFoundError:
        print(f"No such window: {args[0]}")
        exit(1)


def get_full_path(path: str) -> str:
    return os.path.abspath(os.path.expanduser(path))


@click.group(
    cls=OrderedGroup,
    help="A widget framework for building desktop shells, written and configurable in Python.",
)
@click.option(
    "--version",
    is_flag=True,
    callback=print_version,
    expose_value=False,
    is_eager=True,
    help="Print the version and exit.",
)
def cli():
    pass


@cli.command(name="init", help="Initialize Ignis.")
@click.option(
    "--config",
    "-c",
    help="Path to the configuration file (default: ~/.config/ignis/config.py).",
    default=DEFAULT_CONFIG_PATH,
    type=str,
    metavar="PATH",
)
@click.option("--debug", help="Print debug information to the terminal.", is_flag=True)
def init(config: str, debug: bool) -> None:
    from ignis.app import IgnisApp
    from ignis.log_utils import configure_logger
    from ignis._deprecation import _enable_deprecation_warnings
    from ignis.config_manager import ConfigManager

    client = IgnisClient()

    if client.has_owner:
        print("Ignis is already running.")
        exit(1)

    config_path = get_full_path(config)

    _enable_deprecation_warnings()
    configure_logger(debug)

    app = IgnisApp.get_default()

    app.connect(
        "activate",
        lambda x: ConfigManager.get_default()._load_config(app=x, path=config_path),
    )

    try:
        app.run(None)
    except KeyboardInterrupt:
        pass


@cli.command(name="open-window", help="Open a window.")
@click.argument("window_name")
def open_window(window_name: str) -> None:
    call_client_func("open_window", window_name)


@cli.command(name="close-window", help="Close a window.")
@click.argument("window_name")
def close(window_name: str) -> None:
    call_client_func("close_window", window_name)


@cli.command(name="toggle-window", help="Toggle a window.")
@click.argument("window_name")
def toggle(window_name: str) -> None:
    call_client_func("toggle_window", window_name)


@cli.command(name="list-windows", help="List names of all windows.")
def list_windows() -> None:
    window_list = call_client_func("list_windows")
    print("\n".join(window_list))


@cli.command(
    name="run-python", help="Execute a Python code inside the running Ignis process."
)
@click.argument("code")
def run_python(code: str) -> None:
    call_client_func("run_python", code)


@cli.command(
    name="run-file", help="Execute a Python file inside the running Ignis process."
)
@click.argument("file")
def run_file(file: str) -> None:
    call_client_func("run_file", get_full_path(file))


@cli.command(name="inspector", help="Open GTK Inspector.")
def inspector() -> None:
    call_client_func("inspector")


@cli.command(name="reload", help="Reload Ignis.")
def reload() -> None:
    call_client_func("reload")


@cli.command(name="quit", help="Quit Ignis.")
def quit() -> None:
    call_client_func("quit")


@cli.command(name="systeminfo", help="Print system information.")
def systeminfo() -> None:
    print(get_systeminfo())
