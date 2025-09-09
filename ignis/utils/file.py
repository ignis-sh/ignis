from gi.repository import Gio  # type: ignore
from typing import overload, Literal


def _get_gfile(
    func_name: str,
    path: str | None = None,
    uri: str | None = None,
    gfile: "Gio.File | None" = None,
) -> Gio.File:
    if path:
        gfile = Gio.File.new_for_path(path)
    elif uri:
        gfile = Gio.File.new_for_uri(uri)
    elif gfile:
        pass
    else:
        raise TypeError(
            f"{func_name} requires either a path or an URI or a Gio.File to be provided"
        )

    return gfile  # type: ignore


def _get_contents(
    func_name: str, contents: bytes | None = None, string: str | None = None
) -> bytes:
    if string:
        contents = string.encode()
    elif contents:
        pass
    else:
        raise TypeError(
            f"{func_name} requires either contents or a string to be provided"
        )

    return contents  # type: ignore


@overload
def read_file(
    path: str | None = None,
    uri: str | None = None,
    gfile: "Gio.File | None" = None,
    decode: Literal[True] = ...,
) -> str: ...


@overload
def read_file(
    path: str | None = None,
    uri: str | None = None,
    gfile: "Gio.File | None" = None,
    decode: Literal[False] = ...,
) -> bytes: ...


def read_file(
    path: str | None = None,
    uri: str | None = None,
    gfile: "Gio.File | None" = None,
    decode: bool = True,
) -> str | bytes:
    """
    Read the contents of a file.

    Args:
        path: The path to the file.
        uri: The URI of the file.
        gfile: An instance of :class:`Gio.File`.
        decode: Whether to decode the file's contents. If ``True``, this function will return :obj:`str`, otherwise :obj:`bytes`.

    Returns:
        The contents of the file.

    At least one of the arguments, ``path``, ``uri``, or ``gfile``, must be provided.

    Example usage:

    .. code-block:: python

        from ignis import utils

        # regular file
        contents = utils.read_file(path="/path/to/file", decode=True)
        print(contents)

        # URI
        utils.read_file(uri="file:///path/to/file", decode=True)
        # Web also supported
        utils.read_file(uri="https://SOME_SITE.org/example_content", decode=False)
    """
    gfile = _get_gfile(func_name="read_file()", path=path, uri=uri, gfile=gfile)

    _, contents, _ = gfile.load_contents()
    if decode:
        return contents.decode()
    else:
        return contents


@overload
async def read_file_async(
    path: str | None = None,
    uri: str | None = None,
    gfile: "Gio.File | None" = None,
    decode: Literal[True] = ...,
) -> str: ...


@overload
async def read_file_async(
    path: str | None = None,
    uri: str | None = None,
    gfile: "Gio.File | None" = None,
    decode: Literal[False] = ...,
) -> bytes: ...


async def read_file_async(
    path: str | None = None,
    uri: str | None = None,
    gfile: "Gio.File | None" = None,
    decode: bool = True,
) -> str | bytes:
    """
    Asynchronously read the contents of a file.

    Args:
        path: The path to the file.
        uri: The URI of the file.
        gfile: An instance of :class:`Gio.File`.
        decode: Whether to decode the file's contents. If ``True``, the callback will receive :obj:`str`, otherwise :obj:`bytes`.

    Returns:
        The contents of the file.

    At least one of the arguments, ``path``, ``uri``, or ``gfile``, must be provided.

    Example usage:

    .. code-block:: python

        import asyncio
        from ignis import utils


        async def some_func() -> None:

            # regular file
            res1 = await utils.read_file_async(path="/path/to/file", decode=True)
            print("Contents 1: ", res1)

            # URI
            res2 = await utils.read_file_async(uri="file:///path/to/file", decode=True)
            print("Contents 2: ", res2)

            # Web also supported
            res3 = await utils.read_file_async(uri="https://SOME_SITE.org/example_content", decode=False)
            print("Contents 3: ", res3)


        asyncio.create_task(some_func())
    """
    gfile = _get_gfile(func_name="read_file_async()", path=path, uri=uri, gfile=gfile)

    _, contents, _ = await gfile.load_contents_async()  # type: ignore

    if decode:
        return contents.decode()
    else:
        return contents


def write_file(
    path: str | None = None,
    uri: str | None = None,
    gfile: "Gio.File | None" = None,
    contents: bytes | None = None,
    string: str | None = None,
) -> None:
    """
    Write contents to a file.

    Args:
        path: The path to the file.
        uri: The URI of the file.
        gfile: An instance of :class:`Gio.File`.
        contents: The bytes to write to the file.
        string: The string to write to the file.

    At least one of the arguments, ``path``, ``uri``, or ``gfile``, must be provided.
    Either ``contents`` or ``string`` must be provided.

    Example usage:

    .. code-block:: python

        import asyncio
        from ignis import utils


        async def some_write_func() -> None:
            # write string
            await utils.write_file(path="/path/to/file", string="some_string")
            # or bytes
            await utils.write_file(path="/path/to/file", bytes=b"some bytes")


        asyncio.create_task(some_write_func())
    """
    gfile = _get_gfile(func_name="write_file()", path=path, uri=uri, gfile=gfile)
    contents = _get_contents(func_name="write_file()", contents=contents, string=string)

    gfile.replace_contents(
        contents, None, False, Gio.FileCreateFlags.REPLACE_DESTINATION, None
    )


async def write_file_async(
    path: str | None = None,
    uri: str | None = None,
    gfile: "Gio.File | None" = None,
    contents: bytes | None = None,
    string: str | None = None,
) -> None:
    """
    Asynchronously write contents to a file.

    Args:
        path: The path to the file.
        uri: The URI of the file.
        gfile: An instance of :class:`Gio.File`.
        contents: The bytes to write to the file.
        string: The string to write to the file.
        callback: A function to call when the operation is complete.
        *user_data: User data to pass to ``callback``.

    At least one of the arguments, ``path``, ``uri``, or ``gfile``, must be provided.
    Either ``contents`` or ``string`` must be provided.

    Example usage:

    .. code-block:: python

        from ignis import utils

        def some_callback() -> None:
            print("Operation is complete")

        # write string
        utils.write_file_async(path="/path/to/file", string="some_string", callback=some_callback)
        # or bytes
        utils.write_file_async(path="/path/to/file", bytes=b"some bytes", callback=some_callback)
    """
    gfile = _get_gfile(func_name="write_file_async()", path=path, uri=uri, gfile=gfile)
    contents = _get_contents(
        func_name="write_file_async()", contents=contents, string=string
    )

    await gfile.replace_contents_async(  # type: ignore
        contents,
        None,
        False,
        Gio.FileCreateFlags.REPLACE_DESTINATION,
    )
