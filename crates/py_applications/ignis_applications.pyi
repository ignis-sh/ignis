"""
Access desktop application entries defined according to the [XDG Desktop Entry Specification](https://specifications.freedesktop.org/desktop-entry/latest).

### Example
```python

from ignis_applications import ApplicationService

service = ApplicationService()

# display names of all applications
for i in service.apps:
    print(i.name)

# Fuzzy search by name
firefox = service.search_by_name("firfx")

# Launch application
firefox.launch()

# See actions

for action in firefox.actions:
    print(action.name)

    # Launch action
    # action.launch()

```
"""

from typing import final

@final
class Action:
    """
    A desktop application action.
    """
    @property
    def exec(self, /) -> str |None:
        """
        The exec string of the action.
        """
    @property
    def icon(self, /) -> str |None:
        """
        The icon of the action.
        """
    @property
    def icon_locale(self, /) -> str |None:
        """
        The localized icon of the action.
        """
    def launch(self, /) -> None:
        """
        Launches the action.
        """
    @property
    def name(self, /) -> str:
        """
        The name of the action.
        
        For example: `Launch in new window`.
        """
    @property
    def name_locale(self, /) -> str:
        """
        The localized name of the action.
        """

@final
class ApplicationService:
    """
    A service to access desktop applications.
    It loads all application entries from `XDG_DATA_DIRS` and gets the system locale.
    """
    def __new__(cls, /) -> ApplicationService: ...
    @property
    def apps(self, /) -> list[DesktopApp]:
        """
        A list of applications.
        """
    def get_app_by_id(self, /, app_id: str) -> DesktopApp |None:
        """
        An application by its ID, or `None` if it is not found.
        """
    def search_by_name(self, /, query: str) -> list[DesktopApp]:
        """
        Fuzzily search through the application entries by provided application name.
        """
    def watch(self, /) -> None:
        """
        Starts watching for changes in application entries. Re-initializes apps if a change occurs.
        """

@final
class DesktopApp:
    """
    A desktop application.
    """
    @property
    def actions(self, /) -> list[Action]:
        """
        A list of application actions. Can be empty.
        """
    @property
    def app_id(self, /) -> str:
        """
        The unique ID of the application.
        """
    @property
    def exec(self, /) -> str |None:
        """
        The string containing the program to execute, possibly with arguments.
        """
    @property
    def generic_name(self, /) -> str |None:
        """
        The generic name of the application.
        
        For example: `Web browser`.
        """
    @property
    def generic_name_locale(self, /) -> str |None:
        """
        The localized generic name of the application.
        """
    @property
    def icon(self, /) -> str |None:
        """
        The icon of the application.
        
        It's either the name of the icon or the absolute path.
        """
    @property
    def icon_locale(self, /) -> str |None:
        """
        The localized icon of the application.
        """
    @property
    def keywords(self, /) -> list[str]:
        """
        A list of keywords describing the application.
        """
    @property
    def keywords_locale(self, /) -> list[str]:
        """
        A list of localized keywords describing the application.
        """
    def launch(self, /) -> None:
        """
        Launches the application based on the [`exec`][exec] string.
        
        Starts a default terminal window if [`terminal`][terminal] is `true`.
        
        The launched child process is detached from this process.
        """
    @property
    def name(self, /) -> str:
        """
        The name of the application.
        
        For example: `firefox`.
        """
    @property
    def name_locale(self, /) -> str:
        """
        The localized name of the application.
        """
    @property
    def terminal(self, /) -> bool:
        """
        Whether the program should run in a terminal window.
        """
