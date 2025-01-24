import curses
import signal
import time
import math
from random import randint
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, Any, List, Tuple, Union
from enum import Enum

from agentstack import conf, log
if TYPE_CHECKING:
    from agentstack.tui.color import Color, AnimatedColor


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
    callbacks: list[callable]
    
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
        log.debug(f"Key: {ch}")
    
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
        return (self.ch >= 65 and self.ch <= 90) or (self.ch >= 97 and self.ch <= 122)


class Renderable:
    _grid: Optional[curses.window] = None
    y: int
    x: int
    height: int
    width: int
    parent: Optional['Contains'] = None
    h_align: str = ALIGN_LEFT
    v_align: str = ALIGN_TOP
    color: 'Color'
    last_render: float = 0
    padding: tuple[int, int] = (1, 1)
    positioning: str = POS_ABSOLUTE
    
    def __init__(self, coords: tuple[int, int], dims: tuple[int, int], color: Optional['Color'] = None):
        self.y, self.x = coords
        self.height, self.width = dims
        from agentstack.tui.color import Color
        self.color = color or Color(0, 100, 0)
    
    def __repr__( self ):
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
                self.height + self.padding[0], 
                self.width + self.padding[1], 
                self.y, 
                self.x) # TODO this cant be bigger than the window
        return self._grid

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
        return y >= self.abs_y and y < self.abs_y + self.height and x >= self.abs_x and x < self.abs_x + self.width

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


class Module(Renderable):
    positioning: str = POS_RELATIVE
    word_wrap: bool = False
    
    def __init__(self, coords: tuple[int, int], dims: tuple[int, int], value: Optional[Any] = "", color: Optional['Color'] = None):
        super().__init__(coords, dims, color=color)
        self.value = value
    
    def __repr__( self ):
        return f"{type(self)} at ({self.y}, {self.x}) with value '{self.value[:20]}'"

    def _get_lines(self, value: str) -> List[str]:
        if self.word_wrap:
            splits = [''] * self.height
            words = value.split()
            for i in range(self.height):
                while words and (len(splits[i]) + len(words[0]) + 1) <= self.width:
                    splits[i] += f"{words.pop(0)} " if words else ''
        elif '\n' in value:
            splits = value.split('\n')
        else:
            splits = [value, ]
        
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
            
            lines.append(line[:self.width])
        return lines
    
    def render(self):
        for i, line in enumerate(self._get_lines(str(self.value))):
            self.grid.addstr(i, 0, line, self.color.to_curses())


class NodeModule(Module):
    format: Optional[callable] = None
    
    def __init__(self, coords: tuple[int, int], dims: tuple[int, int], node: Node, color: Optional['Color'] = None, format: callable=None):
        super().__init__(coords, dims, color=color)
        self.node = node # TODO can also be str?
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


class Editable(NodeModule):
    filter: Optional[callable] = None
    active: bool
    _original_value: Any
    
    def __init__(self, coords, dims, node, color=None, format: callable=None, filter: callable=None):
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
    
    def deactivate(self):
        """Deactivate this module, making it no longer active."""
        App.editing = False
        self.active = False
    
    def save(self):
        if self.filter:
            self.value = self.filter(self.value)
        super().save()
    
    def input(self, key: Key):
        if not self.active:
            return

        # TODO word wrap
        # TODO we probably don't need to filter as prohibitively
        if key.is_alpha or key.is_numeric or key.PERIOD or key.MINUS or key.SPACE:
            self.value = str(self.value) + key.chr
        elif key.BACKSPACE:
            self.value = str(self.value)[:-1]
        elif key.ESC:
            self.deactivate()
            self.value = self._original_value  # revert changes
        elif key.ENTER:
            self.deactivate()
            self.save()
    
    def destroy(self):
        self.deactivate()
        super().destroy()


class Text(Module):
    pass


class WrappedText(Text):
    word_wrap: bool = True


