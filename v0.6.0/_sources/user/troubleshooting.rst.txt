Troubleshooting
================

Cannot view children of ``widgets.Scroll`` 
------------------------------------------

Set ``min-height: 100px;`` or ``min-width: 100px;`` to your ``widgets.Scroll`` in CSS.
Where ``100px`` you can set any value.

Alternatively, set ``vexpand=True`` or ``hexpand=True`` to your ``widgets.Scroll``.

Render issues or Unresponsive UI after wake up from suspend
-----------------------------------------------------------

If you use Nvidia, see this: `Preserve video memory after suspend <https://wiki.archlinux.org/title/NVIDIA/Tips_and_tricks#Preserve_video_memory_after_suspend>`_.
