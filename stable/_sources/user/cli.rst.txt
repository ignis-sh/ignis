CLI
==============

.. important::
   Python is **not** the fastest language, particularly when it comes to **startup time**.

   You may notice a **significant** delay in the Ignis built-in CLI (around 160ms just to display the help message!).
   For better performance, there's an optional CLI written in **Go**: `goignis <https://github.com/ignis-sh/goignis>`_, which offers excellent speed.

Run ``ignis --help`` to view the CLI usage help message.

.. click:: ignis.cli:cli
   :prog: ignis
   :nested: full