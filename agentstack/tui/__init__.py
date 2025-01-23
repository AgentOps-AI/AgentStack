import curses
import signal
import time
import math
from random import randint
from dataclasses import dataclass
from typing import Optional, Any, List, Tuple, Union
from enum import Enum

from agentstack import conf, log
from agentstack.cli import LOGO
from agentstack.tui.module import *
from agentstack.tui.color import Color, AnimatedColor, ColorWheel


LOGO_ANTHROPIC = """  _                   
 /_/_ _/_/_ __  _  ._ 
/ // // / ///_//_///_ 
              /       """

LOGO_OPENAI = """  _           _       
 / /_  _  _  /_//     
/_//_//_'/ // //      
  /                  """


class LogoModule(Text):
    #h_align = ALIGN_CENTER  # TODO center stars
    
    def __init__(self, coords: tuple[int, int], dims: tuple[int, int]):
        super().__init__(coords, dims)
        self.color = Color(220, 100, 100)
        self.value = LOGO
        self.stars = [(3, 1), (25, 5), (34, 1), (52, 2), (79, 3), (97, 1)]
        self._star_colors = {}
    
    def _get_star_color(self, index: int) -> Color:
        if index not in self._star_colors:
            self._star_colors[index] = AnimatedColor(
                Color(randint(0, 150), 100, 100), 
                Color(randint(200, 360), 100, 100), 
                duration=2.0, 
                loop=True, 
            )
        return self._star_colors[index]
    
    def render(self) -> None:
        super().render()
        for i, (x, y) in enumerate(self.stars):
            if x >= self.width or y >= self.height:
                continue
            self.grid.addch(y, x, '*', self._get_star_color(i).to_curses())


class HelpText(Text):
    def __init__(self, coords: tuple[int, int], dims: tuple[int, int]) -> None:
        super().__init__(coords, dims)
        self.color = Color(0, 0, 50)
        self.value = " | ".join([
            "[tab] to select", 
            "[up / down] to navigate",
            "[space / enter] to confirm",
            "[q] to quit", 
        ])


AGENT_NAME = Node()
AGENT_ROLE = Node()
AGENT_GOAL = Node()
AGENT_BACKSTORY = Node()

class AgentView(View):
    name = "agent"
    def layout(self) -> list[Module]:
        return [
            Box((0, 0), (self.height, self.width), color=Color(90, 100, 100), modules=[
                LogoModule((1, 1), (7, self.width-2)),
                Title((9, 1), (3, self.width-3), color=Color(220, 100, 40, reversed=True), value="Define An Agent"),
                
                # Text((12, 2), (1, 11), color=Color(0, 100, 100), value="Name"),
                # TextInput((12, 13), (2, self.width - 16), AGENT_NAME, color=Color(240, 20, 100, reversed=True)), 
                
                # Text((15, 2), (1, 11), color=Color(0, 100, 100), value="Role"),
                # TextInput((15, 13), (6, self.width - 16), AGENT_ROLE, color=Color(240, 20, 100, reversed=True)),
                
                # Text((22, 2), (1, 11), color=Color(0, 100, 100), value="Goal"),
                # TextInput((22, 13), (6, self.width - 16), AGENT_GOAL, color=Color(240, 20, 100, reversed=True)),
                
                # Text((29, 2), (1, 11), color=Color(0, 100, 100), value="Backstory"),
                # TextInput((29, 13), (6, self.width - 16), AGENT_BACKSTORY, color=Color(240, 20, 100, reversed=True)),
                
                #Button((35, self.width-14), (3, 10), "Next", color=Color(0, 100, 100, reversed=True)),
                
            ]),
        ]


