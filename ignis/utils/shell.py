import asyncio
import subprocess


def exec_sh(command: str, **kwargs) -> subprocess.CompletedProcess:
    """
    Execute a shell (bash) command.

    Args:
        command: The command to execute.

    ``**kwargs`` will be passed to ``subprocess.run()``.

    Returns:
        The result of the command execution. You can use the ``stdout`` property to get the command's output.
    """
    return subprocess.run(command, shell=True, text=True, capture_output=True, **kwargs)


class AsyncCompletedProcess:
    """
    Completed process object for :func:`~ignis.utils.utils.exec_sh_async`.
    """

    def __init__(self, stdout: str, stderr: str, returncode: int) -> None:
        self._returncode: int = returncode
        self._stdout: str = stdout
        self._stderr: str = stderr

    @property
    def returncode(self) -> int:
        """
        The return code of the process.
        """
        return self._returncode

    @property
    def stdout(self) -> str:
        """
        The output of the process.
        """
        return self._stdout

    @property
    def stderr(self) -> str:
        """
        The stderr (errors) of the process.
        """
        return self._stderr


async def exec_sh_async(command: str) -> AsyncCompletedProcess:
    """
    Execute a shell (bash) command asynchronously.

    Args:
        command: The command to execute.
        on_finished: A function to call when the process is finished. An instance of :class:`~ignis.utils.exec_sh.AsyncCompletedProcess` will be passed to this function.

    Returns:
        The instance of ``Gio.Subprocess``.
    """

    process = await asyncio.create_subprocess_shell(
        command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    returncode = process.returncode

    return AsyncCompletedProcess(
        stdout.decode(), stderr.decode(), returncode if returncode is not None else -1
    )
