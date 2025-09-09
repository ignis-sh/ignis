import threading
from collections.abc import Callable
from ignis.gobject import IgnisGObject, IgnisSignal


def thread(target: Callable, *args, **kwargs) -> threading.Thread:
    """
    Simply run the given function in a thread.
    The provided args and kwargs will be passed to the function.

    Args:
        target: The function to run.

    Returns:
        The thread in which the function is running.
    """
    th = threading.Thread(target=target, args=args, kwargs=kwargs, daemon=True)
    th.start()
    return th


def run_in_thread(func: Callable) -> Callable:
    """
    Decorator to run the decorated function in a thread.
    """

    def wrapper(*args, **kwargs):
        return thread(func, *args, **kwargs)

    return wrapper


class ThreadTask(IgnisGObject):
    """
    Execute a function in another thread and call a callback when it's finished.
    The output from the function is passed to the callback.

    Parameters:
        target: The function to execute in another thread.
        callback: The function to call when ``target`` has finished.
    """

    def __init__(self, target: Callable, callback: Callable):
        super().__init__()
        self._target = target
        self._callback = callback

        self.connect("finished", lambda x, result: callback(result))

    @run_in_thread
    def __run(self) -> None:
        result = self._target()
        self.emit("finished", result)

    @IgnisSignal
    def finished(self, output: object):
        """
        Args:
            output: The output from the function.
        """

    def run(self) -> None:
        """
        Run this task.
        """
        self.__run()