class ModelView(View):
    name = "model"
    
    MODEL_OPTIONS = [
        {'value': "gpt-3.5-turbo", 'name': "GPT-3.5 Turbo", 'description': "A fast and cost-effective model.", 'logo': LOGO_ANTHROPIC}, 
        {'value': "gpt-4", 'name': "GPT-4", 'description': "A more advanced model with better understanding.", 'logo': LOGO_OPENAI},
        {'value': "gpt-4o", 'name': "GPT-4o", 'description': "The latest and most powerful model.", 'logo': LOGO_OPENAI},
        {'value': "gpt-4o-mini", 'name': "GPT-4o Mini", 'description': "A smaller, faster version of GPT-4o.", 'logo': LOGO_ANTHROPIC},
    ]
    
    model_choice = Node()
    model_logo = Node()
    model_name = Node()
    model_description = Node()
    
    def set_model_choice(self, index: int, value: str):
        model = self.MODEL_OPTIONS[index]
        self.model_choice.value = model['value']
        self.model_logo.value = model['logo']
        self.model_name.value = model['name']
        self.model_description.value = model['description']
    
    def get_model_options(self):
        return [model['value'] for model in self.MODEL_OPTIONS]
    
    def layout(self) -> list[Module]:
        return [
            Box((0, 0), (self.height-1, self.width), color=Color(90), modules=[
                LogoModule((1, 1), (7, self.width-2)),
                Title((9, 1), (3, self.width-3), color=Color(220, 100, 40, reversed=True), value="Select A Default Model"),
                
                RadioSelect((13, 1), (self.height-20, round(self.width/2)-3), options=self.get_model_options(), color=Color(300, 50), highlight=AnimatedColor(
                    Color(300, 0, 100, reversed=True), Color(300, 70, 50, reversed=True), duration=0.2
                ), on_change=self.set_model_choice),
                Box((13, round(self.width/2)), (self.height-20, round(self.width/2)-3), color=Color(300, 50), modules=[
                    Text((1, 3), (4, round(self.width/2)-10), color=Color(300, 40), value=self.model_logo),
                    BoldText((6, 3), (1, round(self.width/2)-10), color=Color(300), value=self.model_name), 
                    WrappedText((8, 3), (5, round(self.width/2)-10), color=Color(300, 50), value=self.model_description),
                ]),
                
                Button((self.height-6, self.width-17), (3, 15), "Next", color=Color(300, 100, 100, reversed=True)),
            ]),
            HelpText((self.height-1, 0), (1, self.width)),
        ]


class ColorView(View):
    name = "color"
    def layout(self) -> list[Module]:
        return [
            Box((0, 0), (self.height, self.width), color=Color(90, 100, 100), modules=[
                LogoModule((1, 1), (7, self.width-2)),
                ColorWheel((6, 1)),
            ]),
        ]


def run(stdscr):
    import io
    log.set_stdout(io.StringIO())  # disable on-screen logging for now. 
    
    CMD_STR = f" [q]uit [m]odel"
    frame_time = 1.0 / 60  # 30 FPS
    app = App(stdscr)
    view = None
    
    def load_view(view_cls):
        nonlocal view
        if view:
            app.destroy(view)
            view = None
        
        view = view_cls()
        view.init(app.dims)
        app.append(view)
        # underline rendered CMD_STR for the active command
        # view_name = view.__class__.__name__
        # cmd_i = CMD_STR.find(f"[{view_name[0]}]{view_name[1:]}")
        # cmd_len = len(view_name)
        # grid.append(ui.string((29, 0), (1, 80), " " * 80))
        # grid.append(ui.string((29, cmd_i), (1, 80), "*" * (cmd_len + 2)))
    
    load_view(ModelView)
    
    last_frame = time.time()
    while True:
        current_time = time.time()
        delta = current_time - last_frame
        ch = stdscr.getch()
        
        if ch == curses.KEY_MOUSE:
            _, x, y, _, _ = curses.getmouse()
            app.click(y, x)
        elif ch != -1:
            app.input(ch)
        
        if not App.editing:
            if ch == ord('q'):
                break
            elif ch == ord('a'):
                load_view(AgentView)
            elif ch == ord('c'):
                load_view(ColorView)
            elif ch == ord('m'):
                load_view(ModelView)
        
        if delta >= frame_time or ch != -1:
            app.render()
            delta = 0
        if delta < frame_time:
            time.sleep(frame_time - delta)

def main():
    curses.wrapper(run)