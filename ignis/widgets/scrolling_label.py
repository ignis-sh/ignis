from gi.repository import GLib  # type: ignore
from ignis.widgets import Label


class ScrollingLabel(Label):
    def __init__(self, label: str, max_length: int = 10, scroll_speed: int = 500, **kwargs):
        """
        :param text: Full text to be displayed.
        :param max_length: Maximum length of text in characters before scrolling.
        :param scroll_speed: Scrolling speed in milliseconds.
        :param css_classes: List of CSS classes to apply to the widget.
        :param justify: Method of text alignment.
        :param wrap: Specifies whether to wrap the text.
        :param wrap_mode: Text wrapping mode.
        :param kwargs: Additional arguments for the parent class.
        """
        self.full_text = label
        self.max_length = max_length
        self.current_index = 0
        self.scroll_speed = scroll_speed

        super().__init__(label=self._get_display_text(), **kwargs)

        if len(self.full_text) > self.max_length:
            self._start_scrolling()
        else:
            self.set_label(self.full_text)

    def _get_display_text(self) -> str:
        """
        Returns the current text for display with scrolling.
        If the text is too long, it will scroll.
        """
        if len(self.full_text) <= self.max_length:
            return self.full_text

        end_index = self.current_index + self.max_length
        if end_index <= len(self.full_text):
            return self.full_text[self.current_index:end_index]
        else:
            return (
                self.full_text[self.current_index:]
                + " "
                + self.full_text[: end_index - len(self.full_text)]
            )

    def _scroll_text(self):
        """
        Updates the index and text for scrolling.
        """
        self.current_index = (self.current_index + 1) % len(self.full_text)
        self.set_label(self._get_display_text())

    def _start_scrolling(self):
        """
        Starts a timer to automatically update the text for scrolling.
        """
        GLib.timeout_add(self.scroll_speed, self._scroll_text_and_continue)

    def _scroll_text_and_continue(self):
        """
        Wrapper to update the text and continue the timer.
        """
        self._scroll_text()
        return True
