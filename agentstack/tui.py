import curses
import signal
import time
import math
from random import randint
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, Union, Callable, Any
from enum import Enum
from pyfiglet import Figlet

from agentstack import conf, log


class RenderException(Exception):
    pass


# horizontal alignment
ALIGN_LEFT = "left"
ALIGN_CENTER = "center"
ALIGN_RIGHT = "right"

# vertical alignment
ALIGN_TOP = "top"
ALIGN_MIDDLE = "middle"
ALIGN_BOTTOM = "bottom"

# module positioning
POS_RELATIVE = "relative"
POS_ABSOLUTE = "absolute"


class Node:  # TODO this needs a better name
    """
    A simple data node that can be updated and have callbacks. This is used to
    populate and retrieve data from an input field inside the user interface.
    """

    value: Any
    callbacks: list[Callable]

    def __init__(self, value: Any = "") -> None:
        self.value = value
        self.callbacks = []

    def __str__(self):
        return str(self.value)

    def update(self, value: Any) -> None:
        self.value = value
        for callback in self.callbacks:
            callback(self)

    def add_callback(self, callback):
        self.callbacks.append(callback)

    def remove_callback(self, callback):
        self.callbacks.remove(callback)


class Key:
    const = {
        'UP': 259,
        'DOWN': 258,
        'BACKSPACE': 127,
        'TAB': 9,
        'ESC': 27,
        'ENTER': 10,
        'SPACE': 32,
        'PERIOD': 46,
        'PERCENT': 37,
        'MINUS': 45,
    }

    def __init__(self, ch: int):
        self.ch = ch

    def __getattr__(self, name):
        try:
            return self.ch == self.const[name]
        except KeyError:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    @property
    def chr(self):
        return chr(self.ch)

    @property
    def is_numeric(self):
        return self.ch >= 48 and self.ch <= 57

    @property
    def is_alpha(self):
        return self.ch >= 65 and self.ch <= 122


