from ignis.gobject import IgnisGObjectSingleton


# FIXME: Probably it should be deprecated due to its lack of utility.
# But I will leave it as is for now in case I find a meaningful use for it.
class BaseService(IgnisGObjectSingleton):
    """
    Bases: :class:`~ignis.gobject.IgnisGObjectSingleton`.

    The base class for all services.
    """
