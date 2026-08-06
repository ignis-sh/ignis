from ignis.gobject import IgnisGObject, IgnisProperty, IgnisSignal
from gi.repository import GLib  # type: ignore
from ignis.dbus import DBusProxy
from ignis import utils
from .constants import DEVICE_KIND, DeviceState


class UPowerDevice(IgnisGObject):
    """
    The general class for power devices, including batteries.
    """

    def __init__(self, object_path: str):
        super().__init__()

        self.__watching_props: dict[str, tuple[str, ...]] = {}
        self._object_path = object_path

        self._proxy = DBusProxy.new(
            name="org.freedesktop.UPower",
            object_path=object_path,
            interface_name="org.freedesktop.UPower.Device",
            info=utils.load_interface_xml("org.freedesktop.UPower.Device"),
            bus_type="system",
        )
        self._proxy.gproxy.connect("g-properties-changed", self.__sync)

        self.__watch_property("Percentage", "percent")
        self.__watch_property("Energy", "energy")
        self.__watch_property("EnergyFull", "energy-full")
        self.__watch_property("EnergyRate", "energy-rate")
        self.__watch_property("ChargeCycles", "charge-cycles")
        self.__watch_property("PowerSupply", "power-supply")
        self.__watch_property("Voltage", "voltage")
        self.__watch_property("Temperature", "temperature")
        self.__watch_property("IconName", "icon-name")

        self.__watch_property("IsPresent", "available")
        self.__watch_property("State", "charging", "charged", "time-remaining")
        self.__watch_property("TimeToFull", "time-remaining")
        self.__watch_property("TimeToEmpty", "time-remaining")

        self.__watch_property("Online", "online")

    def __watch_property(self, dbus_property: str, *prop_names: str) -> None:
        self.__watching_props[dbus_property] = prop_names

    def __sync(self, proxy, properties: GLib.Variant, invalidated_properties) -> None:
        prop_dict = properties.unpack()

        for dbus_property in prop_dict.keys():
            if dbus_property in self.__watching_props:
                for i in self.__watching_props[dbus_property]:
                    self.notify(i)

    @IgnisSignal
    def removed(self):
        """
        Emitted when the device has been removed.
        """

    @IgnisProperty
    def object_path(self) -> str:
        """
        The D-Bus object path of the device.
        """
        return self._object_path

    @IgnisProperty
    def proxy(self) -> DBusProxy:
        """
        The instance of :class:`~ignis.dbus.DBusProxy` for this device.
        """
        return self._proxy

    @IgnisProperty
    def native_path(self) -> str:
        """
        The native path of the device.
        """
        return self._proxy.NativePath

    @IgnisProperty
    def kind(self) -> str:
        """
        The device kind, e.g. ``battery``.
        """
        return DEVICE_KIND.get(self._proxy.Type, "unknown")

    @IgnisProperty
    def available(self) -> bool:
        """
        Whether the device is available.
        """
        return self._proxy.IsPresent

    @IgnisProperty
    def online(self) -> bool:
        """
        Whether the device is online.
        """
        return self._proxy.Online

    @IgnisProperty
    def percent(self) -> float:
        """
        The current percentage of the device.
        """
        return self._proxy.Percentage

    @IgnisProperty
    def charging(self) -> bool:
        """
        Whether the device is currently charging.
        """
        return self._proxy.State == DeviceState["CHARGING"]

    @IgnisProperty
    def charged(self) -> bool:
        """
        Whether the device is charged.
        """
        return self._proxy.State == DeviceState["FULLY_CHARGED"]

    @IgnisProperty
    def icon_name(self) -> str:
        """
        The current icon name.
        """
        return self._proxy.IconName

    @IgnisProperty
    def time_remaining(self) -> int:
        """
        The time in seconds until fully charged (when charging) or until fully drains (when discharging).
        """
        return self._proxy.TimeToFull if self.charging else self._proxy.TimeToEmpty

    @IgnisProperty
    def energy(self) -> float:
        """
        The energy left in the device. Measured in mWh.
        """
        return self._proxy.Energy

    @IgnisProperty
    def energy_full(self) -> float:
        """
        The amount of energy when the device is fully charged. Measured in mWh.
        """
        return self._proxy.EnergyFull

    @IgnisProperty
    def energy_full_design(self) -> float:
        """
        The amount of energy when the device was brand new. Measured in mWh.
        """
        return self._proxy.EnergyDesign

    @IgnisProperty
    def energy_rate(self) -> float:
        """
        The rate of discharge or charge. Measured in mW.
        """
        return self._proxy.EnergyRate

    @IgnisProperty
    def charge_cycles(self) -> int:
        """
        The number of charge cycles for the device, or -1 if unknown or non-applicable.
        """
        return self._proxy.ChargeCycles

    @IgnisProperty
    def vendor(self) -> str:
        """
        The vendor of the device.
        """
        return self._proxy.Vendor

    @IgnisProperty
    def model(self) -> str:
        """
        The model of the device.
        """
        return self._proxy.Model

    @IgnisProperty
    def serial(self) -> str:
        """
        The serial number of the device.
        """
        return self._proxy.Serial

    @IgnisProperty
    def power_supply(self) -> bool:
        """
        Whether the device is powering the system.
        """
        return self._proxy.PowerSupply

    @IgnisProperty
    def technology(self) -> str:
        """
        The device technology e.g. ``lithium-ion``.
        """
        return DEVICE_KIND.get(self._proxy.Technology, "unknown")

    @IgnisProperty
    def temperature(self) -> float:
        """
        The temperature of the device in degrees Celsius.
        """
        return self._proxy.Temperature

    @IgnisProperty
    def voltage(self) -> float:
        """
        The current voltage of the device.
        """
        return self._proxy.Voltage
