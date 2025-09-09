from collections.abc import Callable
from .timeout import Timeout


class DebounceTask:
    """
    Delays function calls until a specified time elapses after the most recent call.

    .. hint::
        See the decorator for this class :func:`~ignis.utils.utils.debounce`.

    Parameters:
        ms: The delay time in milliseconds.
        target: The function to invoke after the delay.
    """

    def __init__(self, ms: int, target: Callable) -> None:
        self._timeout: Timeout | None = None
        self._ms = ms
        self._target = target

    def run(self, *args, **kwargs):
        """
        Run the task.
        ``*args`` and ``**kwargs`` will be passed to the ``target`` function.
        """
        if self._timeout is not None:
            self._timeout.cancel()
        self._timeout = Timeout(self._ms, lambda: self._target(*args, **kwargs))


def debounce(ms: int):
    """
    A decorator to delay function execution until a set time has passed since the last call.

    This is a convenient wrapper for the :class:`~ignis.utils.utils.DebounceTask` class.

    Args:
        ms: The delay time in milliseconds.

    Example usage:

    .. code-block:: python

        from ignis import utils

        @utils.debounce(500) # delay for 500 ms (0.5 s)
        def some_func(x) -> None:
            print("called!")

        some_func(1)
        some_func(2)  # only this call will execute
    """

    def decorate_function(func: Callable):
        task = DebounceTask(ms, func)

        def wrapper(*args, **kwargs):
            task.run(*args, **kwargs)

        return wrapper

    return decorate_function
