from gi.repository import GLib  # type: ignore
from ignis.gobject import IgnisGObject, IgnisProperty
from collections.abc import Callable


class Timeout(IgnisGObject):
    """
    Calls a function after a specified time interval.

    Args:
        ms: Time in milliseconds.
        target: The function to call.

    Example usage:

    .. code-block:: python

        from ignis import utils

        utils.Timeout(ms=3000, target=lambda: print("Hello"))
    """

    def __init__(self, ms: int, target: Callable, *args):
        super().__init__()
        self._ms = ms
        self._target = target

        self._id = GLib.timeout_add(ms, target, *args)

    @IgnisProperty
    def ms(self) -> int:
        """
        Time in milliseconds.
        """
        return self._ms

    @IgnisProperty
    def target(self) -> Callable:
        """
        The function to call.
        """
        return self._target

    def cancel(self) -> None:
        """
        Cancel the timeout if it is active.

        This method prevents the ``target`` function from being called.
        """
        if GLib.MainContext.default().find_source_by_id(self._id):
            GLib.source_remove(self._id)
