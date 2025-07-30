from ignis._deprecation import deprecated

@deprecated("It returns an empty string now, use ignis._version module instead.")
def get_ignis_version() -> str:
    """
    .. deprecated:: 0.6
        It returns an empty string now, use ignis._version module instead.
    """
    return ""

@deprecated("It returns an empty string now, use ignis._version module instead.")
def get_ignis_commit() -> str:
    """
    .. deprecated:: 0.6
        It returns an empty string now, use ignis._version module instead.
    """
    return ""

@deprecated("It returns an empty string now, use ignis._version module instead.")
def get_ignis_branch() -> str:
    """
    .. deprecated:: 0.6
        It returns an empty string now, use ignis._version module instead.
    """
    return ""


@deprecated("It returns an empty string now, use ignis._version module instead.")
def get_ignis_commit_msg() -> str:
    """
    .. deprecated:: 0.6
        It returns an empty string now, use ignis._version module instead.
    """
    return ""