class Color:
    """
    Color class based on HSV color space, mapping directly to terminal color capabilities.

    Hue: 0-360 degrees, mapped to 6 primary directions (0, 60, 120, 180, 240, 300)
    Saturation: 0-100%, mapped to 6 levels (0, 20, 40, 60, 80, 100)
    Value: 0-100%, mapped to 6 levels for colors, 24 levels for grayscale
    """

    # TODO: fallback for 16 color mode
    # TODO: fallback for no color mode
    BACKGROUND = curses.COLOR_BLACK
    SATURATION_LEVELS = 12
    HUE_SEGMENTS = 6
    VALUE_LEVELS = 6
    GRAYSCALE_LEVELS = 24
    COLOR_CUBE_SIZE = 6  # 6x6x6 color cube

    reversed: bool = False
    bold: bool = False

    _color_map = {}  # Cache for color mappings

    def __init__(
        self, h: float, s: float = 100, v: float = 100, reversed: bool = False, bold: bool = False
    ) -> None:
        """
        Initialize color with HSV values.

        Args:
            h: Hue (0-360 degrees)
            s: Saturation (0-100 percent)
            v: Value (0-100 percent)
        """
        self.h = h % 360
        self.s = max(0, min(100, s))
        self.v = max(0, min(100, v))
        self.reversed = reversed
        self.bold = bold
        self._pair_number: Optional[int] = None

    def _get_closest_color(self) -> int:
        """Map HSV to closest available terminal color number."""
        # Handle grayscale case
        if self.s < 10:
            gray_val = int(self.v * (self.GRAYSCALE_LEVELS - 1) / 100)
            return 232 + gray_val if gray_val < self.GRAYSCALE_LEVELS else 231

        # Convert HSV to the COLOR_CUBE_SIZE x COLOR_CUBE_SIZE x COLOR_CUBE_SIZE color cube
        h = self.h
        s = self.s / 100
        v = self.v / 100

        # Map hue to primary and secondary colors (0 to HUE_SEGMENTS-1)
        h = (h + 330) % 360  # -30 degrees = +330 degrees
        h_segment = int((h / 60) % self.HUE_SEGMENTS)
        h_remainder = (h % 60) / 60

        # Get RGB values based on hue segment
        max_level = self.COLOR_CUBE_SIZE - 1
        if h_segment == 0:  # Red to Yellow
            r, g, b = max_level, int(max_level * h_remainder), 0
        elif h_segment == 1:  # Yellow to Green
            r, g, b = int(max_level * (1 - h_remainder)), max_level, 0
        elif h_segment == 2:  # Green to Cyan
            r, g, b = 0, max_level, int(max_level * h_remainder)
        elif h_segment == 3:  # Cyan to Blue
            r, g, b = 0, int(max_level * (1 - h_remainder)), max_level
        elif h_segment == 4:  # Blue to Magenta
            r, g, b = int(max_level * h_remainder), 0, max_level
        else:  # Magenta to Red
            r, g, b = max_level, 0, int(max_level * (1 - h_remainder))

        # Apply saturation
        max_rgb = max(r, g, b)
        if max_rgb > 0:
            # Map the saturation to the number of levels
            s_level = int(s * (self.SATURATION_LEVELS - 1))
            s_factor = s_level / (self.SATURATION_LEVELS - 1)

            r = int(r + (max_level - r) * (1 - s_factor))
            g = int(g + (max_level - g) * (1 - s_factor))
            b = int(b + (max_level - b) * (1 - s_factor))

        # Apply value (brightness)
        v = max(0, min(max_level, int(v * self.VALUE_LEVELS)))
        r = min(max_level, int(r * v / max_level))
        g = min(max_level, int(g * v / max_level))
        b = min(max_level, int(b * v / max_level))

        # Convert to color cube index (16-231)
        return int(16 + (r * self.COLOR_CUBE_SIZE * self.COLOR_CUBE_SIZE) + (g * self.COLOR_CUBE_SIZE) + b)

    def hue(self, h: float) -> 'Color':
        """Set the hue of the color."""
        return Color(h, self.s, self.v, self.reversed, self.bold)

    def sat(self, s: float) -> 'Color':
        """Set the saturation of the color."""
        return Color(self.h, s, self.v, self.reversed, self.bold)

    def val(self, v: float) -> 'Color':
        """Set the value of the color."""
        return Color(self.h, self.s, v, self.reversed, self.bold)

    def reverse(self) -> 'Color':
        """Set the reversed attribute of the color."""
        return Color(self.h, self.s, self.v, True, self.bold)

    def _get_color_pair(self, pair_number: int) -> int:
        """Apply reversing to the color pair."""
        pair = curses.color_pair(pair_number)
        if self.reversed:
            pair = pair | curses.A_REVERSE
        if self.bold:
            pair = pair | curses.A_BOLD
        return pair

    def to_curses(self) -> int:
        """Get curses color pair for this color."""
        if self._pair_number is not None:
            return self._get_color_pair(self._pair_number)

        color_number = self._get_closest_color()

        # Create new pair if needed
        if color_number not in self._color_map:
            pair_number = len(self._color_map) + 1
            curses.init_pair(pair_number, color_number, self.BACKGROUND)
            self._color_map[color_number] = pair_number
        else:
            pair_number = self._color_map[color_number]

        self._pair_number = pair_number
        return self._get_color_pair(pair_number)

    @classmethod
    def initialize(cls) -> None:
        """Initialize terminal color support."""
        if not curses.has_colors():
            raise RuntimeError("Terminal does not support colors")

        curses.start_color()
        curses.use_default_colors()

        try:
            curses.init_pair(1, 1, -1)
        except:
            raise RuntimeError("Terminal does not support required color features")

        cls._color_map = {}


class ColorAnimation(Color):
    start: Color
    end: Color
    reversed: bool = False
    bold: bool = False
    duration: float
    loop: bool
    _start_time: float

    def __init__(self, start: Color, end: Color, duration: float, loop: bool = False):
        super().__init__(start.h, start.s, start.v)
        self.start = start
        self.end = end
        self.duration = duration
        self.loop = loop
        self._start_time = time.time()

    def reset_animation(self):
        self._start_time = time.time()

    def to_curses(self) -> int:
        if self.reversed:
            self.start.reversed = True
            self.end.reversed = True
        elif self.start.reversed:
            self.reversed = True
        
        if self.bold:
            self.start.bold = True
            self.end.bold = True
        elif self.start.bold:
            self.bold = True
        
        elapsed = time.time() - self._start_time
        if elapsed > self.duration:
            if self.loop:
                self.start, self.end = self.end, self.start
                self.reset_animation()
                return self.start.to_curses()  # prevents flickering :shrug:
            else:
                return self.end.to_curses()

        t = elapsed / self.duration
        h1, h2 = self.start.h, self.end.h
        # take the shortest path
        diff = h2 - h1
        if abs(diff) > 180:
            if diff > 0:
                h1 += 360
            else:
                h2 += 360
        h = (h1 + t * (h2 - h1)) % 360

        # saturation and value
        s = self.start.s + t * (self.end.s - self.start.s)
        v = self.start.v + t * (self.end.v - self.start.v)

        return Color(h, s, v, reversed=self.reversed, bold=self.bold).to_curses()


