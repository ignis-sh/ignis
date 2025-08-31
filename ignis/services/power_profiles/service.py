from __future__ import annotations
from ignis.base_service import BaseService
from ignis.dbus import DBusProxy
from ignis.exceptions import PowerProfilesDaemonNotRunningError
from ignis.gobject import IgnisProperty
from gi.repository import GLib  # type: ignore
from ignis import utils
from .constants import PP_ICON_TEMPLATE


class PowerProfilesService(BaseService):
    """
    A service for managing power profiles through the DBus interface power-profiles-daemon provides.

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

        if not self.is_available:
            return

        self._proxy.gproxy.connect("g-properties-changed", self.__on_properties_changed)

        self._active_profile: str = self._proxy.ActiveProfile
        self._profiles: list[str] = [p["Profile"] for p in self._proxy.Profiles]
        self._cookie = -1

    @IgnisProperty
    def is_available(self) -> bool:
        """
        Whether power profiles capability in UPower is available and UPower is running.

        If ``False``, this service will not be functional.
        """
        return self._proxy.has_owner

    @IgnisProperty
    def active_profile(  # type: ignore
        self,
    ) -> str:
        """
        Current active power profile.

        Should be either of:
            - `performance`
            - `balanced`
            - `power-saver`
        """
        return self._active_profile

    @active_profile.setter
    def active_profile(
        self,
        profile: str,
    ) -> None:
        self._cookie = -1
        self._proxy.ActiveProfile = GLib.Variant("s", profile)

    def hold_profile(self, profile: str) -> None:
        """
        This forces the passed profile (only `performance` or `power-saver`) to be activated until ignis exits,
        :func:`~release_profile` is called, or the :attr:`~active_profile` is changed manually.

        Use if you need to ensure a specific profile is active for a certain amount of time or while
        a specific task is being performed. This way the previous state will not have to be managed by you.
        """
        if profile == "balanced":
            raise ValueError(
                "Cannot hold the balanced profile, only performance or power-saver."
            )

        self.__hold_profile(profile)

    def __hold_profile(self, profile: str) -> None:
        if not self.is_available:
            raise PowerProfilesDaemonNotRunningError()

        if self._cookie != -1:
            return

        self._cookie = self._proxy.gproxy.HoldProfile(
            "(sss)", profile, "", "com.github.linkfrg.ignis"
        )

    def release_profile(self) -> None:
        """
        Release the hold on the profile
        """
        self.__release_profile()

    def __release_profile(self) -> None:
        if not self.is_available:
            raise PowerProfilesDaemonNotRunningError()

        if self._cookie == -1:
            return

        self._proxy.gproxy.ReleaseProfile("(u)", self._cookie)
        self._cookie = -1

    @IgnisProperty
    def profiles(self) -> list[str]:
        """
        List of available power profiles.

        Possible values are:
            - `performance`
            - `balanced`
            - `power-saver`
        """
        return self._profiles

    @IgnisProperty
    def icon_name(self) -> str:
        """
        Icon name representing the active power profile.
        """
        return PP_ICON_TEMPLATE.format(self.active_profile)

    def __on_properties_changed(self, _, properties: GLib.Variant, ignored):
        prop_dict = properties.unpack()

        if "ActiveProfile" in prop_dict:
            self._active_profile = prop_dict["ActiveProfile"]
            self.notify("active-profile")
            self.notify("icon-name")
        if "Profiles" in prop_dict:
            self._profiles = list(prop_dict["Profiles"].keys())
            self.notify("profiles")
