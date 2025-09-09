# Ignis

[![docs](https://github.com/ignis-sh/ignis/actions/workflows/latest_docs.yaml/badge.svg)](https://github.com/ignis-sh/ignis/actions/workflows/latest_docs.yaml)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Linting: Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

A widget framework for building desktop shells, written and configurable in Python.

- Easy to use
- GTK4-based
- Batteries Included (a lot of built-in Services and Utilities!)
- Flexible work with widgets

> [!NOTE]
> Ignis is mostly stable, but still a work in progress.
> The API is a subject to change.
>
> The breaking changes tracker is available in [#60](https://github.com/ignis-sh/ignis/issues/60)

## Getting started
See the [Documentation](https://ignis-sh.github.io/ignis)

## Supported Desktops
- wlroots-based Wayland compositors (e.g., __Sway__) 
- __Hyprland__
- Smithay based compositors (e.g., __COSMIC__)
- __KDE Plasma__ on wayland

...and all other compositors that implement the Layer Shell protocol.

Ignis __is not supported__ on:
- GNOME Wayland
- X11

...because they don't support the Layer Shell protocol.

## Examples
* A simple bar, see [examples](./examples/bar)
![simple-bar](./examples/bar/simple-bar.png)

* [My own configuration](https://github.com/linkfrg/dotfiles/)
![My own configuration](https://github.com/linkfrg/dotfiles/blob/main/assets/1.png?raw=true)

## Contributing
Check out the [Developer Guide](https://ignis-sh.github.io/ignis/latest/dev/index.html)

## Licensing
Ignis is licensed under the __LGPL-2.1-or-later__.

## Special Thanks
[AGS](https://github.com/aylur/ags) - for inspiration
