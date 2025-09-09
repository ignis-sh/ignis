from __future__ import annotations

import io
import sys
import loguru
import warnings
import asyncio
from loguru import logger
from gi.repository import GLib  # type: ignore

LOG_DIR = f"{GLib.get_user_state_dir()}/ignis"
LOG_FILE = f"{LOG_DIR}/ignis.log"
LOG_FORMAT = "{time:YYYY-MM-DD HH:mm:ss} [<level>{level}</level>] {message}"


G_LOG_LEVEL_FUNC = {
    GLib.LogLevelFlags.LEVEL_DEBUG: lambda message: logger.debug(message),
    # LEVEL_INFO logs are not very useful to print them to logger.info()
    GLib.LogLevelFlags.LEVEL_INFO: lambda message: logger.debug(message),
    GLib.LogLevelFlags.LEVEL_MESSAGE: lambda message: logger.info(message),
    GLib.LogLevelFlags.LEVEL_WARNING: lambda message: logger.warning(message),
    GLib.LogLevelFlags.LEVEL_ERROR: lambda message: logger.error(message),
    GLib.LogLevelFlags.LEVEL_CRITICAL: lambda message: logger.critical(message),
}


def logging_excepthook(exc_type, exc_value, exc_traceback):
    logger.opt(exception=(exc_type, exc_value, exc_traceback)).error(
        f"{exc_type.__name__}: {exc_value}"
    )


def async_exception_handler(loop, context):
    exception = context.get("exception")
    if exception:
        logging_excepthook(type(exception), exception, exception.__traceback__)
    else:
        logger.error(f"Caught an unhandled exception: {context}\n")


def g_log_writer(
    logs_level: GLib.LogLevelFlags, log_fields: list[GLib.LogField], gsize: int
) -> GLib.LogWriterOutput:
    message = GLib.log_writer_format_fields(logs_level, log_fields, False)

    func = G_LOG_LEVEL_FUNC.get(logs_level, None)
    if func is not None:
        func(message.strip())

    return GLib.LogWriterOutput.HANDLED


# source: https://github.com/Delgan/loguru/issues/540#issuecomment-1868010541
def rich_formatter(record: loguru.Record, force_terminal: bool = True) -> str:
    format_ = LOG_FORMAT + "\n"

    if record["exception"] is not None:
        # lazy load rich to reduce startup time
        from rich.traceback import Traceback
        from rich.console import Console

        output = io.StringIO()
        console = Console(file=output, force_terminal=force_terminal)
        traceback = Traceback.from_exception(*record["exception"])  # type: ignore
        console.print(traceback)
        record["extra"]["rich_exception"] = output.getvalue()
        format_ += "{extra[rich_exception]}"

    return format_


# source: https://github.com/Delgan/loguru/issues/554#issuecomment-998185211
def log_showwarning(message, category, filename, lineno, file=None, line=None):
    new_message = warnings.formatwarning(message, category, filename, lineno, line)
    logger.warning(new_message)


def configure_logger(debug: bool) -> None:
    logger.remove()

    if debug:
        LEVEL = "DEBUG"
    else:
        LEVEL = "INFO"

    logger.add(
        sys.stderr,
        level=LEVEL,
        format=lambda record: rich_formatter(record, True),
        colorize=True,
        backtrace=False,
        diagnose=False,
    )
    logger.add(
        LOG_FILE,
        level=LEVEL,
        # pass False to second arg to make traceback colorless in log file
        format=lambda record: rich_formatter(record, False),
        rotation="1 day",
        backtrace=False,
        diagnose=False,
    )

    logger.level("INFO", color="<green>")

    sys.excepthook = logging_excepthook

    loop = asyncio.get_event_loop()
    loop.set_exception_handler(async_exception_handler)

    GLib.log_set_writer_func(g_log_writer)

    warnings.showwarning = log_showwarning
