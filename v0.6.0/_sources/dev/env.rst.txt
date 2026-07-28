Setting up a Development Environment
=====================================

This guide with walk you through process of setting up a Development Environment for working on Ignis.

Source
------

Firstly, you have to grab the Ignis sources:

.. code-block:: bash

    # replace with the actual URL of your fork (if needed)
    git clone https://github.com/ignis-sh/ignis.git
    cd ignis

Virtual Environment
-------------------

It's always a good practice to work within a Python virtual environment.

.. code-block:: bash

    python -m venv venv
    source venv/bin/activate  # for fish: . venv/bin/activate.fish

Editable install
----------------

Editable installs let you modify the source code directly in the repository
and the changes take effect immediately without reinstalling the package.

You can install Ignis in editable mode using ``pip`` with ``-e`` flag:

.. code-block:: bash

    pip install -e .

Additionally, you can install useful development tools by running:

.. code-block:: bash

    pip install -r dev.txt