class Renderable:
    _grid: Optional[curses.window] = None
    y: int
    x: int
    height: int
    width: int
    parent: Optional['Contains'] = None
    h_align: str = ALIGN_LEFT
    v_align: str = ALIGN_TOP
    color: Color
    last_render: float = 0
    padding: tuple[int, int] = (1, 1)
    positioning: str = POS_ABSOLUTE

    def __init__(self, coords: tuple[int, int], dims: tuple[int, int], color: Optional[Color] = None):
        self.y, self.x = coords
        self.height, self.width = dims
        self.color = color or Color(0, 100, 0)

    def __repr__(self):
        return f"{type(self)} at ({self.y}, {self.x})"

    @property
    def grid(self):
        # TODO cleanup
        # TODO validate that coords and size are within the parent window and give
        # an explanatory error message.
        if not self._grid:
            if self.parent:
                if self.positioning == POS_RELATIVE:
                    grid_func = self.parent.grid.derwin
                elif self.positioning == POS_ABSOLUTE:
                    grid_func = self.parent.grid.subwin
                else:
                    raise ValueError("Invalid positioning value")
            else:
                grid_func = curses.newwin

            self._grid = grid_func(
                self.height + self.padding[0], self.width + self.padding[1], self.y, self.x
            )  # TODO this cant be bigger than the window
            self._grid.bkgd(' ', curses.color_pair(1))
        return self._grid

    def move(self, y: int, x: int):
        self.y, self.x = y, x
        if self._grid:
            if self.positioning == POS_RELATIVE:
                self._grid.mvderwin(self.y, self.x)
            elif self.positioning == POS_ABSOLUTE:
                self._grid.mvwin(self.y, self.x)
            else:
                raise ValueError("Cannot move a root window")

    @property
    def abs_x(self):
        """Absolute X coordinate of this module"""
        if self.parent and not self.positioning == POS_ABSOLUTE:
            return self.x + self.parent.abs_x
        return self.x

    @property
    def abs_y(self):
        """Absolute Y coordinate of this module"""
        if self.parent and not self.positioning == POS_ABSOLUTE:
            return self.y + self.parent.abs_y
        return self.y

    def render(self):
        pass

    def hit(self, y, x):
        """Is the mouse click inside this module?"""
        return (
            y >= self.abs_y
            and y < self.abs_y + self.height
            and x >= self.abs_x
            and x < self.abs_x + self.width
        )

    def click(self, y, x):
        """Handle mouse click event."""
        pass

    def input(self, key: Key):
        """Handle key input event."""
        pass

    def destroy(self) -> None:
        if self._grid:
            self._grid.erase()
            self._grid.refresh()
            self._grid = None


