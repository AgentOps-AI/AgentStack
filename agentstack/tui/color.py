import curses
from typing import Optional
import time
import math
from agentstack import log
from agentstack.tui.module import Module


# TODO: fallback for 16 color mode
# TODO: fallback for no color mode

class Color:
    """
    Color class based on HSV color space, mapping directly to terminal color capabilities.
    
    Hue: 0-360 degrees, mapped to 6 primary directions (0, 60, 120, 180, 240, 300)
    Saturation: 0-100%, mapped to 6 levels (0, 20, 40, 60, 80, 100)
    Value: 0-100%, mapped to 6 levels for colors, 24 levels for grayscale
    """
    SATURATION_LEVELS = 12
    HUE_SEGMENTS = 6
    VALUE_LEVELS = 6
    GRAYSCALE_LEVELS = 24
    COLOR_CUBE_SIZE = 6  # 6x6x6 color cube

    reversed: bool = False
    bold: bool = False

    _color_map = {}      # Cache for color mappings
    
    def __init__(self, h: float, s: float = 100, v: float = 100, reversed: bool = False, bold: bool = False) -> None:
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
        if h_segment == 0:    # Red to Yellow
            r, g, b = max_level, int(max_level * h_remainder), 0
        elif h_segment == 1:  # Yellow to Green
            r, g, b = int(max_level * (1 - h_remainder)), max_level, 0
        elif h_segment == 2:  # Green to Cyan
            r, g, b = 0, max_level, int(max_level * h_remainder)
        elif h_segment == 3:  # Cyan to Blue
            r, g, b = 0, int(max_level * (1 - h_remainder)), max_level
        elif h_segment == 4:  # Blue to Magenta
            r, g, b = int(max_level * h_remainder), 0, max_level
        else:                 # Magenta to Red
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
            #try:
            # TODO make sure we don't overflow the available color pairs
            curses.init_pair(pair_number, color_number, -1)
            self._color_map[color_number] = pair_number
            #except:
            #    return curses.color_pair(0)
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
        
        return Color(h, s, v, reversed=self.start.reversed).to_curses()


class ColorWheel(Module):
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
        center_y, center_x  = 12, 22
        radius = 10
        elapsed = time.time() - self.start_time
        hue_offset = (elapsed / self.duration) * 360  # animate
        
        for y in range(center_y - radius, center_y + radius + 1):
            for x in range(center_x - radius * 2, center_x + radius * 2 + 1):
                # Convert position to polar coordinates
                dx = (x - center_x) / 2  # Compensate for terminal character aspect ratio
                dy = y - center_y
                distance = math.sqrt(dx*dx + dy*dy)
                
                if distance <= radius:
                    # Convert to HSV
                    angle = math.degrees(math.atan2(dy, dx))
                    #h = (angle + 360) % 360
                    h = (angle + hue_offset) % 360
                    s = (distance / radius) * 100
                    v = 100 # (distance / radius) * 100
                    
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
        #super().render()