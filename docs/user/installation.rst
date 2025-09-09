Installation
============

Arch Linux
-----------

Install the package from AUR.

.. code-block:: bash

    paru -S python-ignis

For the latest (git) version of Ignis install ``python-ignis-git``.

.. code-block:: bash

    paru -S python-ignis-git

Nix
---

Read more on the `Nix page <nix.html>`_.

Void Linux
----------

An ``xbps-src`` template is available in a `third party repository <https://github.com/binarylinuxx/ignis-xbps-src>`_
with `prebuilt packages <https://github.com/binarylinuxx/ignis-xbps-src/tree/x86_64-glibc>`_ too.

Add this repository by creating ``ignis.conf`` at ``/etc/xbps.d/``:

.. tab-set::

    .. tab-item:: /etc/xbps.d/ignis.conf

        .. code-block::

            repository=https://raw.githubusercontent.com/binarylinuxx/ignis-xbps-src/x86_64-glibc/pkgs

Then, you can install Ignis as a usual package using ``xbps-install``.

.. code-block:: bash

    sudo xbps-install -S ignis

Pip
----

Pip is the standard package manager for Python.
You can install Ignis directly from the Git repository using Pip.

.. hint::

    You can do this in a Python virtual environment.
    Create and activate one with the following commands:

    .. code-block:: bash

        python -m venv venv
        source venv/bin/activate  # for fish: . venv/bin/activate.fish

To install the latest (Git) version of Ignis:

.. code-block:: bash

    pip install git+https://github.com/ignis-sh/ignis.git

To install a specific version (e.g., ``v0.5``):

.. code-block:: bash

    # replace "TAG" with the desired Git tag
    pip install git+https://github.com/ignis-sh/ignis.git@TAG

.. seealso::

    For advanced usage, you can `set up a development environment <../dev/env.html>`_ and install Ignis in editable mode.
    This allows you to easily switch between commits, versions, branches, or pull requests using `git`, without having to reinstall Ignis.
