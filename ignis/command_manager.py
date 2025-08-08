from collections.abc import Callable
from ignis.gobject import IgnisGObjectSingleton
from ignis.exceptions import CommandAddedError, CommandNotFoundError


CommandCallback = Callable[[list[str]], str | None]
"""
Callback type of a custom command.

Alias of ``Callable[[list[str]], str | None]``.

Example:

.. code-block:: python

    def callback(args: list[str]) -> str | None:
        return " ".join(args)
"""


class CommandManager(IgnisGObjectSingleton):
    """
    A class for managing custom commands.
    A command is a function that accepts a ``list[str]`` as args
    and optionally returns a ``str`` as output.

    Example usage:

    .. code-block:: python

        from ignis.command_manager import CommandManager

        command_manager = CommandManager.get_default()

        # Add or remove a command
        command_manager.add_command("command-name", lambda _: "output message")
        command_manager.remove_command("command-name")

        # Run a command
        command_manager.run_command("command-name")
        # Run with args and output
        output = command_manager.run_command("command-name", ["arg1", "arg2"])

        # Get the callback of a command
        callback = command_manager.get_command("command-name")
    """

    def __init__(self):
        self._commands: dict[str, CommandCallback] = {}
        super().__init__()

    def get_command(self, command_name: str) -> CommandCallback:
        """
        Get a command by name.

        Args:
            command_name: The command's name.

        Returns:
            The command callback.

        Raises:
            CommandNotFoundError: If a command with the given name does not exist.
        """
        command = self._commands.get(command_name, None)
        if command:
            return command
        else:
            raise CommandNotFoundError(command_name)

    def add_command(self, command_name: str, callback: CommandCallback) -> None:
        """
        Add a command.

        Args:
            command_name: The command's name.
            callback: The command callback. It accepts an args list and optionally returns a string.

        Raises:
            CommandAddedError: If a command with the given name already exists.

        Example usage:

        .. code-block:: python

            command_manager = CommandManager.get_default()
            command_manager.add_command("echo", lambda args: " ".join(args))
            command_manager.add_command("ping", lambda _: "pong")
        """
        if command_name in self._commands:
            raise CommandAddedError(command_name)

        self._commands[command_name] = callback

    def remove_command(self, command_name: str) -> None:
        """
        Remove a command by its name.

        Args:
            command_name: The command's name.

        Raises:
            CommandNotFoundError: If a command with the given name does not exist.
        """
        command = self._commands.pop(command_name, None)
        if not command:
            raise CommandNotFoundError(command_name)

    def run_command(
        self, command_name: str, command_args: list[str] | None = None
    ) -> str | None:
        """
        Run a command by its name.

        Args:
            command_name: The command's name.
            command_args: The args list to pass to the command.

        Raises:
            CommandNotFoundError: If a command with the given name does not exist.
        """
        command = self.get_command(command_name)
        return command(command_args or [])

    def list_command_names(self) -> tuple[str, ...]:
        """
        List the names of commands.

        Returns:
            A tuple containing command names.
        """
        return tuple(self._commands.keys())
