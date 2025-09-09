from gi.repository import GObject  # type: ignore
from collections.abc import Callable
from ignis.dbus import DBusProxy


class ConnectionManager:
    """
    A helper class for managing connection handler IDs.
    """

    def __init__(self):
        self._ids: dict[GObject.Object, list[int]] = {}

    @property
    def ids(self) -> dict[GObject.Object, list[int]]:
        """
        A dictionary mapping GObject instances to lists of handler IDs.
        """
        return self._ids

    def connect(
        self, gobject: GObject.Object, signal_name: str, handler: Callable, *args
    ) -> int:
        """
        Connect to a signal and store the handler ID.
        Equivalent to :func:`GObject.Object.connect`, but also saves the handler ID in :attr:`ids`.

        Args:
            gobject: The GObject instance.
            signal_name: The signal name.
            handler: The handler function.
            *args: Arguments to pass to ``handler``.
        Returns:
            The handler ID.
        """
        id_ = gobject.connect(signal_name, handler, *args)

        if gobject in self._ids:
            self._ids[gobject].append(id_)
        else:
            self._ids[gobject] = [id_]

        return id_

    def disconnect(self, gobject: GObject.Object, handler_id: int) -> None:
        """
        Disconnect from a signal by the ``handler_id``.
        Equivalent to :func:`GObject.Object.disconnect`, but also removes the stored handler ID from :attr:`ids`.

        Args:
            gobject: The GObject instance.
            handler_id: The handler ID.
        """
        gobject.disconnect(handler_id)
        self._ids[gobject].remove(handler_id)

    def disconnect_gobject(self, gobject: GObject.Object) -> None:
        """
        Disconnect the given GObject from ALL signals that were connected using :func:`connect`.

        Args:
            gobject: The GObject to disconnect.
        """
        for id_ in self._ids[gobject]:
            self.disconnect(gobject, id_)

    def disconnect_all(self) -> None:
        """
        Disconnect ALL GObjects from ALL signals that were connected using :func:`connect`.
        """
        for gobject, ids in self._ids.items():
            for id_ in ids:
                self.disconnect(gobject, id_)


class DBusConnectionManager:
    """
    A helper class for managing :class:`DBusProxy` subscription IDs.
    """

    def __init__(self):
        self._ids: dict[DBusProxy, list[int]] = {}

    @property
    def ids(self) -> dict[DBusProxy, list[int]]:
        """
        A dictionary mapping :class:`DBusProxy` instances to lists of subscription IDs.
        """
        return self._ids

    def subscribe(self, proxy: DBusProxy, signal_name: str, callback: Callable) -> int:
        """
        Subscribe to a D-Bus signal.
        The same as :class:`DBusProxy.signal_subscribe`, but saves the subscription ID to :attr:`ids`.

        Args:
            proxy: The D-Bus proxy instance.
            signal_name: The signal name.
            callback: The callback function.
        Returns:
            The subscription ID.
        """
        id_ = proxy.signal_subscribe(signal_name, callback)

        if proxy in self._ids:
            self._ids[proxy].append(id_)
        else:
            self._ids[proxy] = [id_]

        return id_

    def unsubscribe(self, proxy: DBusProxy, subscription_id: int) -> None:
        """
        Unsubscribe from a signal by the ``subscription_id``.
        Equivalent to :func:`DBusProxy.unsubscribe`, but also removes the stored subscription ID from :attr:`ids`.

        Args:
            gobject: The D-Bus proxy instance.
            subscription_id: The subscription ID.
        """
        proxy.signal_unsubscribe(subscription_id)
        self._ids[proxy].remove(subscription_id)

    def unsubscribe_proxy(self, proxy: DBusProxy) -> None:
        """
        Unsubscribe the given proxy from ALL signals that were subscribed using :func:`subscribe`.

        Args:
            proxy: The proxy to unsubscribe.
        """
        for id_ in self._ids[proxy]:
            self.unsubscribe(proxy, id_)

    def unsubscribe_all(self) -> None:
        """
        Unsubscribe ALL proxys from ALL signals that were subscribed using :func:`subscribe`.
        """
        for proxy, ids in self._ids.items():
            for id_ in ids:
                self.unsubscribe(proxy, id_)