class Element(Renderable):
    positioning: str = POS_RELATIVE
    word_wrap: bool = False

    def __init__(
        self,
        coords: tuple[int, int],
        dims: tuple[int, int],
        value: Optional[Any] = "",
        color: Optional[Color] = None,
    ):
        super().__init__(coords, dims, color=color)
        self.value = value

    def __repr__(self):
        return f"{type(self)} at ({self.y}, {self.x}) with value '{self.value[:20]}'"

    def _get_lines(self, value: str) -> list[str]:
        if self.word_wrap:
            splits = [''] * self.height
            words = value.split()
            for i in range(self.height):
                while words and (len(splits[i]) + len(words[0]) + 1) <= self.width:
                    splits[i] += f"{words.pop(0)} " if words else ''
        elif '\n' in value:
            splits = value.split('\n')
        else:
            splits = [
                value,
            ]

        if self.v_align == ALIGN_TOP:
            # add empty elements below
            splits = splits + [''] * (self.height - len(splits))
        elif self.v_align == ALIGN_MIDDLE:
            # add empty elements before and after the splits to center it
            pad = (self.height // 2) - (len(splits) // 2)
            splits = [''] * pad + splits + [''] * pad
        elif self.v_align == ALIGN_BOTTOM:
            splits = [''] * (self.height - len(splits)) + splits

        lines = []
        for line in splits:
            if self.h_align == ALIGN_LEFT:
                line = line.ljust(self.width)
            elif self.h_align == ALIGN_RIGHT:
                line = line.rjust(self.width)
            elif self.h_align == ALIGN_CENTER:
                line = line.center(self.width)

            lines.append(line[: self.width])
        return lines

    def render(self):
        for i, line in enumerate(self._get_lines(str(self.value))):
            self.grid.addstr(i, 0, line, self.color.to_curses())


class NodeElement(Element):
    format: Optional[Callable] = None

    def __init__(
        self,
        coords: tuple[int, int],
        dims: tuple[int, int],
        node: Node,
        color: Optional[Color] = None,
        format: Optional[Callable] = None,
    ):
        super().__init__(coords, dims, color=color)
        self.node = node  # TODO can also be str?
        self.value = str(node)
        self.format = format
        if isinstance(node, Node):
            self.node.add_callback(self.update)

    def update(self, node: Node):
        self.value = str(node)
        if self.format:
            self.value = self.format(self.value)

    def save(self):
        self.node.update(self.value)
        self.update(self.node)

    def destroy(self):
        if isinstance(self.node, Node):
            self.node.remove_callback(self.update)
        super().destroy()


class Editable(NodeElement):
    filter: Optional[Callable] = None
    active: bool
    _original_value: Any

    def __init__(
        self,
        coords,
        dims,
        node,
        color=None,
        format: Optional[Callable] = None,
        filter: Optional[Callable] = None,
    ):
        super().__init__(coords, dims, node=node, color=color, format=format)
        self.filter = filter
        self.active = False
        self._original_value = self.value

    def click(self, y, x):
        if not self.active and self.hit(y, x):
            self.activate()
        elif self.active:  # click off
            self.deactivate()
            self.save()

    def activate(self):
        """Make this module the active one; ie. editing or selected."""
        App.editing = True
        self.active = True
        self._original_value = self.value

    def deactivate(self, save: bool = True):
        """Deactivate this module, making it no longer active."""
        App.editing = False
        self.active = False
        if save:
            self.save()

    def save(self):
        if self.filter:
            self.value = self.filter(self.value)
        super().save()

    def input(self, key: Key):
        if not self.active:
            return

        if key.is_alpha or key.is_numeric or key.PERIOD or key.MINUS or key.SPACE:
            self.value = str(self.value) + key.chr
        elif key.BACKSPACE:
            self.value = str(self.value)[:-1]
        elif key.ESC:
            self.deactivate(save=False)
            self.value = self._original_value  # revert changes
        elif key.ENTER:
            self.deactivate()

    def destroy(self):
        self.deactivate()
        super().destroy()


class Text(Element):
    pass


class WrappedText(Text):
    word_wrap: bool = True


class ASCIIText(Text):
    default_font: str = "pepper"
    formatter: Figlet
    _ascii_render: Optional[str] = None  # rendered content
    _ascii_value: Optional[str] = None  # value used to render content

    def __init__(
        self,
        coords: tuple[int, int],
        dims: tuple[int, int],
        value: Optional[Any] = "",
        color: Optional[Color] = None,
        formatter: Optional[Figlet] = None,
    ):
        super().__init__(coords, dims, value=value, color=color)
        self.formatter = formatter or Figlet(font=self.default_font)

    def _get_lines(self, value: str) -> list[str]:
        if not self._ascii_render or self._ascii_value != value:
            # prevent rendering on every frame
            self._ascii_value = value
            self._ascii_render = self.formatter.renderText(value) or ""

        return super()._get_lines(self._ascii_render)


class BoldText(Text):
    def __init__(
        self,
        coords: tuple[int, int],
        dims: tuple[int, int],
        value: Optional[Any] = "",
        color: Optional[Color] = None,
    ):
        super().__init__(coords, dims, value=value, color=color)
        self.color.bold = True


class Title(BoldText):
    h_align: str = ALIGN_CENTER
    v_align: str = ALIGN_MIDDLE


class TextInput(Editable):
    """
    A module that allows the user to input text.
    """

    H, V, BR = "━", "┃", "┛"
    padding: tuple[int, int] = (2, 1)
    border_color: Color
    active_color: Color
    word_wrap: bool = True

    def __init__(
        self,
        coords: tuple[int, int],
        dims: tuple[int, int],
        node: Node,
        color: Optional[Color] = None,
        border: Optional[Color] = None,
        active: Optional[Color] = None,
        format: Optional[Callable] = None,
    ):
        super().__init__(coords, dims, node=node, color=color, format=format)
        self.width, self.height = (dims[1] - 1, dims[0] - 1)
        self.border_color = border or self.color
        self.active_color = active or self.color

    def activate(self):
        # change the border color to a highlight
        self._original_border_color = self.border_color
        self.border_color = self.active_color
        super().activate()

    def deactivate(self, save: bool = True):
        if self.active and hasattr(self, '_original_border_color'):
            self.border_color = self._original_border_color
        super().deactivate(save)

    def render(self) -> None:
        for i, line in enumerate(self._get_lines(str(self.value))):
            self.grid.addstr(i, 0, line, self.color.to_curses())

        # # add border to bottom right like a drop shadow
        for x in range(self.width):
            self.grid.addch(self.height, x, self.H, self.border_color.to_curses())
        for y in range(self.height):
            self.grid.addch(y, self.width, self.V, self.border_color.to_curses())
        self.grid.addch(self.height, self.width, self.BR, self.border_color.to_curses())


class Button(Element):
    h_align: str = ALIGN_CENTER
    v_align: str = ALIGN_MIDDLE
    active: bool = False
    selected: bool = False
    highlight: Optional[Color] = None
    on_confirm: Optional[Callable] = None
    on_activate: Optional[Callable] = None

    def __init__(
        self,
        coords: tuple[int, int],
        dims: tuple[int, int],
        value: Optional[Any] = "",
        color: Optional[Color] = None,
        highlight: Optional[Color] = None,
        on_confirm: Optional[Callable] = None,
        on_activate: Optional[Callable] = None,
    ):
        super().__init__(coords, dims, value=value, color=color)
        self.highlight = highlight or self.color.sat(80)
        self.on_confirm = on_confirm
        self.on_activate = on_activate

    def confirm(self):
        """Handle button confirmation."""
        if self.on_confirm:
            self.on_confirm()

    def activate(self):
        """Make this module the active one; ie. editing or selected."""
        self.active = True
        self._original_color = self.color
        self.color = self.highlight or self.color
        if hasattr(self.color, 'reset_animation'):
            self.color.reset_animation()
        if self.on_activate:
            self.on_activate(self.value)

    def deactivate(self, save: bool = True):
        """Deactivate this module, making it no longer active."""
        self.active = False
        if hasattr(self, '_original_color'):
            self.color = self._original_color

    def click(self, y, x):
        if self.hit(y, x):
            self.confirm()

    def input(self, key: Key):
        """Handle key input event."""
        if not self.active:
            return

        if key.ENTER or key.SPACE:
            self.confirm()


class RadioButton(Button):
    """A Button with an indicator that it is selected"""

    ON, OFF = "●", "○"
    selected: bool = False

    def render(self):
        super().render()
        icon = self.ON if self.selected else self.OFF
        self.grid.addstr(1, 2, icon, self.color.to_curses())


class CheckButton(RadioButton):
    """A Button with an indicator that it is selected"""

    ON, OFF = "■", "□"


class Contains(Renderable):
    _grid: Optional[curses.window] = None
    y: int
    x: int
    positioning: str = POS_RELATIVE
    padding: tuple[int, int] = (1, 0)
    color: Color
    last_render: float = 0
    parent: Optional['Contains'] = None
    modules: list[Renderable]

    def __init__(
        self,
        coords: tuple[int, int],
        dims: tuple[int, int],
        modules: list[Renderable],
        color: Optional[Color] = None,
    ):
        super().__init__(coords, dims, color=color)
        self.modules = []
        for module in modules:
            self.append(module)

    def append(self, module: Renderable):
        module.parent = self
        self.modules.append(module)

    def get_modules(self):
        """Override this to filter displayed modules"""
        return self.modules

    def render(self):
        for module in self.get_modules():
            module.render()
            module.last_render = time.time()
            module.grid.noutrefresh()
        self.last_render = time.time()

    def click(self, y, x):
        for module in self.modules:
            module.click(y, x)

    def input(self, key: Key):
        for module in self.modules:
            module.input(key)

    def destroy(self):
        for module in self.modules:
            module.destroy()
        self.grid.erase()
        self.grid.refresh()


class Box(Contains):
    """A container with a border"""

    H, V, TL, TR, BL, BR = "─", "│", "┌", "┐", "└", "┘"

    def render(self) -> None:
        w: int = self.width - 1
        h: int = self.height - 1

        for x in range(1, w):
            self.grid.addch(0, x, self.H, self.color.to_curses())
            self.grid.addch(h, x, self.H, self.color.to_curses())
        for y in range(1, h):
            self.grid.addch(y, 0, self.V, self.color.to_curses())
            self.grid.addch(y, w, self.V, self.color.to_curses())
        self.grid.addch(0, 0, self.TL, self.color.to_curses())
        self.grid.addch(h, 0, self.BL, self.color.to_curses())
        self.grid.addch(0, w, self.TR, self.color.to_curses())
        self.grid.addch(h, w, self.BR, self.color.to_curses())

        for module in self.get_modules():
            module.render()
            module.last_render = time.time()
            module.grid.noutrefresh()
        self.last_render = time.time()
        self.grid.noutrefresh()


class LightBox(Box):
    """A Box with light borders"""

    pass


class HeavyBox(Box):
    """A Box with heavy borders"""

    H, V, TL, TR, BL, BR = "━", "┃", "┏", "┓", "┗", "┛"


class DoubleBox(Box):
    """A Box with double borders"""

    H, V, TL, TR, BL, BR = "═", "║", "╔", "╗", "╚", "╝"


class Select(Box):
    """
    Build a select menu out of buttons.
    """

    UP, DOWN = "▲", "▼"
    on_change: Optional[Callable] = None
    on_select: Optional[Callable] = None
    button_cls: type[Button] = Button
    button_height: int = 3
    show_up: bool = False
    show_down: bool = False

    def __init__(
        self,
        coords: tuple[int, int],
        dims: tuple[int, int],
        options: list[str],
        color: Optional[Color] = None,
        highlight: Optional[Color] = None,
        on_change: Optional[Callable] = None,
        on_select: Optional[Callable] = None,
    ) -> None:
        super().__init__(coords, dims, [], color=color)
        self.highlight = highlight or Color(0, 100, 100)
        self.options = options
        self.on_change = on_change
        self.on_select = on_select

        for i, option in enumerate(self.options):
            self.append(self._get_button(i, option))
        self._mark_active(0)

    def _get_button(self, index: int, option: str) -> Button:
        """Helper to create a button for an option"""
        return self.button_cls(
            ((index * self.button_height) + 1, 1),
            (self.button_height, self.width - 2),
            value=option,
            color=self.color,
            highlight=self.highlight,
            on_activate=lambda _: self._button_on_activate(index, option),
        )

    def _button_on_activate(self, index: int, option: str):
        """Callback for when a button is activated."""
        if self.on_change:
            self.on_change(index, option)

    def _mark_active(self, index: int):
        """Mark a submodule as active."""
        for module in self.modules:
            assert hasattr(module, 'deactivate')
            module.deactivate()

        active = self.modules[index]
        assert hasattr(active, 'active')
        if not active.active:
            assert hasattr(active, 'activate')
            active.activate()

        if self.on_change:
            self.on_change(index, self.options[index])

    def _get_active_index(self):
        """Get the index of the active option."""
        for module in self.modules:
            if module.active:
                return self.modules.index(module)
        return None

    def get_modules(self):
        """Return a subset of modules to be rendered"""
        # since we can't always render all of the buttons, return a subset
        # that can be displayed in the available height.
        num_displayed = (self.height - 4) // self.button_height
        index = self._get_active_index() or 0
        count = len(self.modules)

        if count <= num_displayed:
            start = 0
            self.show_up = False
        else:
            ideal_start = index - (num_displayed // 2)
            start = min(ideal_start, count - num_displayed)
            start = max(0, start)
            self.show_up = bool(start > 0)

        end = min(start + num_displayed, count)
        self.show_down = bool(end < count)
        visible = self.modules[start:end]

        for i, module in enumerate(visible):
            pad = 2 if self.show_up else 1
            module.move((i * self.button_height) + pad, module.x)
        return visible

    def render(self):
        """Render all options and conditionally show up/down arrows."""
        for module in self.modules:
            if module.last_render:
                module.grid.erase()

        self.grid.erase()
        if self.show_up:
            self.grid.addstr(1, 1, self.UP.center(self.width - 2), self.color.to_curses())
        if self.show_down:
            self.grid.addstr(self.height - 2, 1, self.DOWN.center(self.width - 2), self.color.to_curses())

        super().render()

    def select(self, option: Button):
        """Select an option; ie. mark it as the value of this element."""
        index = self.modules.index(option)
        option.selected = not option.selected
        self.value = self.options[index]
        self._mark_active(index)
        if self.on_select:
            self.on_select(index, self.options[index])

    def input(self, key: Key):
        """Handle key input event."""
        index = self._get_active_index()

        if index is None:
            return  # can't select a non-active element

        if key.UP or key.DOWN:
            direction = -1 if key.UP else 1
            index = direction + index
            if index < 0 or index >= len(self.modules):
                return  # don't loop
            self._mark_active(index)
        elif key.SPACE or key.ENTER:
            self.select(self.modules[index])

        super().input(key)

    def click(self, y, x):
        # TODO there is a bug when you click on the last element in a scrollable list
        for module in self.modules:
            if not module in self.get_modules():
                continue  # module is not visible
            if not module.hit(y, x):
                continue
            self.select(module)


class RadioSelect(Select):
    """Allow one button to be `selected` at a time"""

    button_cls = RadioButton

    def __init__(
        self,
        coords: tuple[int, int],
        dims: tuple[int, int],
        options: list[str],
        color: Optional[Color] = None,
        highlight: Optional[Color] = None,
        on_change: Optional[Callable] = None,
        on_select: Optional[Callable] = None,
    ) -> None:
        super().__init__(
            coords, dims, options, color=color, highlight=highlight, on_change=on_change, on_select=on_select
        )
        self.select(self.modules[0])  # type: ignore[arg-type]

    def select(self, module: Button):
        """Radio buttons only allow a single selection."""
        for _module in self.modules:
            assert hasattr(_module, 'selected')
            _module.selected = False
        super().select(module)


class MultiSelect(Select):
    """Allow multiple buttons to be `selected` at a time"""

    button_cls = CheckButton


class ColorWheel(Element):
    """
    A module used for testing color display.
    """

    width: int = 80
    height: int = 24

    def __init__(self, coords: tuple[int, int], duration: float = 10.0):
        super().__init__(coords, (self.height, self.width))
        self.duration = duration
        self.start_time = time.time()

    def render(self) -> None:
        self.grid.erase()
        center_y, center_x = 12, 22
        radius = 10
        elapsed = time.time() - self.start_time
        hue_offset = (elapsed / self.duration) * 360  # animate

        for y in range(center_y - radius, center_y + radius + 1):
            for x in range(center_x - radius * 2, center_x + radius * 2 + 1):
                # Convert position to polar coordinates
                dx = (x - center_x) / 2  # Compensate for terminal character aspect ratio
                dy = y - center_y
                distance = math.sqrt(dx * dx + dy * dy)

                if distance <= radius:
                    # Convert to HSV
                    angle = math.degrees(math.atan2(dy, dx))
                    # h = (angle + 360) % 360
                    h = (angle + hue_offset) % 360
                    s = (distance / radius) * 100
                    v = 100  # (distance / radius) * 100

                    color = Color(h, s, v)
                    self.grid.addstr(y, x, "█", color.to_curses())

        x = 50
        y = 4
        for i in range(0, curses.COLORS):
            self.grid.addstr(y, x, f"███", curses.color_pair(i + 1))
            y += 1
            if y >= self.height - 4:
                y = 4
                x += 3
            if x >= self.width - 3:
                break

        self.grid.refresh()


class DebugElement(Element):
    """Show fps and color usage."""

    def __init__(self, coords: tuple[int, int]):
        super().__init__(coords, (1, 24))

    def render(self) -> None:
        self.grid.addstr(0, 1, f"FPS: {1 / (time.time() - self.last_render):.0f}")
        self.grid.addstr(0, 10, f"Colors: {len(Color._color_map)}/{curses.COLORS}")


class View(Contains):
    app: 'App'
    positioning: str = POS_ABSOLUTE
    padding: tuple[int, int] = (0, 0)
    y: int = 0
    x: int = 0

    def __init__(self, app: 'App'):
        self.app = app
        self.modules = []

    def init(self, dims: tuple[int, int]) -> None:
        self.height, self.width = dims
        self.modules = self.layout()

        if conf.DEBUG:
            self.append(DebugElement((1, 1)))

    @property
    def grid(self):
        if not self._grid:
            self._grid = curses.newwin(self.height, self.width, self.y, self.x)
            self._grid.bkgd(' ', curses.color_pair(1))
        return self._grid

    def layout(self) -> list[Renderable]:
        """Override this in subclasses to define the layout of the view."""
        log.warning(f"`layout` not implemented in View: {self.__class__}.")
        return []


class App:
    stdscr: curses.window
    height: int
    width: int
    min_height: int = 30
    min_width: int = 80
    frame_time: float = 1.0 / 60  # 30 FPS
    editing = False
    view: Optional[View] = None  # the active view
    views: dict[str, type[View]] = {}
    shortcuts: dict[str, str] = {}

    def __init__(self, stdscr: curses.window) -> None:
        self.stdscr = stdscr
        self.height, self.width = self.stdscr.getmaxyx()  # TODO dynamic resizing

        if not self.width >= self.min_width or not self.height >= self.min_height:
            raise RenderException(
                f"Terminal window is too small. Resize to at least {self.min_width}x{self.min_height}."
            )

        curses.curs_set(0)
        stdscr.nodelay(True)
        stdscr.timeout(10)  # balance framerate with cpu usage
        curses.mousemask(curses.BUTTON1_CLICKED | curses.REPORT_MOUSE_POSITION)

        Color.initialize()
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)

    def add_view(self, name: str, view_cls: type[View], shortcut: Optional[str] = None) -> None:
        self.views[name] = view_cls
        if shortcut:
            self.shortcuts[shortcut] = name

    def load(self, view_name: str):
        if self.view:
            self.view.destroy()
            self.view = None

        view_cls = self.views[view_name]
        self.view = view_cls(self)
        self.view.init((self.height, self.width))

    def run(self):
        frame_time = 1.0 / 60  # 30 FPS
        last_frame = time.time()
        self._running = True
        while self._running:
            self.height, self.width = self.stdscr.getmaxyx()

            current_time = time.time()
            delta = current_time - last_frame
            ch = self.stdscr.getch()

            if ch == curses.KEY_MOUSE:
                try:
                    _, x, y, _, bstate = curses.getmouse()
                    if not bstate & curses.BUTTON1_CLICKED:
                        continue  # only allow left click
                    self.click(y, x)
                except curses.error:
                    pass
            elif ch != -1:
                self.input(ch)

            if not App.editing:
                if ch == ord('q'):
                    break
                elif ch in [ord(x) for x in self.shortcuts.keys()]:
                    self.load(self.shortcuts[chr(ch)])

            if delta >= self.frame_time or ch != -1:
                self.render()
                delta = 0
            if delta < self.frame_time:
                time.sleep(frame_time - delta)

    def stop(self):
        if self.view:
            self.view.destroy()
        self._running = False
        curses.endwin()

    def render(self):
        if not self.view:
            return

        try:
            self.view.render()
            self.view.last_render = time.time()
            self.view.grid.noutrefresh()
            curses.doupdate()
        except curses.error as e:
            log.debug(f"Error rendering view: {e}")
            if "add_wch() returned ERR" in str(e):
                raise RenderException("Grid not large enough to render all modules.")
            if "curses function returned NULL" in str(e):
                raise RenderException("Window not large enough to render.")
            raise e

    def click(self, y, x):
        """Handle mouse click event."""
        if self.view:
            self.view.click(y, x)

    def input(self, ch: int):
        """Handle key input event."""
        key = Key(ch)

        if key.TAB:
            self._select_next_tabbable()

        if self.view:
            self.view.input(key)

    def _get_tabbable_modules(self):
        """
        Search through the tree of modules to find selectable elements.
        """

        def _get_activateable(module: Element):
            """Find modules with an `activate` method"""
            if hasattr(module, 'activate'):
                yield module
            for submodule in getattr(module, 'modules', []):
                yield from _get_activateable(submodule)

        return list(_get_activateable(self.view))

    def _select_next_tabbable(self):
        """
        Activate the next tabbable module in the list.
        """

        def _get_active_module(module: Element):
            if hasattr(module, 'active') and module.active:
                return module
            for submodule in getattr(module, 'modules', []):
                active = _get_active_module(submodule)
                if active:
                    return active
            return None

        modules = self._get_tabbable_modules()
        active_module = _get_active_module(self.view)
        if active_module:
            for module in modules:
                module.deactivate()
            next_index = modules.index(active_module) + 1
            if next_index >= len(modules):
                next_index = 0
            modules[next_index].activate()  # TODO this isn't working
        elif modules:
            modules[0].activate()
