from ._imports import NM


def check_is_vpn(func):
    def wrapper(*args, **kwargs):
        connection = args[2]
        if (
            connection.get_connection_type() == "vpn"
            or connection.get_connection_type() == "wireguard"
        ):
            func(*args, **kwargs)

    return wrapper


def get_wifi_connect_window_name(bssid: str) -> str:
    return f"wifi-connect_{bssid}"


def filter_connections(
    obj: "NM.AccessPoint | NM.Device", connections: list[NM.Connection]
) -> list[NM.Connection]:
    # Filter manually using connection_valid()
    # Because the transfer annotation for this function may not work correctly with bindings
    # See https://gitlab.gnome.org/GNOME/gobject-introspection/-/issues/305
    # E.g.: NM.Device.filter_connections(NM.Client.get_connections()) can cause SIGSEGV

    return [conn for conn in connections if obj.connection_valid(conn)]
