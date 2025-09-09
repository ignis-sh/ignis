import asyncio
from ignis import widgets
from .util import get_wifi_connect_window_name
from collections.abc import Callable


class WifiConnectDialog(widgets.RegularWindow):
    """
    :meta private:
    """

    def __init__(self, access_point, callback: Callable | None = None) -> None:
        self._password_entry = widgets.Entry(
            visibility=False,
            hexpand=True,
            on_accept=lambda x: asyncio.create_task(self.__connect_to()),
        )
        self._access_point = access_point
        self._callback = callback
        super().__init__(
            resizable=False,
            width_request=400,
            height_request=200,
            namespace=get_wifi_connect_window_name(access_point.bssid),
            style="padding: 1rem;",
            child=widgets.Box(
                vertical=True,
                child=[
                    widgets.Box(
                        child=[
                            widgets.Icon(
                                icon_name="dialog-password",
                                pixel_size=48,
                                style="margin-bottom: 2rem; margin-right: 2rem; margin-left: 1rem; margin-top: 1rem;",
                            ),
                            widgets.Box(
                                vertical=True,
                                spacing=20,
                                child=[
                                    widgets.Label(
                                        label="Authentication required by Wi-Fi network",
                                        style="font-size: 1.1rem;",
                                    ),
                                    widgets.Label(
                                        label=f'Passwords or encryption keys are required to access the Wi-Fi network "{access_point.ssid}".',
                                        wrap=True,
                                        max_width_chars=30,
                                        style="font-weight: normal;",
                                    ),
                                ],
                            ),
                        ]
                    ),
                    widgets.Box(
                        child=[widgets.Label(label="Password"), self._password_entry],
                        spacing=10,
                        style="margin-top: 1rem;",
                    ),
                    widgets.CheckButton(
                        label="Show password",
                        active=True,
                        on_toggled=lambda x,
                        active: self._password_entry.set_visibility(not active),
                        style="margin-left: 5.5rem; margin-top: 0.5rem;",
                    ),
                    widgets.Box(
                        vexpand=True,
                        valign="end",
                        halign="end",
                        spacing=10,
                        child=[
                            widgets.Button(
                                label="Cancel",
                                on_click=lambda x: self.unrealize(),
                            ),
                            widgets.Button(
                                sensitive=self._password_entry.bind(
                                    "text", lambda value: len(value) >= 8
                                ),
                                label="Connect",
                                on_click=lambda x: asyncio.create_task(
                                    self.__connect_to()
                                ),
                            ),
                        ],
                    ),
                ],
            ),
        )

    async def __connect_to(self) -> None:
        if len(self._password_entry.text) >= 8:
            conn = await self._access_point.connect_to(self._password_entry.text)
            if self._callback:
                self._callback(conn)
            self.unrealize()
