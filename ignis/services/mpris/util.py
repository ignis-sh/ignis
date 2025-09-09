import os
from urllib.parse import urlparse, unquote


def uri_to_unix_path(uri: str) -> str:
    parsed = urlparse(uri)

    if parsed.scheme == "file":
        return unquote(os.path.basename(parsed.path))

    elif parsed.scheme in ("http", "https"):
        return unquote(os.path.basename(parsed.path))

    else:
        raise ValueError(f"Unsupported URI scheme: {parsed.scheme}")
