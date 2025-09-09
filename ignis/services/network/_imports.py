import gi
from ignis.exceptions import NetworkManagerNotFoundError
from ignis import is_sphinx_build

try:
    if not is_sphinx_build:
        gi.require_version("NM", "1.0")
    from gi.repository import NM  # type: ignore
except (ImportError, ValueError):
    raise NetworkManagerNotFoundError() from None

__all__ = ["NM"]
