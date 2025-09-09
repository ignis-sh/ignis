import re


def snake_to_pascal(string: str) -> str:
    """
    Convert a `snake_case` string to `PascalCase`.

    Args:
        string: the string to convert.
    """
    return string.replace("_", " ").title().replace(" ", "")


def pascal_to_snake(string: str) -> str:
    """
    Convert a `PascalCase` string to `snake_case`.

    Args:
        string: the string to convert.
    """
    return re.sub(r"(?<!^)(?=[A-Z])", "_", string).lower()
