import gi
from ignis.exceptions import GvcNotFoundError
from ignis import is_sphinx_build

try:
    if not is_sphinx_build:
        gi.require_version("Gvc", "1.0")
    from gi.repository import Gvc  # type: ignore
except (ImportError, ValueError):
    raise GvcNotFoundError() from None

__all__ = ["Gvc"]
