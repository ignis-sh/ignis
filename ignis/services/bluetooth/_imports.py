import gi
from ignis.exceptions import GnomeBluetoothNotFoundError
from ignis import is_sphinx_build

try:
    if not is_sphinx_build:
        gi.require_version("GnomeBluetooth", "3.0")
    from gi.repository import GnomeBluetooth  # type: ignore
except (ImportError, ValueError):
    raise GnomeBluetoothNotFoundError() from None

__all__ = ["GnomeBluetooth"]
