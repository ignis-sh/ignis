from __future__ import annotations
from ignis.base_service import BaseService
from ignis.dbus import DBusProxy
from ignis.gobject import IgnisProperty
from gi.repository import GLib  # type: ignore
from ignis import utils


class PowerProfilesService(BaseService):
    """
    A service for managing power profiles through the UPower DBus interface.

    Example usage:

    .. code-block:: python

        from ignis.services.power_profiles import PowerProfilesService

        power_profiles = PowerProfilesService.get_default()

        print(power_profiles.active_profile)
        power_profiles.active_profile = "performance"

        for profile in power_profiles.profiles:
            print(profile)

        power_profiles.connect("notify::active-profile", lambda x, y: print(power_profiles.active_profile))
    """

    def __init__(self) -> None:
        super().__init__()

        self._proxy = DBusProxy.new(
            name="org.freedesktop.UPower.PowerProfiles",
            object_path="/org/freedesktop/UPower/PowerProfiles",
            interface_name="org.freedesktop.UPower.PowerProfiles",
            info=utils.load_interface_xml("org.freedesktop.UPower.PowerProfiles"),
            bus_type="system",
        )

        self._proxy.gproxy.connect("g-properties-changed", self.__on_properties_changed)

        self._active_profile: str = self._proxy.ActiveProfile
        self._profiles: list[str] = [p["Profile"] for p in self._proxy.Profiles]
        self._cookie = -1

    @IgnisProperty
    def active_profile(  # type: ignore
        self,
    ) -> str:
        """
        Current active power profile.

        Should be either of:
            - performance
            - balanced
            - power-saver
        """
        return self._active_profile

    @active_profile.setter
    def active_profile(
        self,
        profile: str,
    ) -> None:
        if profile == "balanced" and self._cookie != -1:
            self._proxy.gproxy.ReleaseProfile("(u)", self._cookie)
            return
        self._cookie = self._proxy.gproxy.HoldProfile(
            "(sss)", profile, "", "com.github.linkfrg.ignis"
        )

    @IgnisProperty
    def profiles(self) -> list[str]:
        """
        List of available power profiles.

        Possible values are:
            - performance
            - balanced
            - power-saver
        """
        return self._profiles

    @IgnisProperty
    def icon_name(self) -> str:
        """
        The current icon name representing the active power profile.
        """
        if self.active_profile == "performance":
            return "power-profile-performance-symbolic"
        if self.active_profile == "balanced":
            return "power-profile-balanced-symbolic"
        if self.active_profile == "power-saver":
            return "power-profile-power-saver-symbolic"
        return ""

    def __on_properties_changed(self, _, properties: GLib.Variant, ignored):
        prop_dict = properties.unpack()

        if "ActiveProfile" in prop_dict:
            self._active_profile = prop_dict["ActiveProfile"]
            self.notify("active-profile")
        if "Profiles" in prop_dict:
            self._profiles = list(prop_dict["Profiles"].keys())
            self.notify("profiles")
