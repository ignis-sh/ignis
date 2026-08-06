from gi.repository import Gio, GioUnix  # type: ignore
from ignis.base_service import BaseService
from .application import Application
from ignis.options import options
from ignis.gobject import IgnisProperty


class ApplicationsService(BaseService):
    """
    Provides a list of applications installed on the system.
    It also allows "pinning" of apps and retrieving a list of pinned applications.

    There are options available for this service: :class:`~ignis.options.Options.Applications`.

    Example usage:

    .. code-block:: python

        from ignis.services.applications import ApplicationsService

        applications = ApplicationsService.get_default()
        for i in applications.apps:
            print(i.name)

    """

    def __init__(self):
        super().__init__()
        self._apps: dict[str, Application] = {}

        self._monitor = Gio.AppInfoMonitor.get()
        self._monitor.connect("changed", lambda x: self.__sync())

        options.applications.connect_option(
            "pinned_apps", lambda: self.notify("pinned")
        )

        self.__sync()

    @IgnisProperty
    def apps(self) -> list[Application]:
        """
        A list of all installed applications.
        """
        return sorted(self._apps.values(), key=lambda x: x.name)

    @IgnisProperty
    def pinned(self) -> list[Application]:
        """
        A list of all pinned applications.
        """
        return [
            self._apps.get(name)  # type: ignore
            for name in options.applications.pinned_apps
            if name in self._apps
        ]

    def __sync(self) -> None:
        self._apps = {}

        for app in Gio.AppInfo.get_all():
            if isinstance(app, GioUnix.DesktopAppInfo):
                self.__add_app(app)

        self.notify("apps")
        self.notify("pinned")

    def __add_app(self, app: GioUnix.DesktopAppInfo) -> None:
        if app.get_nodisplay():
            return

        obj = Application(app=app)

        self._apps[obj.id] = obj

    @classmethod
    def search(
        cls,
        apps: list[Application],
        query: str,
    ) -> list[Application]:
        """
        Search applications by a query.

        Args:
            apps: A list of applications where to search, e.g., :attr:`~ignis.services.applications.ApplicationsService.apps`.
            query: The string to be searched for.

        Returns:
            list[Application]: A list of applications filtered by the provided query.
        """
        return [
            entry
            for result in GioUnix.DesktopAppInfo.search(query)
            for entry in apps
            if entry.id in result
        ]
