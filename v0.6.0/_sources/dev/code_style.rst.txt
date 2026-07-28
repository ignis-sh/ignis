Code Style Guidelines
========================

Code Formatting
-------------------

All code must be formatted using `Ruff <https://github.com/astral-sh/ruff>`_.

Type checking
-----------------

The use of type hints is encouraged, 
and all code must be checked using `mypy <https://mypy-lang.org/>`_.

Commit messages
----------------

Commit messages should follow the `Conventional Commits <https://www.conventionalcommits.org/en/v1.0.0/#summary>`_.

Versioning
----------------

Ignis follows `Semantic Versioning <https://semver.org/>`_.

Definitions and Naming
-----------------------

Use the following naming conventions for different purposes:

- ``snake_case``: Functions, variables, GObject properties (except D-Bus methods/properties)
- ``SCREAMING_SNAKE_CASE``: Constants
- ``PascalCase``: Classes, D-Bus methods/properties
- ``kebab-case``: GObject signals