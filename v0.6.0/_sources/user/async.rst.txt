Asynchronous Programming
========================

Some I/O-bound and high-latency tasks can block the main thread and make your application unresponsive.
To work around this, it's better to run these tasks independently of the main program flow.
Asynchronous programming allows you to wait until a task is finished in the background while keeping your application responsive.

Ignis (and PyGObject in general) integrates with Python's :mod:`asyncio` module and provides convenient ``async/await`` syntax support.

Asynchronous functions in the Ignis documentation are prefixed with the ``async`` word before their name.

Calling Asynchronous Functions
-------------------------------

There are two common cases.

1. From a synchronous function

Use :func:`asyncio.create_task` to schedule execution.

.. code-block:: python
    
    import asyncio
    from ignis import utils

    asyncio.create_task(utils.exec_sh_async("notify-send 'asynchrony!'"))

2. From another asynchronous function

Use the ``await`` keyword to wait for execution.

.. code-block:: python
    
    import asyncio
    from ignis import utils

    async def some_func() -> None:
        await utils.exec_sh_async("notify-send 'asynchrony!'")

    # you still need create_task() because some_func is async
    asyncio.create_task(some_func())


Choosing the right approach
^^^^^^^^^^^^^^^^^^^^^^^^^^^

The best approach depends on your needs:

- If you need to retrieve the function's output and/or control execution order, define a custom async function and use await.
- Otherwise, if execution timing is not critical, use :func:`asyncio.create_task` to run the task in the background.

Cancelling tasks
----------------

Since :func:`asyncio.create_task` schedules execution for the future, you can cancel a task if needed.

.. code-block:: python

    task = asyncio.create_task(some_func())
    # cancel task
    task.cancel()

.. seealso::
    The following resources may be useful to you:

    - `PyGObject Asynchronous Guide <https://pygobject.gnome.org/guide/asynchronous.html>`_
    - :mod:`asyncio` documentation