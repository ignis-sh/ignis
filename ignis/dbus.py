import asyncio
from gi.repository import Gio, GLib  # type: ignore
from typing import Any, overload
from collections.abc import Callable
from ignis import utils
from ignis.gobject import IgnisGObject, IgnisProperty
from ignis.exceptions import DBusMethodNotFoundError, DBusPropertyNotFoundError
from typing import Literal

BUS_TYPE = {"session": Gio.BusType.SESSION, "system": Gio.BusType.SYSTEM}


class DBusService(IgnisGObject):
    """
    A class that helps create a D-Bus service.

    Args:
        name: The well-known name to own.
        object_path: An object path.
        info: An instance of :class:`Gio.DBusInterfaceInfo`. You can get it from XML using :func:`~ignis.utils.utils.load_interface_xml`.
        on_name_acquired: The function to call when ``name`` is acquired.
        on_name_lost: The function to call when ``name`` is lost.

    .. code-block:: python

        from gi.repository import Gio, GLib
        from ignis.dbus import DBusService

        def _MyMethod(invocation: Gio.DBusMethodInvocation, prop1: str, prop2: str, *args) -> GLib.Variant:
            print("do something")
            return GLib.Variant("(is)", (42, "hello"))

        def _MyProperty() -> GLib.Variant:
            return GLib.Variant("(b)", (False,))

        dbus = DBusService(...)
        dbus.register_dbus_method("MyMethod", _MyMethod)
        dbus.register_dbus_property("MyProperty", _MyProperty)
    """

    def __init__(
        self,
        name: str,
        object_path: str,
        info: Gio.DBusInterfaceInfo,
        on_name_acquired: Callable | None = None,
        on_name_lost: Callable | None = None,
    ):
        super().__init__()

        self._name = name
        self._object_path = object_path
        self._info = info
        self._on_name_acquired = on_name_acquired
        self._on_name_lost = on_name_lost

        self._methods: dict[str, Callable] = {}
        self._properties: dict[str, Callable] = {}

        self._id = Gio.bus_own_name(
            Gio.BusType.SESSION,
            name,
            Gio.BusNameOwnerFlags.NONE,
            self.__export_object,
            self._on_name_acquired,
            self._on_name_lost,
        )

    @IgnisProperty
    def name(self) -> str:
        """
        The well-known name to own.
        """
        return self._name

    @IgnisProperty
    def object_path(self) -> str:
        """
        An object path.
        """
        return self._object_path

    @IgnisProperty
    def info(self) -> Gio.DBusInterfaceInfo:
        """
        An instance of :class:`Gio.DBusInterfaceInfo`

        You can get it from XML using :func:`~ignis.utils.utils.load_interface_xml`.
        """
        return self._info

    @IgnisProperty
    def on_name_acquired(self) -> Callable:
        """
        The function to call when ``name`` is acquired.
        """
        return self._on_name_acquired

    @on_name_acquired.setter
    def on_name_acquired(self, value: Callable) -> None:
        self._on_name_acquired = value

    @IgnisProperty
    def on_name_lost(self) -> Callable:
        """
        The function to call when ``name`` is lost.
        """
        return self._on_name_lost

    @on_name_lost.setter
    def on_name_lost(self, value: Callable) -> None:
        self._on_name_lost = value

    @IgnisProperty
    def connection(self) -> Gio.DBusConnection:
        """
        The instance of :class:`Gio.DBusConnection` for this service.
        """
        return self._connection

    @IgnisProperty
    def methods(self) -> dict[str, Callable]:
        """
        The dictionary of registred DBus methods. See :func:`~ignis.dbus.DBusService.register_dbus_method`.
        """
        return self._methods

    @IgnisProperty
    def properties(self) -> dict[str, Callable]:
        """
        The dictionary of registred DBus properties. See :func:`~ignis.dbus.DBusService.register_dbus_property`.
        """
        return self._properties

    def __export_object(self, connection: Gio.DBusConnection, name: str) -> None:
        self._connection = connection
        self._connection.register_object_with_closures2(  # type: ignore
            self._object_path,
            self._info,
            self.__handle_method_call,
            self.__handle_get_property,
            None,
        )

    def __handle_method_call(
        self,
        connection: Gio.DBusConnection,
        sender: str,
        object_path: str,
        interface_name: str,
        method_name: str,
        params: GLib.Variant,
        invocation: Gio.DBusMethodInvocation,
    ) -> None:
        def callback(func: Callable, unpacked_params) -> None:
            result = func(invocation, *unpacked_params)
            invocation.return_value(result)

        func = self._methods.get(method_name, None)
        if not func:
            raise DBusMethodNotFoundError(method_name)

        # params can contain pixbuf, very large amount of data
        # and unpacking may take some time and block the main thread
        # so we unpack in another thread, and call DBus method when unpacking is finished
        utils.ThreadTask(
            target=params.unpack, callback=lambda result: callback(func, result)
        ).run()

    def __handle_get_property(
        self,
        connection: Gio.DBusConnection,
        sender: str,
        object_path: str,
        interface: str,
        value: str,
    ) -> GLib.Variant:
        func = self._properties.get(value, None)
        if not func:
            raise DBusPropertyNotFoundError(value)

        return func()

    def register_dbus_method(self, name: str, method: Callable) -> None:
        """
        Register a D-Bus method for this service.

        Args:
            name: The name of the method to register.
            method: A function to call when the method is invoked (from D-Bus).

        DBus methods:
            - Must accept :class:`Gio.DBusMethodInvocation` as the first argument.
            - Must accept all other arguments typical for this method (specified by interface info).
            - Must return :class:`GLib.Variant` or ``None``, as specified by interface info.
        """
        self._methods[name] = method

    def register_dbus_property(self, name: str, method: Callable) -> None:
        """
        Register D-Bus property for this service.

        Args:
            name: The name of the property to register.
            method: A function to call when the property is accessed (from DBus).

        DBus properties:
            - Must return :class:`GLib.Variant`, as specified by interface info.
        """
        self._properties[name] = method

    def emit_signal(
        self, signal_name: str, parameters: "GLib.Variant | None" = None
    ) -> None:
        """
        Emit a D-Bus signal on this service.

        Args:
            signal_name: The name of the signal to emit.
            parameters: The :class:`GLib.Variant` containing paramaters to pass with the signal.
        """

        self._connection.emit_signal(
            None,
            self._object_path,
            self._name,
            signal_name,
            parameters,
        )

    def unown_name(self) -> None:
        """
        Release ownership of the name.
        """
        Gio.bus_unown_name(self._id)


