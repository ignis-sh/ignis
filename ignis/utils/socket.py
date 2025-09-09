import socket
from collections.abc import Generator
from typing import Literal


def send_socket(
    sock: socket.socket,
    message: str,
    errors: Literal["strict", "replace", "ignore"] = "strict",
    end_char: str | None = None,
) -> str:
    """
    Send a message to the socket.

    Args:
        sock: An instance of a socket.
        message: The message to send.
        errors: The error handling scheme that will be passed to :py:meth:`bytes.decode`.
        end_char: The character after which the response is considered fully received (e.g, ``\\n``).

    Returns:
        The response from the socket.
    """
    sock.send(message.encode())

    resp = bytearray()
    end_bytes = end_char.encode() if end_char is not None else None

    while True:
        chunk = sock.recv(8192)
        if not chunk:
            break

        resp.extend(chunk)

        if end_bytes and resp.endswith(end_bytes):
            break

    return resp.decode("utf-8", errors=errors)


def listen_socket(
    sock: socket.socket, errors: Literal["strict", "replace", "ignore"] = "strict"
) -> Generator[str, None, None]:
    """
    Listen to the socket.
    This function is a generator.

    Args:
        sock: An instance of a socket.
        errors: The error handling scheme that will be passed to :py:meth:`bytes.decode`.

    Returns:
        A generator that yields responses from the socket.

    Example usage:

    .. code-block:: python

        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.connect("path/to/socket.sock")

            for message in utils.listen_socket(sock):
                print(message)
    """

    buffer = b""
    while True:
        new_data = sock.recv(8192)
        if not new_data:
            break
        buffer += new_data
        while b"\n" in buffer:
            data, buffer = buffer.split(b"\n", 1)
            yield data.decode("utf-8", errors=errors)
