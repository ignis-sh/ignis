from typing import TypeAlias
from .window import Window
from .label import Label
from .button import Button
from .box import Box
from .calendar import Calendar
from .scale import Scale
from .icon import Icon
from .picture import Picture
from .centerbox import CenterBox
from .revealer import Revealer
from .scroll import Scroll
from .entry import Entry
from .switch import Switch
from .separator import Separator
from .toggle_button import ToggleButton
from .regular_window import RegularWindow
from .file_chooser_button import FileChooserButton
from .file_filter import FileFilter
from .file_dialog import FileDialog
from .grid import Grid
from .popover_menu import PopoverMenu
from .eventbox import EventBox
from .headerbar import HeaderBar
from .listboxrow import ListBoxRow
from .listbox import ListBox
from .check_button import CheckButton
from .spin_button import SpinButton
from .dropdown import DropDown
from .overlay import Overlay
from .arrow import Arrow
from .arrow_button import ArrowButton
from .revealer_window import RevealerWindow
from .stack import Stack
from .stack_switcher import StackSwitcher
from .stack_page import StackPage
from .animated_gif import AnimatedGif
from ignis._deprecation import deprecated_getattribute
from .corner import Corner


@deprecated_getattribute(
    """The "Widget" class is deprecated, please use "from ignis import widgets" instead."""
)
class Widget:
    Window: TypeAlias = Window
    Label: TypeAlias = Label
    Button: TypeAlias = Button
    Box: TypeAlias = Box
    Calendar: TypeAlias = Calendar
    Scale: TypeAlias = Scale
    Icon: TypeAlias = Icon
    CenterBox: TypeAlias = CenterBox
    Revealer: TypeAlias = Revealer
    Scroll: TypeAlias = Scroll
    Entry: TypeAlias = Entry
    Switch: TypeAlias = Switch
    Separator: TypeAlias = Separator
    ToggleButton: TypeAlias = ToggleButton
    RegularWindow: TypeAlias = RegularWindow
    FileChooserButton: TypeAlias = FileChooserButton
    FileFilter: TypeAlias = FileFilter
    Grid: TypeAlias = Grid
    PopoverMenu: TypeAlias = PopoverMenu
    EventBox: TypeAlias = EventBox
    FileDialog: TypeAlias = FileDialog
    HeaderBar: TypeAlias = HeaderBar
    ListBoxRow: TypeAlias = ListBoxRow
    ListBox: TypeAlias = ListBox
    Picture: TypeAlias = Picture
    CheckButton: TypeAlias = CheckButton
    SpinButton: TypeAlias = SpinButton
    DropDown: TypeAlias = DropDown
    Overlay: TypeAlias = Overlay
    Arrow: TypeAlias = Arrow
    ArrowButton: TypeAlias = ArrowButton
    RevealerWindow: TypeAlias = RevealerWindow
    Stack: TypeAlias = Stack
    StackSwitcher: TypeAlias = StackSwitcher
    StackPage = StackPage
    AnimatedGif: TypeAlias = AnimatedGif
    Corner: TypeAlias = Corner


__all__ = [
    "Arrow",
    "ArrowButton",
    "Box",
    "Button",
    "Calendar",
    "CenterBox",
    "CheckButton",
    "Corner",
    "DropDown",
    "Entry",
    "EventBox",
    "FileChooserButton",
    "FileDialog",
    "FileFilter",
    "Grid",
    "HeaderBar",
    "Icon",
    "Label",
    "ListBox",
    "ListBoxRow",
    "Overlay",
    "Picture",
    "PopoverMenu",
    "RegularWindow",
    "Revealer",
    "RevealerWindow",
    "Scale",
    "Scroll",
    "Separator",
    "SpinButton",
    "Stack",
    "StackPage",
    "StackSwitcher",
    "Switch",
    "ToggleButton",
    "Window",
    "AnimatedGif",
]
