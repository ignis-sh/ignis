import os
import re
import asyncio
import subprocess
from gi.repository import GLib, GioUnix  # type: ignore
from ignis.gobject import IgnisGObject, IgnisProperty, IgnisSignal
from ignis.options import options
from .action import ApplicationAction


class Application(IgnisGObject):
    """
    An application object.
    """

    def __init__(self, app: GioUnix.DesktopAppInfo):
        super().__init__()

        self._app = app
        self._actions: list[ApplicationAction] = []

        for action in app.list_actions():
            self._actions.append(ApplicationAction(app=app, action=action))

    @IgnisSignal
    def pinned(self):
        """
        Emitted when the application has been pinned.
        """

    @IgnisSignal
    def unpinned(self):
        """
        Emitted when the application has been unpinned.
        """

    @IgnisProperty
    def app(self) -> GioUnix.DesktopAppInfo:
        """
        An instance of :class:`GioUnix.DesktopAppInfo`.
        """
        return self._app

    @IgnisProperty
    def id(self) -> str | None:
        """
        The ID of the application.
        """
        return self._app.get_id()

    @IgnisProperty
    def name(self) -> str:
        """
        The name of the application.
        """
        return self._app.get_display_name()

    @IgnisProperty
    def description(self) -> str | None:
        """
        The description of the application.
        """
        return self._app.get_description()

    @IgnisProperty
    def icon(self) -> str:
        """
        The icon of the application. If the app has no icon, "image-missing" will be returned.
        """
        icon = self._app.get_string("Icon")
        if not icon:
            return "image-missing"
        else:
            return icon

    @IgnisProperty
    def keywords(self) -> list[str]:
        """
        Keywords of the application. Ususally, these are words that describe the application.
        """
        return self._app.get_keywords()

    @IgnisProperty
    def desktop_file(self) -> str | None:
        """
        The full path to the ``.desktop`` file of the application.
        """
        return self._app.get_filename()

    @IgnisProperty
    def executable(self) -> str:
        """
        The executable of the application.
        """
        return self._app.get_executable()

    @IgnisProperty
    def exec_string(self) -> str | None:
        """
        The string that contains the executable with command line arguments, used to launch the application.
        """
        return self._app.get_string("Exec")

    @IgnisProperty
    def actions(self) -> list[ApplicationAction]:
        """
        A list of actions.
        """
        return self._actions

    @IgnisProperty
    def is_pinned(self) -> bool:
        """
        Whether the application is pinned.
        """
        return self.id in options.applications.pinned_apps

    @is_pinned.setter
    def is_pinned(self, value: bool) -> None:
        if value == self.is_pinned:
            return

        opt = options.applications.pinned_apps
        if value:
            opt.append(self.id)
            self.emit("pinned")
        else:
            opt.remove(self.id)
            self.emit("unpinned")

    @IgnisProperty
    def is_terminal(self) -> bool:
        """
        Whether the application has to be launched in a terminal.
        """
        return {"true": True, "false": False, None: False}.get(
            self._app.get_string("Terminal"), False
        )

    def pin(self) -> None:
        """
        Pin the application.
        """
        self.is_pinned = True

    def unpin(self) -> None:
        """
        Unpin the application.
        """
        self.is_pinned = False

    def launch(
        self, command_format: str | None = None, terminal_format: str | None = None
    ) -> None:
        """
        Launch the application.

        Args:
            command_format: A format string for the command to launch. ``%command%`` will be replaced with the actual command. Shell syntax is supported.
            terminal_format: A format string for the command to launch if the application has to be run in a terminal. ``%command%`` will be replaced with the actual command. Shell syntax is supported.

        To launch terminal applications, pass the ``terminal_format`` argument:

        .. code-block:: python

            # kitty for example, format may differ for other terminals
            APPLICATION.launch(terminal_format="kitty %command%")
        """
        exec_string = re.sub(r"%\S*", "", self.exec_string)
        custom_env = os.environ.copy()

        # Disable Python virtual environment
        custom_env.pop("VIRTUAL_ENV", None)
        custom_env.pop("PYTHONHOME", None)
        custom_env.pop("PYTHONPATH", None)

        cmd: str

        if self.is_terminal is True and terminal_format is not None:
            cmd = terminal_format.replace("%command%", exec_string)
        elif command_format is not None:
            cmd = command_format.replace("%command%", exec_string)
        else:
            cmd = exec_string

        # FIXME: add logging for stdout & stderr
        asyncio.create_task(
            asyncio.create_subprocess_shell(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                cwd=GLib.get_home_dir(),
                env=custom_env,
                preexec_fn=os.setsid,  # create new session
            )
        )

    def launch_uwsm(self) -> None:
        """
        Launch the application using UWSM (Universal Wayland Session Manager).
        """
        self.launch(command_format="uwsm app -- %command%")