class BoldText(Text):
    def __init__(self, coords: tuple[int, int], dims: tuple[int, int], value: Optional[Any] = "", color: Optional['Color'] = None):
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
    border_color: 'Color'
    active_color: 'Color'
    word_wrap: bool = True
    
    def __init__(self, coords: tuple[int, int], dims: tuple[int, int], node: Node, color: Optional['Color'] = None, border: Optional['Color'] = None, active: Optional['Color'] = None, format: callable=None):
        super().__init__(coords, dims, node=node, color=color, format=format)
        self.width, self.height = (dims[1]-1, dims[0]-1)
        self.border_color = border or self.color
        self.active_color = active or self.color
    
    def activate(self):
        # change the border color to a highlight
        self._original_border_color = self.border_color
        self.border_color = self.active_color
        super().activate()
    
    def deactivate(self):
        if self.active and hasattr(self, '_original_border_color'):
            self.border_color = self._original_border_color
        super().deactivate()
    
    def render(self) -> None:
        for i, line in enumerate(self._get_lines(str(self.value))):
            self.grid.addstr(i, 0, line, self.color.to_curses())
        
        # # add border to bottom right like a drop shadow
        for x in range(self.width):
            self.grid.addch(self.height, x, self.H, self.border_color.to_curses())
        for y in range(self.height):
            self.grid.addch(y, self.width, self.V, self.border_color.to_curses())
        self.grid.addch(self.height, self.width, self.BR, self.border_color.to_curses())


class Button(Module):
    h_align: str = ALIGN_CENTER
    v_align: str = ALIGN_MIDDLE
    active: bool = False
    selected: bool = False
    highlight: Optional['Color'] = None
    on_confirm: Optional[callable] = None
    
    def __init__( self, coords: tuple[int, int], dims: tuple[int, int], value: Optional[Any] = "", color: Optional['Color'] = None, highlight: Optional['Color'] = None, on_confirm: Optional[callable] = None):
        super().__init__(coords, dims, value=value, color=color)
        self.highlight = highlight or self.color.sat(80)
        self.on_confirm = on_confirm
    
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

    def deactivate(self):
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
    color: 'Color'
    last_render: float = 0
    parent: Optional['Contains'] = None
    modules: List[Module]
    
    def __init__(self, coords: tuple[int, int], dims: tuple[int, int], modules: list[Module], color: Optional['Color'] = None):
        super().__init__(coords, dims, color=color)
        self.modules = []
        for module in modules:
            self.append(module)
    
    def append(self, module: Union['Contains', Module]):
        module.parent = self
        self.modules.append(module)

    def render(self):
        for module in self.modules:
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
    H, V, TL, TR, BL, BR =  "─", "│", "┌", "┐", "└", "┘"

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
        
        for module in self.modules:
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
    H, V, TL, TR, BL, BR =  "━", "┃", "┏", "┓", "┗", "┛"


class DoubleBox(Box):
    """A Box with double borders"""
    H, V, TL, TR, BL, BR =  "═", "║", "╔", "╗", "╚", "╝"


class Select(Box):
    """
    Build a select menu out of buttons.
    """
    on_change: Optional[callable] = None
    button_cls: type[Button] = Button
    
    def __init__(self, coords: Tuple[int, int], dims: Tuple[int, int], options: List[str], color: Optional['Color'] = None, highlight: Optional['Color'] = None, on_change: Optional[callable] = None) -> None:
        super().__init__(coords, dims, [], color=color)
        from agentstack.tui.color import Color
        self.highlight = highlight or Color(0, 100, 100)
        self.options = options
        self.on_change = on_change
        for i, option in enumerate(self.options):
            self.append(self.button_cls(((i*3)+1, 1), (3, self.width-2), value=option, color=color, highlight=self.highlight))
        self._mark_active(0)

    def _mark_active(self, index: int):
        for module in self.modules:
            module.deactivate()
        self.modules[index].activate()
        # TODO other modules in the app will not get marked. 
        
        if self.on_change:
            self.on_change(index, self.options[index])

    def select(self, module: Module):
        module.selected = not module.selected
        self._mark_active(self.modules.index(module))
    
    def input(self, key: Key):
        index = None
        for module in self.modules:
            if module.active:
                index = self.modules.index(module)
        
        if index is None:
            return
        
        if key.UP or key.DOWN:
            direction = -1 if key.UP else 1
            index = (direction + index) % len(self.modules)
            self._mark_active(index)
        elif key.SPACE or key.ENTER:
            self.select(self.modules[index])
        
        super().input(key)
    
    def click(self, y, x):
        for module in self.modules:
            if not module.hit(y, x):
                continue
            self._mark_active(self.modules.index(module))
            self.select(module)


