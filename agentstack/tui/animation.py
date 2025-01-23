

"""
Animations are classes that interact with elements inside of a tui.Module to 
create visual effects over time. tui.Module keeps track of the current frame and
handles render, but we prepare the elements that need to be rendered beforehand. 

We want to accomplish a few things with animation:

- Fading an element in or out. Module.color -> black and back. 
- A color sweep that passes from left to right across an element. The animation
  can either play on repeat with a delay, or just once (perhaps by setting a delay of -1)




# space_colors = [
#     (75, 0, 130),    # Indigo
#     (138, 43, 226),  # Purple
#     (0, 0, 255),     # Blue
#     (138, 43, 226),  # Purple
# ]
# main_box.set_color_animation(ColorAnimation(space_colors, speed=0.2))


class ColorAnimation:
    def __init__(self, colors: List[Tuple[int, int, int]], speed: float = 1.0):
        self.colors = colors
        self.speed = speed
        self.start_time = time.time()

    def _interpolate_color(self, color1: Tuple[int, int, int], color2: Tuple[int, int, int], factor: float) -> Tuple[int, int, int]:
        return tuple(int(c1 + (c2 - c1) * factor) for c1, c2 in zip(color1, color2))

    def _rgb_to_curses_color(self, r: int, g: int, b: int) -> int:
        colors = [
            (0, 0, 0, curses.COLOR_BLACK),
            (1000, 0, 0, curses.COLOR_RED),
            (0, 1000, 0, curses.COLOR_GREEN),
            (1000, 1000, 0, curses.COLOR_YELLOW),
            (0, 0, 1000, curses.COLOR_BLUE),
            (1000, 0, 1000, curses.COLOR_MAGENTA),
            (0, 1000, 1000, curses.COLOR_CYAN),
            (1000, 1000, 1000, curses.COLOR_WHITE),
        ]
        
        r = r * 1000 // 255
        g = g * 1000 // 255
        b = b * 1000 // 255
        
        min_dist = float('inf')
        best_color = curses.COLOR_WHITE
        for cr, cg, cb, color in colors:
            dist = (cr - r) ** 2 + (cg - g) ** 2 + (cb - b) ** 2
            if dist < min_dist:
                min_dist = dist
                best_color = color
        return best_color

    def get_color_for_line(self, line: int, total_lines: int, current_time: Optional[float] = None) -> int:
        if current_time is None:
            current_time = time.time()
        
        wave_pos = (current_time - self.start_time) * self.speed
        line_pos = (line / total_lines + wave_pos) % 1.0
        
        color_pos = line_pos * len(self.colors)
        color_index = int(color_pos)
        color_factor = color_pos - color_index
        
        color1 = self.colors[color_index % len(self.colors)]
        color2 = self.colors[(color_index + 1) % len(self.colors)]
        
        blended = self._interpolate_color(color1, color2, color_factor)
        return self._rgb_to_curses_color(*blended)