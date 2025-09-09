from typing import TypeVar

_SingletonT = TypeVar("_SingletonT", bound="IgnisSingleton")


class IgnisSingleton:
    """
    The singleton class.
    """

    _instance: _SingletonT | None = None  # type: ignore

    @classmethod
    def get_default(cls: type[_SingletonT]) -> _SingletonT:
        """
        Returns the default instance for this process, creating it if necessary.
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
