from collections.abc import Callable
from ignis.gobject import IgnisGObjectSingleton
from ignis.exceptions import CommandAddedError, CommandNotFoundError


CommandCallback = Callable[..., str | None]


class CommandManager(IgnisGObjectSingleton):
    """
    A class for managing custom commands.
    A command is a function that accepts ``*args: str`` as args
    and optionally returns a ``str`` as output.

    Example usage:

    .. code-block:: python

        from ignis.command_manager import CommandManager

        command_manager = CommandManager.get_default()

        # Add a command
        command_manager.add_command("command-name", lambda *_: "output message")
        command_manager.add_command(
            "command-name", lambda fmt="%H:%M", *_: set_format(fmt)
        )

        # A regular form of callbacks
        def regular_callback(
            arg1: str, arg_optional: str | None = None, *args: str
        ) -> str | None:
            if arg1 == "Hello":
                return "world!"

            if arg_optional:
                return f"arg_optional: {arg_optional}"

            return None # Nothing will be printed in CLI

        command_manager.add_command("regular-command", regular_callback)

        # Remove a command by name
        command_manager.remove_command("command-name")

        # Run a command
        command_manager.run_command("command-name")
        # Run with args and output
        output = command_manager.run_command("command-name", *["arg1", "arg2"])
        output = command_manager.run_command("command-name", "arg1", "arg2")
        # Run from the `ignis` CLI:
        # $ ignis run-command command-name
        # $ ignis run-command command-name arg1 arg2

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
            callback: The command callback. It accepts an ``*args: str`` and optionally returns a ``str``.

        Raises:
            CommandAddedError: If a command with the given name already exists.
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

    def run_command(self, command_name: str, *command_args: str) -> str | None:
        """
        Run a command by its name.

        Args:
            command_name: The command's name.
            command_args: The args list to pass to the command.

        Raises:
            CommandNotFoundError: If a command with the given name does not exist.
        """
        command = self.get_command(command_name)
        return command(*command_args)

    def list_command_names(self) -> tuple[str, ...]:
        """
        List the names of commands.

        Returns:
            A tuple containing command names.
        """
        return tuple(self._commands.keys())