class RadioSelect(Select):
    """Allow one button to be `selected` at a time"""
    button_cls = RadioButton

    def __init__(self, coords: Tuple[int, int], dims: Tuple[int, int], options: List[str], color: Optional['Color'] = None, highlight: Optional['Color'] = None, on_change: Optional[callable] = None) -> None:
        super().__init__(coords, dims, options, color=color, highlight=highlight, on_change=on_change)
        self.select(self.modules[0])

    def select(self, module: Module):
        for _module in self.modules:
            _module.selected = False
        super().select(module)


class MultiSelect(Select):
    """Allow multiple buttons to be `selected` at a time"""
    button_cls = CheckButton


class DebugModule(Module):
    """Show fps and color usage."""
    def __init__(self, coords: Tuple[int, int]):
        super().__init__(coords, (1, 24))
    
    def render(self) -> None:
        from agentstack.tui.color import Color
        self.grid.addstr(0, 1, f"FPS: {1 / (time.time() - self.last_render):.0f}")
        self.grid.addstr(0, 10, f"Colors: {len(Color._color_map)}/{curses.COLORS}")


class View(Contains):
    positioning: str = POS_ABSOLUTE
    padding: tuple[int, int] = (0, 0)
    y: int = 0
    x: int = 0

    def __init__(self):
        self.modules = []

    def init(self, dims: Tuple[int, int]) -> None:
        self.height, self.width = dims
        self.modules = self.layout()
        
        if conf.DEBUG:
            self.append(DebugModule((1, 1)))

    @property
    def grid(self):
        if not self._grid:
            self._grid = curses.newwin(self.height, self.width, self.y, self.x)
        return self._grid

    def layout(self) -> list[Module]:
        log.warn(f"`layout` not implemented in View: {self.__class__}.")
        return []


class App:
    stdscr: curses.window
    frame_time: float = 1.0 / 60  # 30 FPS
    editing = False
    dims = property(lambda self: self.stdscr.getmaxyx())  # TODO remove this
    view: Optional[View] = None  # the active view
    views: dict[str, type[View]] = {}
    shortcuts: dict[str, str] = {}
    
    def __init__(self, stdscr: curses.window) -> None:
        self.stdscr = stdscr
        self.height, self.width = self.stdscr.getmaxyx()  # TODO dynamic resizing
        
        curses.curs_set(0)
        stdscr.nodelay(True)
        stdscr.timeout(10)  # balance framerate with cpu usage
        curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)
        
        from agentstack.tui.color import Color
        Color.initialize()

    def add_view(self, name: str, view_cls: type[View], shortcut: Optional[str] = None) -> None:
        self.views[name] = view_cls
        if shortcut:
            self.shortcuts[shortcut] = name

    def load(self, name: str):
        if self.view:
            self.view.destroy()
            self.view = None
        
        view_cls = self.views[name]
        self.view = view_cls()
        self.view.init(self.dims)

    def run(self):
        frame_time = 1.0 / 60  # 30 FPS
        last_frame = time.time()
        while True:
            current_time = time.time()
            delta = current_time - last_frame
            ch = self.stdscr.getch()
            
            if ch == curses.KEY_MOUSE:
                _, x, y, _, _ = curses.getmouse()
                self.click(y, x)
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

    def render(self):
        if self.view:
            self.view.render()
            self.view.last_render = time.time()
            self.view.grid.noutrefresh()
        
        curses.doupdate()
    
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
        def _get_activateable(module: Module):
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
        def _get_active_module(module: Module):
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
            log.debug(f"Active index: {modules.index(active_module)}")
            log.debug(f"Next index: {next_index}")
            modules[next_index].activate()  # TODO this isn't working
        elif modules:
            modules[0].activate()

