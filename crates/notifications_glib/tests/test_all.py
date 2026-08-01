import asyncio
import random
import string

import gi
import pytest

gi.require_version("IgnisNotificationsGLib", "0.1")
from gi.events import GLibEventLoopPolicy  # noqa: E402
from gi.repository import (  # noqa: E402
    Gio,  # type: ignore
    GLib,  # type: ignore
    IgnisNotificationsGLib,  # type: ignore
)


def generate_random_string() -> str:
    return "".join(random.choices(string.ascii_letters, k=20))


async def send_random_notification() -> tuple[str, str]:
    summary = generate_random_string()
    body = generate_random_string()

    proc = await asyncio.create_subprocess_exec(
        "notify-send",
        summary,
        body,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await proc.communicate()

    if proc.returncode != 0:
        print(stdout)
        print(stderr)

    assert proc.returncode == 0
    # TODO: return a dataclass containing sent notification info
    # also, generate random app name, icon, urgency, replace id, timeout
    return summary, body


@pytest.fixture(scope="session", autouse=True)
def setup_asyncio():
    asyncio.set_event_loop_policy(GLibEventLoopPolicy())


@pytest.fixture
def run_in_glib():
    def run(coro):
        mainloop = GLib.MainLoop()
        exception = None

        async def wrapper():
            return await coro

        def done(task):
            nonlocal exception
            try:
                task.result()
            except Exception as e:
                exception = e
            finally:
                mainloop.quit()

        def start():
            task = asyncio.create_task(wrapper())
            task.add_done_callback(done)

        GLib.idle_add(start)
        mainloop.run()

        if exception:
            raise exception

    return run


@pytest.fixture
def notification_service(run_in_glib):
    service = None

    async def start():
        nonlocal service
        service = IgnisNotificationsGLib.Service.new()
        await service.run_async()

    run_in_glib(start())

    yield service


def test_notify(run_in_glib, notification_service):
    async def test():
        summary, body = await send_random_notification()
        latest = notification_service.get_notifications()[-1]

        assert latest.get_summary() == summary
        assert latest.get_body() == body
        assert hasattr(latest, "dismiss_async")

    run_in_glib(test())


def test_property(notification_service):
    assert isinstance(notification_service.props.notifications, Gio.ListStore)
    for i in notification_service.get_property("notifications"):
        assert isinstance(i, IgnisNotificationsGLib.Notification)


def test_signals(run_in_glib, notification_service):
    received_signal_notified: bool = False
    received_notify_notifications: bool = False

    def on_notify_notification(_, __):
        nonlocal received_notify_notifications
        received_notify_notifications = True

    def on_new_notification(x, id_, notification, replace):
        nonlocal received_signal_notified
        received_signal_notified = True
        assert isinstance(notification, IgnisNotificationsGLib.Notification)

    async def test():
        notification_service.connect("notified", on_new_notification)
        notification_service.connect("notify::notifications", on_notify_notification)
        await send_random_notification()

    run_in_glib(test())

    assert received_signal_notified
    assert received_notify_notifications


def test_notification_properties(run_in_glib, notification_service):
    async def test():
        await send_random_notification()
        latest = notification_service.props.notifications[-1]

        assert isinstance(latest.get_id(), int)
        assert isinstance(latest.get_app_name(), str)
        assert isinstance(latest.get_icon(), str)
        assert isinstance(latest.get_summary(), str)
        assert isinstance(latest.get_body(), str)
        assert isinstance(latest.get_actions(), list)
        assert isinstance(latest.get_urgency(), IgnisNotificationsGLib.Urgency)
        assert isinstance(latest.get_timeout(), int)

        assert latest.props.id == latest.get_id()
        assert latest.props.app_name == latest.get_app_name()
        assert latest.props.icon == latest.get_icon()
        assert latest.props.summary == latest.get_summary()
        assert latest.props.body == latest.get_body()
        assert latest.props.urgency == latest.get_urgency()
        assert latest.props.timeout == latest.get_timeout()
        assert isinstance(latest.props.actions, Gio.ListStore)

    run_in_glib(test())


def test_dismiss_notification(run_in_glib, notification_service):
    id_: int = -1
    closed_emitted: bool = False

    def on_closed(x, closed_id, reason):
        nonlocal id_, closed_emitted

        assert id_ == closed_id
        assert reason == IgnisNotificationsGLib.CloseReason.DISMISSED
        closed_emitted = True

    async def test():
        nonlocal id_
        await send_random_notification()

        notification_service.connect("closed", on_closed)

        latest = notification_service.get_notifications()[-1]
        id_ = latest.props.id

        await notification_service.dismiss_notification_async(id_)

    run_in_glib(test())

    assert closed_emitted


def test_dismiss_notification_2(run_in_glib, notification_service):
    closed_emitted: bool = False

    def on_closed(x, reason):
        nonlocal closed_emitted

        assert reason == IgnisNotificationsGLib.CloseReason.DISMISSED
        closed_emitted = True

    async def test():
        await send_random_notification()

        latest = notification_service.get_notifications()[-1]
        latest.connect("closed", on_closed)
        await latest.dismiss_async()

    run_in_glib(test())

    assert closed_emitted


def test_sorted(notification_service):
    notifications = notification_service.get_notifications()
    is_sorted = notifications == sorted(notifications, key=lambda x: x.get_id())
    assert is_sorted


def test_clear_notifications(run_in_glib, notification_service):
    notifications_cleared_emitted: bool = False

    def on_clear_all(_):
        nonlocal notifications_cleared_emitted
        notifications_cleared_emitted = True

    async def test():
        for _ in range(10):
            await send_random_notification()

        notification_service.connect("notifications-cleared", on_clear_all)
        await notification_service.clear_notifications_async()

        assert len(notification_service.props.notifications) == 0
        assert len(notification_service.get_notifications()) == 0

    run_in_glib(test())

    assert notifications_cleared_emitted


def test_urgency():
    assert hasattr(IgnisNotificationsGLib.Urgency, "LOW")
    assert hasattr(IgnisNotificationsGLib.Urgency, "NORMAL")
    assert hasattr(IgnisNotificationsGLib.Urgency, "CRITICAL")


def test_action():
    # TODO: call invoke action here
    assert hasattr(IgnisNotificationsGLib, "Action")
    assert hasattr(IgnisNotificationsGLib.Action, "get_notification_id")
    assert hasattr(IgnisNotificationsGLib.Action, "get_label")
    assert hasattr(IgnisNotificationsGLib.Action, "get_action_key")
    assert hasattr(IgnisNotificationsGLib.Action, "invoke_async")
    assert hasattr(IgnisNotificationsGLib.Action, "invoke_finish")


def test_settings(notification_service):
    notification_service.props.follow_xdg_timeout = False
    notification_service.props.default_timeout = 2000
    notification_service.props.expire_by_default = True

    assert notification_service.props.follow_xdg_timeout is False
    assert notification_service.props.default_timeout == 2000
    assert notification_service.props.expire_by_default is True


def test_error():
    assert hasattr(IgnisNotificationsGLib.Error, "DBUS_ERROR")
    assert hasattr(IgnisNotificationsGLib.Error, "NO_CONNECTION")
    assert hasattr(IgnisNotificationsGLib.Error, "IO_ERROR")
    assert hasattr(IgnisNotificationsGLib.Error, "JSON_ERROR")
    assert hasattr(IgnisNotificationsGLib.Error, "NOTIFICATION_NOT_FOUND")
    assert hasattr(IgnisNotificationsGLib.Error, "CONNECTION_INITIALIZED_TWICE")
