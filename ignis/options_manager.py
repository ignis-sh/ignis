import json
from ignis.gobject import IgnisGObject, Binding, IgnisProperty, IgnisSignal
from ignis import utils
from typing import Any, TypeVar
from collections.abc import Callable
from collections.abc import Generator
from ignis import is_sphinx_build

T = TypeVar("T")


class TrackedList(list[T]):
    """
    Bases: :class:`list`.

    The same as a usual Python list, but it can emit ``changed`` signal
    for the :class:`OptionsGroup` attribute in which it is stored when the list's elements change.

    .. code-block:: python

        from ignis.options_manager import OptionsGroup, TrackedList

        class SomeGroup(OptionsGroup):
            some_list: TrackedList = TrackedList()

        group = SomeGroup()
        group.connect_option("some_list", lambda: print(f"changed!: {group.some_list}"))
        group.some_list.append(123)
    """

    def __init__(
        self, owner: "OptionsGroup | None" = None, name: str | None = None, *args
    ):
        super().__init__(*args)
        self._owner = owner
        self._name = name

    @property
    def owner(self) -> "OptionsGroup | None":
        return self._owner

    @property
    def name(self) -> str | None:
        return self._name

    def __notify(self) -> None:
        if self._owner and self._name:
            obj = self._owner._instance
            new_list: TrackedList = TrackedList(self._owner, self._name, self)
            setattr(obj, self._name, new_list)

    def __set_name__(self, owner, name):
        self._owner = owner
        self._name = name

    def append(self, item):
        """
        :meta private:
        """
        super().append(item)
        self.__notify()

    def extend(self, iterable):
        """
        :meta private:
        """
        super().extend(iterable)
        self.__notify()

    def insert(self, index, item):
        """
        :meta private:
        """
        super().insert(index, item)
        self.__notify()

    def remove(self, item):
        """
        :meta private:
        """
        super().remove(item)
        self.__notify()

    def pop(self, index=-1):
        """
        :meta private:
        """
        item = super().pop(index)
        self.__notify()
        return item

    def clear(self):
        """
        :meta private:
        """
        super().clear()
        self.__notify()

    def __setitem__(self, index, value):
        """
        :meta private:
        """
        super().__setitem__(index, value)
        self.__notify()

    def __delitem__(self, index):
        """
        :meta private:
        """
        super().__delitem__(index)
        self.__notify()


class Option(IgnisGObject):
    """
    :meta private:

    The class for simulating a GObject that represents an option and its value,
    need for OptionsGroup.bind()
    """

    def __init__(self, manager: "OptionsGroup", name: str):
        super().__init__()
        self._manager = manager
        self._name = name

        self._manager.connect("changed", self.__check)

    def __check(self, manager, name: str) -> None:
        if name == self._name:
            self.notify("value")

    @IgnisProperty
    def value(self):
        return getattr(self._manager, self._name)