class DBusProxy(IgnisGObject):
    """
    A class to interact with D-Bus services (create a D-Bus proxy).
    Unlike :class:`Gio.DBusProxy`,
    this class also provides convenient pythonic property access.

    To call a D-Bus method, use the standart pythonic way.
    The first argument always needs to be the DBus signature tuple of the method call.
    Next arguments must match the provided D-Bus signature.
    If the D-Bus method does not accept any arguments, do not pass them.
    Add ``Async`` at the end of the method name to call it asynchronously.

    .. code-block:: python

        from ignis.dbus import DBusProxy

        # sync
        proxy = DBusProxy.new(...)
        result = proxy.MyMethod("(is)", 42, "hello")
        print(result)

        # async
        async def some_func():
            proxy = DBusProxy.new_async(...)
            result = proxy.MyMethodAsync("(is)", 42, "hello")

    To get a D-Bus property:

    .. code-block:: python

        from ignis.dbus import DBusProxy
        proxy = DBusProxy.new(...)
        print(proxy.MyValue)

    To set a D-Bus property:

    .. code-block:: python

        from ignis.dbus import DBusProxy
        proxy = DBusProxy.new(...)
        # pass GLib.Variant as new property value
        proxy.MyValue = GLib.Variant("s", "Hello world!")

    Args:
        bus_type: The type of the bus.
        gproxy: An instance of :class:`Gio.DBusProxy`.
    """

    def __init__(self, bus_type: Literal["session", "system"], gproxy: Gio.DBusProxy):
        super().__init__()
        self._bus_type = bus_type
        self._methods: list[str] = []
        self._properties: list[str] = []

        self._gproxy = gproxy

        for method in self.info.methods:
            self._methods.append(method.name)

        for prop in self.info.properties:
            self._properties.append(prop.name)

    @classmethod
    def new(
        cls,
        name: str,
        object_path: str,
        interface_name: str,
        info: Gio.DBusInterfaceInfo,
        bus_type: Literal["session", "system"] = "session",
    ) -> "DBusProxy":
        """
        Synchronously initialize a new instance.

        Args:
            name: A bus name (well-known or unique).
            object_path: An object path.
            interface_name: A D-Bus interface name.
            info: A :class:`Gio.DBusInterfaceInfo` instance. You can get it from XML using :class:`~ignis.utils.utils.load_interface_xml`.
            bus_type: The type of the bus.
        """
        gproxy = Gio.DBusProxy.new_for_bus_sync(
            BUS_TYPE[bus_type],
            Gio.DBusProxyFlags.NONE,
            info,
            name,
            object_path,
            interface_name,
            None,
        )
        return cls(bus_type=bus_type, gproxy=gproxy)

    @classmethod
    async def new_async(
        cls,
        name: str,
        object_path: str,
        interface_name: str,
        info: Gio.DBusInterfaceInfo,
        bus_type: Literal["session", "system"] = "session",
    ) -> "DBusProxy":
        """
        Asynchronously initialize a new instance.

        Args:
            name: A bus name (well-known or unique).
            object_path: An object path.
            interface_name: A D-Bus interface name.
            info: A :class:`Gio.DBusInterfaceInfo` instance. You can get it from XML using :class:`~ignis.utils.utils.load_interface_xml`.
            bus_type: The type of the bus.
            callback: A function to call when the initialization is complete. The function will receive a newly initialized instance of this class.
            *user_data: User data to pass to ``callback``.
        """

        gproxy = await Gio.DBusProxy.new_for_bus(  # type: ignore
            BUS_TYPE[bus_type],
            Gio.DBusProxyFlags.NONE,
            info,
            name,
            object_path,
            interface_name,
        )

        return cls(bus_type=bus_type, gproxy=gproxy)

    @IgnisProperty
    def name(self) -> str:
        """
        A bus name (well-known or unique).
        """
        return self._gproxy.props.g_name

    @IgnisProperty
    def object_path(self) -> str:
        """
        An object path.
        """
        return self._gproxy.props.g_object_path

    @IgnisProperty
    def interface_name(self) -> str:
        """
        A D-Bus interface name.
        """
        return self._gproxy.props.g_interface_name

    @IgnisProperty
    def info(self) -> Gio.DBusInterfaceInfo:
        """
        A :class:`Gio.DBusInterfaceInfo` instance.

        You can get it from XML using :class:`~ignis.utils.utils.load_interface_xml`.
        """
        return self._gproxy.props.g_interface_info

    @IgnisProperty
    def bus_type(self) -> Literal["session", "system"]:
        """
        The type of the bus.
        """
        return self._bus_type

    @IgnisProperty
    def gproxy(self) -> Gio.DBusProxy:
        """
        The :class:`Gio.DBusProxy` instance.
        """
        return self._gproxy

    @IgnisProperty
    def connection(self) -> Gio.DBusConnection:
        """
        The instance of :class:`Gio.DBusConnection` for this proxy.
        """
        return self._gproxy.get_connection()

    @IgnisProperty
    def methods(self) -> list[str]:
        """
        A list of methods exposed by D-Bus service.
        """
        return self._methods

    @IgnisProperty
    def properties(self) -> list[str]:
        """
        A list of properties exposed by D-Bus service.
        """
        return self._properties

    @IgnisProperty
    def has_owner(self) -> bool:
        """
        Whether the ``name`` has an owner.
        """
        dbus = DBusProxy.new(
            name="org.freedesktop.DBus",
            object_path="/org/freedesktop/DBus",
            interface_name="org.freedesktop.DBus",
            info=utils.load_interface_xml("org.freedesktop.DBus"),
            bus_type=self.bus_type,
        )
        return dbus.NameHasOwner("(s)", self.name)

    def __getattr__(self, name: str) -> Any:
        async def async_method_wrapper(*args, **kwargs):
            return await self.call_async(name.replace("Async", ""), *args, **kwargs)

        if name in self.methods:
            return getattr(self._gproxy, name)
        elif name.endswith("Async") and name.replace("Async", "") in self.methods:
            return async_method_wrapper
        elif name in self.properties:
            return self.get_dbus_property(name)
        else:
            return super().__getattribute__(name)

    def __setattr__(self, name: str, value: Any) -> None:
        if name in self.__dict__.get("_properties", {}):  # avoid recursion
            self.set_dbus_property(name, value)
        else:
            return super().__setattr__(name, value)

    def signal_subscribe(
        self,
        signal_name: str,
        callback: Callable | None = None,
    ) -> int:
        """
        Subscribe to D-Bus signal.

        Args:
            signal_name: The signal name to subscribe.
            callback: A function to call when signal is emitted.
        Returns:
            A subscription ID that can be used with :func:`~ignis.dbus.DBusProxy.signal_unsubscribe`
        """
        return self.connection.signal_subscribe(
            self.name,
            self.interface_name,
            signal_name,
            self.object_path,
            None,
            Gio.DBusSignalFlags.NONE,
            callback,
        )

    def signal_unsubscribe(self, id: int) -> None:
        """
        Unsubscribe from D-Bus signal.

        Args:
            id: The ID of the subscription.
        """
        self.connection.signal_unsubscribe(id)

    def __get_variant(self, signature: str, *args) -> GLib.Variant:
        if "(" in signature:
            return GLib.Variant(signature, args)
        else:
            return GLib.Variant(signature, *args)

    def call(
        self,
        method_name: str,
        signature: str | None = None,
        *args,
        flags: Gio.DBusCallFlags = Gio.DBusCallFlags.NONE,
        timeout: int = -1,
    ) -> Any:
        """
        Call a D-Bus method on ``self``.

        Args:
            method_name: The name of the method.
            signature: The D-Bus signature.
            *args: Arguments to pass to the D-Bus method.
            flags: D-Bus call flags.
            timeout: The timeout in milliseconds, or ``-1`` to use the proxy default timeout.
        Returns:
            The returned data from the D-Bus method.
        """
        variant = self._gproxy.call_sync(
            method_name=method_name,
            parameters=self.__get_variant(signature, *args) if signature else None,
            flags=flags,
            timeout_msec=timeout,
            cancellable=None,
        )
        return variant.unpack()

    async def call_async(
        self,
        method_name: str,
        signature: str | None = None,
        *args,
        flags: Gio.DBusCallFlags = Gio.DBusCallFlags.NONE,
        timeout: int = -1,
    ) -> Any:
        """
        Asynchronously call a D-Bus method on ``self``.

        Args:
            method_name: The name of the method.
            signature: The D-Bus signature.
            *args: Arguments to pass to the D-Bus method.
            flags: D-Bus call flags.
            timeout: The timeout in milliseconds, or ``-1`` to use the proxy default timeout.
        Returns:
            The returned data from the D-Bus method.
        """
        variant = await self._gproxy.call(  # type: ignore
            method_name=method_name,
            parameters=self.__get_variant(signature, *args) if signature else None,
            flags=flags,
            timeout_msec=timeout,
        )

        return await asyncio.to_thread(lambda: variant.unpack())

    @overload
    def get_dbus_property(
        self, property_name: str, unpack: Literal[True] = ...
    ) -> Any: ...

    @overload
    def get_dbus_property(
        self, property_name: str, unpack: Literal[False] = ...
    ) -> GLib.Variant: ...

    def get_dbus_property(
        self, property_name: str, unpack: bool = True
    ) -> "Any | GLib.Variant":
        """
        Get the value of a D-Bus property by its name.

        Args:
            property_name: The name of the property.
            unpack: Whether to unpack the returned :class:`GLib.Variant`.
        Returns:
            The value of the D-Bus property or :class:`GLib.Variant`.
        """
        try:
            variant = self.connection.call_sync(
                self.name,
                self.object_path,
                "org.freedesktop.DBus.Properties",
                "Get",
                GLib.Variant(
                    "(ss)",
                    (self.interface_name, property_name),
                ),
                None,
                Gio.DBusCallFlags.NONE,
                -1,
                None,
            )

            if unpack:
                return variant[0]
            else:
                return variant

        except GLib.Error:
            return None

    @overload
    async def get_dbus_property_async(
        self, property_name: str, unpack: Literal[True] = ...
    ) -> Any: ...

    @overload
    async def get_dbus_property_async(
        self, property_name: str, unpack: Literal[False] = ...
    ) -> GLib.Variant: ...

    async def get_dbus_property_async(
        self, property_name: str, unpack: bool = True
    ) -> "Any | GLib.Variant":
        """
        Asynchronously get the value of a D-Bus property by its name.

        Args:
            property_name: The name of the property.
            unpack: Whether to unpack the returned :class:`GLib.Variant`.
        Returns:
            The value of the D-Bus property or :class:`GLib.Variant`.
        """

        variant = await self.connection.call(
            self.name,
            self.object_path,
            "org.freedesktop.DBus.Properties",
            "Get",
            GLib.Variant(
                "(ss)",
                (self.interface_name, property_name),
            ),
            None,
            Gio.DBusCallFlags.NONE,
            -1,
        )

        if unpack:
            # unpack in thread
            return await asyncio.to_thread(lambda: variant[0])
        else:
            return variant

    def set_dbus_property(self, property_name: str, value: GLib.Variant) -> None:
        """
        Set a D-Bus property's value.

        Args:
            property_name: The name of the property to set.
            value: The new value for the property.
        """
        self.connection.call_sync(
            self.name,
            self.object_path,
            "org.freedesktop.DBus.Properties",
            "Set",
            GLib.Variant(
                "(ssv)",
                (self.interface_name, property_name, value),
            ),
            None,
            Gio.DBusCallFlags.NONE,
            -1,
            None,
        )

    async def set_dbus_property_async(
        self, property_name: str, value: GLib.Variant
    ) -> None:
        """
        Asynchronously set a D-Bus property's value.

        Args:
            property_name: The name of the property to set.
            value: The new value for the property.
        """

        await self.connection.call(
            self.name,
            self.object_path,
            "org.freedesktop.DBus.Properties",
            "Set",
            GLib.Variant(
                "(ssv)",
                (self.interface_name, property_name, value),
            ),
            None,
            Gio.DBusCallFlags.NONE,
            -1,
        )

    def watch_name(
        self,
        on_name_appeared: Callable | None = None,
        on_name_vanished: Callable | None = None,
    ) -> None:
        """
        Watch ``name``.

        Args:
            on_name_appeared: A function to call when ``name`` appeared.
            on_name_vanished: A function to call when ``name`` vanished.
        """
        self._watcher = Gio.bus_watch_name(
            BUS_TYPE[self._bus_type],
            self.name,
            Gio.BusNameWatcherFlags.NONE,
            on_name_appeared,
            on_name_vanished,
        )

    def unwatch_name(self) -> None:
        """
        Unwatch name.
        """
        Gio.bus_unwatch_name(self._watcher)
