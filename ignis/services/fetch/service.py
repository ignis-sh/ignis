import os
import glob
from gi.repository import Gtk  # type: ignore
from ignis.base_service import BaseService
from ignis.gobject import IgnisProperty
from ignis import utils


class FetchService(BaseService):
    """
    A service for fetching system information.

    Example usage:

    .. code-block:: python

        from ignis.services.fetch import FetchService

        fetch = FetchService.get_default()

        print(fetch.os_name)
        print(fetch.hostname)
        print(fetch.kernel)
    """

    def __init__(self):
        super().__init__()
        self._icon_theme = Gtk.IconTheme.get_for_display(utils.get_gdk_display())
        self._os_info = self.__get_os_info()

    def __get_os_info(self) -> dict[str, str]:
        os_info = {}
        with open("/etc/os-release") as f:
            for line in f:
                if "=" in line:
                    key, value = line.strip().split("=", 1)
                    os_info[key] = value.strip('"')

        return os_info

    @IgnisProperty
    def os_name(self) -> str:
        """
        The OS name.
        """
        return self._os_info.get("NAME", "Unknown")

    @IgnisProperty
    def os_id(self) -> str:
        """
        The OS ID.
        """
        return self._os_info.get("ID", "Unknown")

    @IgnisProperty
    def os_build_id(self) -> str:
        """
        The OS build ID.
        """
        return self._os_info.get("BUILD_ID", "Unknown")

    @IgnisProperty
    def os_ansi_color(self) -> str:
        """
        The OS ANSI color.
        """
        return self._os_info.get("ANSI_COLOR", "Unknown")

    @IgnisProperty
    def os_home_url(self) -> str:
        """
        The OS homepage URL.
        """
        return self._os_info.get("HOME_URL", "Unknown")

    @IgnisProperty
    def os_documentation_url(self) -> str:
        """
        The OS documentation URL.
        """
        return self._os_info.get("DOCUMENTATION_URL", "Unknown")

    @IgnisProperty
    def os_support_url(self) -> str:
        """
        The OS support URL.
        """
        return self._os_info.get("SUPPORT_URL", "Unknown")

    @IgnisProperty
    def os_bug_report_url(self) -> str:
        """
        The OS bug report URL.
        """
        return self._os_info.get("BUG_REPORT_URL", "Unknown")

    @IgnisProperty
    def os_privacy_policy_url(self) -> str:
        """
        The OS privacy policy URL.
        """
        return self._os_info.get("PRIVACY_POLICY_URL", "Unknown")

    def __icon_or_none(self, icon_name: str) -> str | None:
        if not self._icon_theme.has_icon(icon_name):
            return None
        else:
            return icon_name

    @IgnisProperty
    def os_logo(self) -> str | None:
        """
        The OS logo icon name. ``None`` if not available.
        """
        return self._os_info.get("LOGO", None)

    @IgnisProperty
    def os_logo_dark(self) -> str | None:
        """
        The OS dark logo icon name. ``None`` if not available.
        """
        return self.__icon_or_none(f"{self.os_logo}-dark")

    @IgnisProperty
    def os_logo_text(self) -> str | None:
        """
        The OS logo with text icon name. ``None`` if not available.
        """
        return self.__icon_or_none(f"{self.os_logo}-text")

    @IgnisProperty
    def os_logo_text_dark(self) -> str | None:
        """
        The OS dark logo with text icon name. ``None`` if not available.
        """
        return self.__icon_or_none(f"{self.os_logo}-text-dark")

    @IgnisProperty
    def session_type(self) -> str | None:
        """
        The current session type (wayland/x11).
        """
        return os.environ.get("XDG_SESSION_TYPE")

    @IgnisProperty
    def current_desktop(self) -> str | None:
        """
        The current desktop environment.
        """
        return os.environ.get("XDG_CURRENT_DESKTOP")

    @IgnisProperty
    def hostname(self) -> str:
        """
        The hostname of this machine.
        """
        with open("/etc/hostname") as file:
            data = file.read()
        return data

    @IgnisProperty
    def kernel(self) -> str:
        """
        Kernel version.
        """
        return os.uname().release

    @IgnisProperty
    def uptime(self) -> tuple[int, int, int, int]:
        """
        The current uptime (days, hours, minutes, seconds).

        You can use :class:`~ignis.utils.utils.Poll` to get the current uptime every minute or second.
        """
        with open("/proc/uptime") as f:
            uptime_seconds = float(f.readline().split()[0])

        uptime_minutes, seconds = divmod(uptime_seconds, 60)
        uptime_hours, minutes = divmod(uptime_minutes, 60)
        days, hours = divmod(uptime_hours, 24)

        return int(days), int(hours), int(minutes), int(seconds)

    @IgnisProperty
    def cpu(self) -> str:
        """
        CPU model.
        """
        cpu_name = "Unknown"
        with open("/proc/cpuinfo") as f:
            for line in f:
                if "model name" in line:
                    cpu_name = line.split(":")[1].strip()
                    break
        return cpu_name

    # Get CPU temperature from x86_pkg_temp driver used by various Intel CPUs
    # Returns None if not found
    def __get_x86_pkg_temp(self) -> float | None:
        for thermal_zone in glob.glob("/sys/class/thermal/thermal_zone*"):
            type_path = os.path.join(thermal_zone, "type")
            temp_path = os.path.join(thermal_zone, "temp")
            try:
                with open(type_path) as type_file:
                    zone_type = type_file.read().strip().lower()

                if zone_type == "x86_pkg_temp":
                    with open(temp_path) as temp_file:
                        return int(temp_file.read().strip()) / 1000.0
            except FileNotFoundError:
                continue
        return None

    # Get CPU temperature from k10temp driver used by various AMD CPUs
    # Returns None if not found
    def __get_k10temp(self) -> float | None:
        for hwmon in glob.glob("/sys/class/hwmon/*"):
            name_path = os.path.join(hwmon, "name")
            try:
                with open(name_path) as name_file:
                    name = name_file.read().strip()

                if name == "k10temp":
                    for temp_label_path, temp_input_path in zip(
                        glob.glob(os.path.join(hwmon, "temp*_label")),
                        glob.glob(os.path.join(hwmon, "temp*_input")),
                        strict=True,
                    ):
                        try:
                            with open(temp_label_path) as temp_label_file:
                                temp_label = temp_label_file.read().strip()

                            if temp_label == "Tctl":
                                with open(temp_input_path) as temp_input_file:
                                    return int(temp_input_file.read().strip()) / 1000.0
                        except FileNotFoundError:
                            continue
            except FileNotFoundError:
                continue
        return None

    @IgnisProperty
    def cpu_temp(self) -> float:
        """
        Current CPU temperature.
        """
        return self.__get_x86_pkg_temp() or self.__get_k10temp() or -1.0

    @IgnisProperty
    def mem_info(self) -> dict[str, int]:
        """
        The dictionary with all information about RAM.
        """
        mem_info = {}
        with open("/proc/meminfo") as file:
            for line in file:
                key, value = line.split(":")
                value = value.replace("kB", "")
                value = value.replace(" ", "")
                mem_info[key.strip()] = int(value)
        return mem_info

    @IgnisProperty
    def mem_total(self) -> int:
        """
        Total amount of RAM.
        """
        return self.mem_info.get("MemTotal", None)

    @IgnisProperty
    def mem_available(self) -> int:
        """
        Available amount of RAM.
        """
        return self.mem_info.get("MemAvailable", None)

    @IgnisProperty
    def mem_used(self) -> int:
        """
        Vendor of the motherboard.
        """
        return self.mem_total - self.mem_available

    @IgnisProperty
    def board_vendor(self) -> str:
        """
        Motherboard name.
        """
        with open("/sys/devices/virtual/dmi/id/board_vendor") as file:
            data = file.read()

        return data.strip()

    @IgnisProperty
    def board_name(self) -> str:
        """
        BIOS/UEFI version.
        """
        with open("/sys/devices/virtual/dmi/id/board_name") as file:
            data = file.read()

        return data.strip()

    @IgnisProperty
    def bios_version(self) -> str:
        with open("/sys/devices/virtual/dmi/id/bios_version") as file:
            data = file.read()

        return data.strip()

    @IgnisProperty
    def gtk_theme(self) -> str | None:
        """
        Current GTK theme.
        """
        settings = Gtk.Settings.get_default()
        if not settings:
            return None

        return settings.get_property("gtk-theme-name")

    @IgnisProperty
    def icon_theme(self) -> str | None:
        """
        Current icon theme.
        """
        return self._icon_theme.get_theme_name()