class OptionsGroup(IgnisGObject):
    """
    An options group.
    Implements the Singleton pattern.
    """

    # Singleton is required for TrackedList.__notify()
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        super().__init__()
        self._modified_options: dict[str, Any] = {}

        for subgroup_name, subgroup in self.__yield_subgroups():
            subgroup.connect(
                "changed",
                lambda x, option_name, subgroup_name=subgroup_name: self.emit(
                    "subgroup-changed", subgroup_name, option_name
                ),
            )
            subgroup.connect("autosave", lambda *_: self.emit("autosave"))

    @IgnisSignal
    def changed(self, option_name: str):
        """
        Emitted when an option of this group has changed

        Args:
            option_name: The name of the option.
        """

    @IgnisSignal
    def subgroup_changed(self, subgroup_name: str, option_name: str):
        """
        Emitted when an option of a subgroup has changed

        Args:
            subgroup_name: The name of the subgroup.
            option_name: The name of the option.
        """

    @IgnisSignal
    def autosave(self):
        """
        Emitted when changes to this group or its child subgroups are going to be saved to the file.
        """

    def bind(self, property_name: str, transform: Callable | None = None) -> Binding:
        """
        :meta private:

        Creates a fake GObject that represents an option
        and makes Binding for it
        """
        opt_obj = Option(self, property_name.replace("-", "_"))
        return opt_obj.bind("value", transform)

    def connect_option(self, option_name: str, callback: Callable, *args) -> None:
        """
        Connect an option change event to the specified `callback`.

        This method serves as a replacement for the ``notify`` signal, as options are simple Python properties, not GObject properties.

        Args:
            option_name: The name of the option to connect.
            callback: The function to invoke when the value of the option changes.

        Any ``*args`` will be passed to the ``callback``.
        """
        option_name = option_name.replace("-", "_")
        self.connect(
            "changed", lambda x, name: callback(*args) if option_name == name else None
        )

    def to_dict(self) -> dict[str, Any]:
        """
        Returns a dictionary representation of all options and subgroups.
        """
        data = {}

        for key in self.__class__.__dict__.keys():
            if not key.startswith("_"):
                value = getattr(self, key)
                if not isinstance(value, type) and not callable(value):
                    data[key] = value

        for name, manager in self.__yield_subgroups():
            data[name] = manager.to_dict()

        return data

    def get_modified_options(self) -> dict[str, Any]:
        """
        Get a dictionary representation of modified options and subgroups.
        """
        data = self._modified_options.copy()
        for name, manager in self.__yield_subgroups():
            data[name] = manager.get_modified_options()

        return data

    def apply_from_dict(
        self, data: dict[str, Any], emit: bool = True, autosave: bool = True
    ) -> None:
        """
        Apply values to options from a dictionary.

        Args:
            data: A dictionary containing the values to apply.
            emit: Whether to emit the :attr:`changed `and :attr:`subgroup_changed` signals for options in `data` that differ from those on `self`.
            autosave: Whether to automatically save changes to the file.
        """
        for key, value in data.items():
            if not hasattr(self, key):
                continue

            attr = getattr(self, key)

            if isinstance(attr, OptionsGroup):
                attr.apply_from_dict(value, emit, autosave)
            else:
                if attr != value:
                    if isinstance(attr, TrackedList) and isinstance(value, list):
                        # replace TrackedList with new TrackedList with the same owner and name, but with new value
                        # so it will not be overwritten by usual python list
                        value = TrackedList(attr.owner, attr.name, value)
                    self.__setattr__(key, value, emit, autosave)

    def __yield_subgroups(
        self,
    ) -> Generator[tuple[str, "OptionsGroup"], None, None]:
        for key, value in type(self).__dict__.items():
            if key.startswith("__"):
                continue
            if isinstance(value, OptionsGroup):
                # _instance contain self, and it can cause recursion
                if value != self:
                    yield key, value

    def __setattr__(
        self, name: str, value: Any, emit: bool = True, autosave: bool = True
    ) -> None:
        if not name.startswith("_"):
            self._modified_options[name] = value
            if emit:
                self.emit("changed", name)
            if autosave:
                self.emit("autosave")

        return super().__setattr__(name, value)

    def __getattribute__(self, name: str) -> Any:
        if name.startswith("set_"):
            property_name = name.replace("set_", "")
            if hasattr(self, property_name):
                return lambda value: setattr(self, property_name, value)
        elif name.startswith("get_"):
            property_name = name.replace("get_", "")
            if hasattr(self, property_name):
                return lambda: getattr(self, property_name)

        return super().__getattribute__(name)


class OptionsManager(OptionsGroup):
    """
    Bases: :class:`OptionsGroup`.

    This is the top-level class in the option structure.
    It provides support for loading and saving options to a file.
    Has support for hot-reloading when the file is modified externally.

    Args:
        file: The path to the file used for saving and loading options. Cannot be changed after initialization.
        hot_reload: Whether to enable hot-reloading.

    .. hint::
        The recommended directory for storing the options file is :obj:`ignis.DATA_DIR`.

    The standard option structure must follow this format:

    .. code-block:: python

        from ignis.options_manager import OptionsManager, OptionsGroup, TrackedList

        class SomeOptions(OptionsManager):
            def __init__(self):
                super().__init__(file="PATH/TO/FILE")

            class Subgroup1(OptionsGroup):
                option1: bool = False
                option2: int = 5000

            class SomeSubgroup(OptionsGroup):
                example_option: str | None = get_something...()
                test: str = "%Y-%m-%d_%H-%M-%S.mp4"
                # using TrackedList instead of usual python list is encouraged
                some_list: TrackedList[int] = TrackedList()


            subgroup1 = Subgroup1()
            some_subgroup = SomeSubgroup()

        some_options = SomeOptions()

    """

    def __init__(self, file: str | None = None, hot_reload: bool = True):
        super().__init__()
        self._file = file

        if not is_sphinx_build and self._file is not None:
            self.connect("autosave", self.__autosave)

            self.load_from_file(self._file, emit=False)

            if hot_reload:
                utils.FileMonitor(path=self._file, callback=self.__hot_reload)

    def __hot_reload(self, x, path: str, event_type: str) -> None:
        if not self._file:
            return

        if event_type != "changes_done_hint":
            return

        with open(self._file) as fp:
            data = json.load(fp)

        self.apply_from_dict(data, autosave=False)

    def __autosave(self, *args) -> None:
        self.save_to_file(self._file)  # type: ignore

    def save_to_file(self, file: str) -> None:
        """
        Manually save options to the specified file.

        Args:
            file: The path to the file where options will be saved.
        """
        with open(file, "w") as fp:
            json.dump(self.get_modified_options(), fp, indent=4)

    def load_from_file(self, file: str, emit: bool = True) -> None:
        """
        Manually load options from the specified file.

        Args:
            file: The path to the file from which options will be loaded.
            emit: Whether to emit the :attr:`changed `and :attr:`subgroup_changed` signals for options in `file` that differ from those on `self`.
        """
        with open(file) as fp:
            data = json.load(fp)
            self.apply_from_dict(data=data, emit=emit, autosave=False)
