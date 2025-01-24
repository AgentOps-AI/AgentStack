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
from agentstack.tui.color import Color, ColorAnimation, ColorWheel


# TODO this could be a dynamic module type
LOGO_ANTHROPIC = """\
  _                   
 /_/_ _/_/_ __  _  ._ 
/ // // / ///_//_///_ 
              /       """

LOGO_OPENAI = """\
  _           _       
 / /_  _  _  /_//     
/_//_//_'/ // //      
  /                  """

COLOR_BORDER = Color(90)
COLOR_MAIN = Color(220)
COLOR_TITLE = Color(220, 100, 40, reversed=True)
COLOR_FORM = Color(300)
COLOR_BUTTON = Color(300, reversed=True)
COLOR_FIELD_BG = Color(240, 20, 100, reversed=True)
COLOR_FIELD_BORDER = Color(300, 100, 50)
COLOR_FIELD_ACTIVE = Color(300, 80)
FIELD_COLORS = {
    'color': COLOR_FIELD_BG, 
    'border': COLOR_FIELD_BORDER, 
    'active': COLOR_FIELD_ACTIVE, 
}

class LogoModule(Text):
    #h_align = ALIGN_CENTER  # TODO center stars
    
    def __init__(self, coords: tuple[int, int], dims: tuple[int, int]):
        super().__init__(coords, dims)
        self.color = COLOR_MAIN
        self.value = LOGO
        self.stars = [(3, 1), (25, 5), (34, 1), (52, 2), (79, 3), (97, 1)]
        self._star_colors = {}
    
    def _get_star_color(self, index: int) -> Color:
        if index not in self._star_colors:
            self._star_colors[index] = ColorAnimation(
                Color(randint(0, 150)), 
                Color(randint(200, 360)), 
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
        if conf.DEBUG:
            self.value += " | [d]ebug"


class BannerView(View):
    name = "banner"
    title = "Welcome to AgentStack"
    sparkle = "The fastest way to build AI agents."
    subtitle = "Let's get started!"
    color = ColorAnimation(
        start=Color(90, 0, 0),  # TODO make this darker
        end=Color(90),
        duration=0.5
    )
    
    def layout(self) -> list[Module]:
        return [
            Box((0, 0), (self.height, self.width), color=COLOR_BORDER, modules=[
                Title((round(self.height / 2)-4, 1), (1, self.width-3), color=self.color, value=self.title),
                Title((round(self.height / 2)-2, 1), (1, self.width-3), color=self.color, value=self.sparkle),
                Title((round(self.height / 2), 1), (1, self.width-3), color=self.color, value=self.subtitle),
            ]),
        ]


class AfterTaskView(BannerView):
    title = "Let there be tasks!"
    sparkle = "(ノ ˘_˘)ノ　ζ|||ζ　ζ|||ζ　ζ|||ζ"
    subtitle = "Tasks are the heart of your agent's work. "


class AgentView(View):
    name = "agent"
    
    agent_name = Node()
    agent_role = Node()
    agent_goal = Node()
    agent_backstory = Node()
    
    def submit(self):
        log.info("Agent defined: %s", self.agent_name.value)
    
    def layout(self) -> list[Module]:
        return [
            Box((0, 0), (self.height-1, self.width), color=COLOR_BORDER, modules=[
                LogoModule((1, 1), (7, self.width-2)),
                Title((9, 1), (1, self.width-3), color=COLOR_TITLE, value="Define An Agent"),
                
                Text((11, 2), (1, 11), color=COLOR_FORM, value="Name"),
                TextInput((11, 13), (2, self.width - 15), self.agent_name, **FIELD_COLORS), 
                
                Text((13, 2), (1, 11), color=COLOR_FORM, value="Role"),
                TextInput((13, 13), (5, self.width - 15), self.agent_role, **FIELD_COLORS),
                
                Text((18, 2), (1, 11), color=COLOR_FORM, value="Goal"),
                TextInput((18, 13), (5, self.width - 15), self.agent_goal, **FIELD_COLORS),
                
                Text((23, 2), (1, 11), color=COLOR_FORM, value="Backstory"),
                TextInput((23, 13), (5, self.width - 15), self.agent_backstory, **FIELD_COLORS),
                
                Button((self.height-6, self.width-17), (3, 15), "Next", color=COLOR_BUTTON, on_confirm=self.submit),
            ]),
            HelpText((self.height-1, 0), (1, self.width)),
        ]


class AfterAgentView(BannerView):
    title = "Boom! We made some agents."
    sparkle = "(ﾉ>ω<)ﾉ :｡･:*:･ﾟ’★,｡･:*:･ﾟ’☆"
    subtitle = "Now lets make some tasks for the agents to accomplish!"


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
    
    def submit(self):
        log.info("Model selected: %s", self.model_choice.value)
    
    def layout(self) -> list[Module]:
        return [
            Box((0, 0), (self.height-1, self.width), color=COLOR_BORDER, modules=[
                LogoModule((1, 1), (7, self.width-2)),
                Title((9, 1), (3, self.width-3), color=Color(220, 100, 40, reversed=True), value="Select A Default Model"),
                
                RadioSelect((13, 1), (self.height-20, round(self.width/2)-3), options=self.get_model_options(), color=Color(300, 50), highlight=ColorAnimation(
                    Color(300, 0, 100, reversed=True), Color(300, 70, 50, reversed=True), duration=0.2
                ), on_change=self.set_model_choice),
                Box((13, round(self.width/2)), (self.height-20, round(self.width/2)-3), color=Color(300, 50), modules=[
                    Text((1, 3), (4, round(self.width/2)-10), color=Color(300, 40), value=self.model_logo),
                    BoldText((6, 3), (1, round(self.width/2)-10), color=Color(300), value=self.model_name), 
                    WrappedText((8, 3), (5, round(self.width/2)-10), color=Color(300, 50), value=self.model_description),
                ]),
                
                Button((self.height-6, self.width-17), (3, 15), "Next", color=COLOR_BUTTON, on_confirm=self.submit),
            ]),
            HelpText((self.height-1, 0), (1, self.width)),
        ]


class DebugView(View):
    name = "debug"
    def layout(self) -> list[Module]:
        from agentstack.utils import get_version
        
        return [
            Box((0, 0), (self.height-1, self.width), color=COLOR_BORDER, modules=[
                ColorWheel((1, 1)),
                Title((self.height-6, 3), (1, self.width-5), color=COLOR_MAIN, 
                     value=f"AgentStack version {get_version()}"),
            ]),
            HelpText((self.height-1, 0), (1, self.width)),
        ]


class WizardApp(App):
    views = {
        'welcome': BannerView,
        'agent': AgentView,
        'model_selection': ModelView,
        'debug': DebugView,
    }
    shortcuts = {
        'q': 'quit',
        'd': 'debug',
        
        # testing shortcuts
        'a': 'agent',
        'm': 'model_selection',
    }
    workflow = {
        'root': [
            'welcome',
            'framework', 
            'project', 
            'after_project',
            'router', 
        ],
        'agent': [
            'agent_details', 
            'model_selection', 
            'tool_selection', 
            'after_agent',
            'router', 
        ], 
        'task': [
            'task_details', 
            'agent_selection', 
            'after_task',
            'router', 
        ],
    }
    
    @classmethod
    def wrapper(cls, stdscr):
        app = cls(stdscr)
        
        app.load('welcome')
        app.run()


def main():
    import io
    log.set_stdout(io.StringIO())  # disable on-screen logging
    
    curses.wrapper(WizardApp.wrapper)

