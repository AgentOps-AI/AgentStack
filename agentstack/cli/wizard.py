import sys
import curses
import time
import math
from random import randint
from dataclasses import dataclass
from typing import Optional, Any, Union, TypedDict
from enum import Enum
from pathlib import Path

from agentstack import conf, log
from agentstack.utils import is_snake_case
from agentstack.tui import *
from agentstack.frameworks import SUPPORTED_FRAMEWORKS, CREWAI, LANGGRAPH
from agentstack._tools import get_all_tools, get_tool
from agentstack.proj_templates import TemplateConfig
from agentstack.cli import LOGO, init_project


COLOR_BORDER = Color(90)
COLOR_MAIN = Color(220)
COLOR_TITLE = Color(220, 100, 40, reversed=True)
COLOR_ERROR = Color(0)
COLOR_FORM = Color(300)
COLOR_FORM_BORDER = Color(300, 50)
COLOR_BUTTON = Color(300, reversed=True)
COLOR_FIELD_BG = Color(240, 20, 100, reversed=True)
COLOR_FIELD_BORDER = Color(300, 100, 50)
COLOR_FIELD_ACTIVE = Color(300, 80)

class FieldColors(TypedDict):
    color: Color
    border: Color
    active: Color

FIELD_COLORS: FieldColors = {
    'color': COLOR_FIELD_BG, 
    'border': COLOR_FIELD_BORDER, 
    'active': COLOR_FIELD_ACTIVE, 
}

class LogoElement(Text):
    h_align = ALIGN_CENTER
    
    def __init__(self, coords: tuple[int, int], dims: tuple[int, int]):
        super().__init__(coords, dims)
        self.color = COLOR_MAIN
        self.value = LOGO
        self.stars = [(3, 1), (25, 5), (34, 1), (52, 2), (79, 3), (97, 1)]
        self._star_colors = {}
        content_width = len(LOGO.split('\n')[0])
        self.left_offset = round((self.width - content_width) / 2)
    
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
            if self.width <= x or self.height <= y:
                continue
            self.grid.addch(y, self.left_offset + x, '*', self._get_star_color(i).to_curses())


class StarBox(Box):
    """Renders random stars that animate down the page in the background of the box."""
    def __init__(self, coords: tuple[int, int], dims: tuple[int, int], **kwargs):
        super().__init__(coords, dims, **kwargs)
        self.stars = [(randint(0, self.width-1), randint(0, self.height-1)) for _ in range(11)]
        self.star_colors = [ColorAnimation(
            Color(randint(0, 150)), 
            Color(randint(200, 360)), 
            duration=2.0, 
            loop=False, 
        ) for _ in range(11)]
        self.star_y = [randint(0, self.height-1) for _ in range(11)]
        self.star_x = [randint(0, self.width-1) for _ in range(11)]
        self.star_speed = 0.001
        self.star_timer = 0.0
        self.star_index = 0

    def render(self) -> None:
        self.grid.clear()
        for i in range(len(self.stars)):
            if self.star_y[i] < self.height:
                self.grid.addch(self.star_y[i], self.star_x[i], '*', self.star_colors[i].to_curses())
                self.star_y[i] += 1
            else:
                self.star_y[i] = 0
                self.star_x[i] = randint(0, self.width-1)
        super().render()


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


class WizardView(View):
    app: 'WizardApp'


class BannerView(WizardView):
    name = "banner"
    title = "Welcome to AgentStack"
    sparkle = "The easiest way to build a robust agent application."
    subtitle = "Let's get started!"
    color = ColorAnimation(
        start=Color(90, 0, 0),  # TODO make this darker
        end=Color(90),
        duration=0.5
    )
    
    def layout(self) -> list[Renderable]:
        buttons = []

        if not self.app.state.project:
            # no project yet, so we need to create one
            buttons.append(Button(
                # center button full width below the subtitle
                (round(self.height / 2)+(len(buttons)*4), round(self.width/2/2)),
                (3, round(self.width/2)),
                "Create Project", 
                color=COLOR_BUTTON,
                on_confirm=lambda: self.app.load('project', workflow='project'),
            ))
        else:
            # project has been created, so we can add agents
            buttons.append(Button(
                (round(self.height / 2)+(len(buttons)*4), round(self.width/2/2)),
                (3, round(self.width/2)),
                "Add Agent", 
                color=COLOR_BUTTON,
                on_confirm=lambda: self.app.load('agent', workflow='agent'),
            ))

        if len(self.app.state.agents):
            # we have one or more agents, so we can add tasks
            buttons.append(Button(
                (round(self.height / 2)+(len(buttons)*4), round(self.width/2/2)),
                (3, round(self.width/2)),
                "Add Task", 
                color=COLOR_BUTTON,
                on_confirm=lambda: self.app.load('task', workflow='task'),
            ))
            
            # # we can also add more tools to existing agents
            # buttons.append(Button(
            #     (self.height-6, self.width-34), 
            #     (3, 15), 
            #     "Add Tool", 
            #     color=COLOR_BUTTON,
            #     on_confirm=lambda: self.app.load('tool_category', workflow='agent'),
            # ))

        if self.app.state.project:
            # we can complete the project
            buttons.append(Button(
                (round(self.height / 2)+(len(buttons)*4), round(self.width/2/2)),
                (3, round(self.width/2)),
                "Finish",
                color=COLOR_BUTTON,
                on_confirm=lambda: self.app.finish(),
            ))

        return [
            StarBox((0, 0), (self.height, self.width), color=COLOR_BORDER, modules=[
                LogoElement((1, 1), (7, self.width-2)),
                Box(
                    (round(self.height / 4), round(self.width / 4)), 
                    (9, round(self.width / 2)), 
                    color=COLOR_BORDER, 
                    modules=[
                        Title((1, 1), (2, round(self.width / 2)-2), color=self.color, value=self.title),
                        Title((3, 1), (2, round(self.width / 2)-2), color=self.color, value=self.sparkle),
                        Title((5, 1), (2, round(self.width / 2)-2), color=self.color, value=self.subtitle),
                    ]),
                *buttons,
            ]),
        ]


class FormView(WizardView):
    title: str
    error_message: Node
    
    def __init__(self, app: 'App'):
        super().__init__(app)
        self.error_message = Node()

    def submit(self):
        pass
    
    def error(self, message: str):
        self.error_message.value = message
    
    def form(self) -> list[Renderable]:
        return []
    
    def layout(self) -> list[Renderable]:
        return [
            Box((0, 0), (self.height-1, self.width), color=COLOR_BORDER, modules=[
                LogoElement((1, 1), (7, self.width-2)),
                Title((9, 1), (1, self.width-3), color=COLOR_TITLE, value=self.title),
                Title((10, 1), (1, self.width-3), color=COLOR_ERROR, value=self.error_message),
                *self.form(),
                Button((self.height-6, self.width-17), (3, 15), "Next", color=COLOR_BUTTON, on_confirm=self.submit),
            ]),
            HelpText((self.height-1, 0), (1, self.width)),
        ]


class ProjectView(FormView):
    title = "Define your Project"
    
    def __init__(self, app: 'App'):
        super().__init__(app)
        self.project_name = Node()
        self.project_description = Node()
    
    def submit(self):
        if not self.project_name.value:
            self.error("Name is required.")
            return

        if not is_snake_case(self.project_name.value):
            self.error("Name must be in snake_case.")
            return
        
        self.app.state.create_project(
            name=self.project_name.value,
            description=self.project_description.value,
        )
        self.app.advance()
    
    def form(self) -> list[Renderable]:
        return [
            Text((12, 2), (1, 11), color=COLOR_FORM, value="Name"),
            TextInput((12, 13), (2, self.width - 15), self.project_name, **FIELD_COLORS), 
            
            Text((14, 2), (1, 11), color=COLOR_FORM, value="Description"),
            TextInput((14, 13), (5, self.width - 15), self.project_description, **FIELD_COLORS),
        ]


class FrameworkView(FormView):
    title = "Select a Framework"
    
    FRAMEWORK_OPTIONS = {
        CREWAI: {'name': "CrewAI", 'description': "A simple and easy-to-use framework."},
        LANGGRAPH: {'name': "LangGraph", 'description': "A powerful and flexible framework."},
    }
    
    def __init__(self, app: 'App'):
        super().__init__(app)
        self.framework_key = Node()
        self.framework_logo = Node()
        self.framework_name = Node()
        self.framework_description = Node()
    
    def set_framework_selection(self, index: int, value: str):
        """Update the content of the framework info box."""
        key, data = None, None
        for _key, _value in self.FRAMEWORK_OPTIONS.items():
            if _value['name'] == value:  # search by name
                key = _key
                data = _value
                break
        
        if not key or not data:
            key = value
            data = {
                'name': "Unknown",
                'description': "Unknown",
            }
        
        self.framework_logo.value = data['name']
        self.framework_name.value = data['name']
        self.framework_description.value = data['description']
    
    def set_framework_choice(self, index: int, value: str):
        """Save the selection."""
        key = None
        for _key, _value in self.FRAMEWORK_OPTIONS.items():
            if _value['name'] == value:  # search by name
                key = _key
                break
        
        self.framework_key.value = key
    
    def get_framework_options(self) -> list[str]:
        return [self.FRAMEWORK_OPTIONS[key]['name'] for key in SUPPORTED_FRAMEWORKS]
    
    def submit(self):
        if not self.framework_key.value:
            self.error("Framework is required.")
            return
        
        self.app.state.update_active_project(framework=self.framework_key.value)
        self.app.advance()
    
    def form(self) -> list[Renderable]:
        return [
            RadioSelect(
                (12, 1), (self.height-18, round(self.width/2)-3), 
                options=self.get_framework_options(), 
                color=COLOR_FORM_BORDER, 
                highlight=ColorAnimation(
                    COLOR_BUTTON.sat(0), COLOR_BUTTON, duration=0.2
                ), 
                on_change=self.set_framework_selection, 
                on_select=self.set_framework_choice
            ),
            Box((12, round(self.width/2)), (self.height-18, round(self.width/2)-3), color=COLOR_FORM_BORDER, modules=[
                ASCIIText((1, 3), (4, round(self.width/2)-10), color=COLOR_FORM.sat(40), value=self.framework_logo),
                BoldText((5, 3), (1, round(self.width/2)-10), color=COLOR_FORM, value=self.framework_name), 
                WrappedText((7, 3), (5, round(self.width/2)-10), color=COLOR_FORM.sat(50), value=self.framework_description),
            ]),
        ]


class AfterProjectView(BannerView):
    title = "We've got a project!"
    sparkle = "*ﾟ･:*:･ﾟ’★,｡･:*:･ﾟ’☆"
    subtitle = "Now, add an Agent to handle your tasks!"


class AgentView(FormView):
    title = "Define your Agent"
    
    def __init__(self, app: 'App'):
        super().__init__(app)
        self.agent_name = Node()
        self.agent_role = Node()
        self.agent_goal = Node()
        self.agent_backstory = Node()
    
    def submit(self):
        if not self.agent_name.value:
            self.error("Name is required.")
            return

        if not is_snake_case(self.agent_name.value):
            self.error("Name must be in snake_case.")
            return

        self.app.state.create_agent(
            name=self.agent_name.value,
            role=self.agent_role.value,
            goal=self.agent_goal.value,
            backstory=self.agent_backstory.value,
        )
        self.app.advance()
    
    def form(self) -> list[Renderable]:
        return [
            Text((12, 2), (1, 11), color=COLOR_FORM, value="Name"),
            TextInput((12, 13), (2, self.width - 15), self.agent_name, **FIELD_COLORS), 
            
            Text((14, 2), (1, 11), color=COLOR_FORM, value="Role"),
            TextInput((14, 13), (5, self.width - 15), self.agent_role, **FIELD_COLORS),
            
            Text((19, 2), (1, 11), color=COLOR_FORM, value="Goal"),
            TextInput((19, 13), (5, self.width - 15), self.agent_goal, **FIELD_COLORS),
            
            Text((24, 2), (1, 11), color=COLOR_FORM, value="Backstory"),
            TextInput((24, 13), (5, self.width - 15), self.agent_backstory, **FIELD_COLORS),
        ]


class ModelView(FormView):
    title = "Select a Model"
    
    MODEL_OPTIONS = [
        {'value': "anthropic/claude-3.5-sonnet", 'name': "Claude 3.5 Sonnet", 'provider': "Anthropic", 'description': "A fast and cost-effective model."}, 
        {'value': "gpt-3.5-turbo", 'name': "GPT-3.5 Turbo", 'provider': "OpenAI", 'description': "A fast and cost-effective model."}, 
        {'value': "gpt-4", 'name': "GPT-4", 'provider': "OpenAI", 'description': "A more advanced model with better understanding."},
        {'value': "gpt-4o", 'name': "GPT-4o", 'provider': "OpenAI", 'description': "The latest and most powerful model."},
        {'value': "gpt-4o-mini", 'name': "GPT-4o Mini", 'provider': "OpenAI", 'description': "A smaller, faster version of GPT-4o."},
    ]
    
    
    def __init__(self, app: 'App'):
        super().__init__(app)
        self.model_choice = Node()
        self.model_logo = Node()
        self.model_name = Node()
        self.model_description = Node()
    
    def set_model_selection(self, index: int, value: str):
        """Update the content of the model info box."""
        model = self.MODEL_OPTIONS[index]
        self.model_logo.value = model['provider']
        self.model_name.value = model['name']
        self.model_description.value = model['description']
    
    def set_model_choice(self, index: int, value: str):
        """Save the selection."""
        # list in UI shows the actual key
        self.model_choice.value = value
    
    def get_model_options(self):
        return [model['value'] for model in self.MODEL_OPTIONS]
    
    def submit(self):
        if not self.model_choice.value:
            self.error("Model is required.")
            return
        
        self.app.state.update_active_agent(llm=self.model_choice.value)
        self.app.advance()
    
    def form(self) -> list[Renderable]:
        return [
            RadioSelect(
                (11, 1), (self.height-18, round(self.width/2)-3), 
                options=self.get_model_options(),
                color=COLOR_FORM_BORDER, 
                highlight=ColorAnimation(
                    COLOR_BUTTON.sat(0), COLOR_BUTTON, duration=0.2
                ), 
                on_change=self.set_model_selection,
                on_select=self.set_model_choice
            ),
            Box((11, round(self.width/2)), (self.height-18, round(self.width/2)-3), color=COLOR_FORM_BORDER, modules=[
                ASCIIText((1, 3), (4, round(self.width/2)-10), color=COLOR_FORM.sat(40), value=self.model_logo),
                BoldText((5, 3), (1, round(self.width/2)-10), color=COLOR_FORM, value=self.model_name), 
                WrappedText((7, 3), (5, round(self.width/2)-10), color=COLOR_FORM.sat(50), value=self.model_description),
            ]),
        ]


class ToolCategoryView(FormView):
    title = "Select a Tool Category"
    
    # TODO category descriptions for all valid categories
    TOOL_CATEGORY_OPTIONS = {
        "web": {'name': "Web Tools", 'description': "Tools that interact with the web."},
        "file": {'name': "File Tools", 'description': "Tools that interact with the file system."},
        "code": {'name': "Code Tools", 'description': "Tools that interact with code."},
    }
    
    def __init__(self, app: 'App'):
        super().__init__(app)
        self.tool_category_key = Node()
        self.tool_category_name = Node()
        self.tool_category_description = Node()
    
    def set_tool_category_selection(self, index: int, value: str):
        key, data = None, None
        for _key, _value in self.TOOL_CATEGORY_OPTIONS.items():
            if _value['name'] == value:  # search by name
                key = _key
                data = _value
                break
        
        if not key or not data:
            key = value
            data = {
                'name': "Unknown",
                'description': "Unknown",
            }
        
        self.tool_category_name.value = data['name']
        self.tool_category_description.value = data['description']
    
    def set_tool_category_choice(self, index: int, value: str):
        self.tool_category_key.value = value
    
    def get_tool_category_options(self) -> list[str]:
        return sorted(list({tool.category for tool in get_all_tools()}))
    
    def submit(self):
        if not self.tool_category_key.value:
            self.error("Tool category is required.")
            return
        
        self.app.state.tool_category = self.tool_category_key.value
        self.app.advance()
    
    def form(self) -> list[Renderable]:
        return [
            RadioSelect(
                (11, 1), (self.height-18, round(self.width/2)-3), 
                options=self.get_tool_category_options(), 
                color=COLOR_FORM_BORDER, 
                highlight=ColorAnimation(
                        COLOR_BUTTON.sat(0), COLOR_BUTTON, duration=0.2
                ), 
                on_change=self.set_tool_category_selection,
                on_select=self.set_tool_category_choice
            ),
            Box((11, round(self.width/2)), (self.height-18, round(self.width/2)-3), color=COLOR_FORM_BORDER, modules=[
                BoldText((1, 3), (1, round(self.width/2)-10), color=COLOR_FORM, value=self.tool_category_name), 
                WrappedText((2, 3), (5, round(self.width/2)-10), color=COLOR_FORM.sat(50), value=self.tool_category_description),
            ]),
        ]


class ToolView(FormView):
    title = "Select a Tool"
    
    def __init__(self, app: 'App'):
        super().__init__(app)
        self.tool_key = Node()
        self.tool_name = Node()
        self.tool_description = Node()
    
    @property
    def category(self) -> str:
        return self.app.state.tool_category
    
    def set_tool_selection(self, index: int, value: str):
        tool_config = get_tool(value)
        self.tool_name.value = tool_config.name
        self.tool_description.value = tool_config.cta
    
    def set_tool_choice(self, index: int, value: str):
        self.tool_key.value = value
    
    def get_tool_options(self) -> list[str]:
        return sorted([tool.name for tool in get_all_tools() if tool.category == self.category])
    
    def submit(self):
        if not self.tool_key.value:
            self.error("Tool is required.")
            return
        
        self.app.state.update_active_agent_tools(self.tool_key.value)
        self.app.advance()
    
    def back(self):
        self.app.back()
    
    def form(self) -> list[Renderable]:
        return [
            RadioSelect(
                (12, 1), (self.height-18, round(self.width/2)-3), 
                options=self.get_tool_options(),
                color=COLOR_FORM_BORDER, 
                highlight=ColorAnimation(
                        COLOR_BUTTON.sat(0), COLOR_BUTTON, duration=0.2
                ), 
                on_change=self.set_tool_selection,
                on_select=self.set_tool_choice
            ),
            Box((12, round(self.width/2)), (self.height-18, round(self.width/2)-3), color=COLOR_FORM_BORDER, modules=[
                BoldText((1, 3), (1, round(self.width/2)-10), color=COLOR_FORM, value=self.tool_name), 
                WrappedText((2, 3), (5, round(self.width/2)-10), color=COLOR_FORM.sat(50), value=self.tool_description),
            ]),
            Button((self.height-6, self.width-17), (3, 15), "Back", color=COLOR_BUTTON, on_confirm=self.back),
        ]


class AfterAgentView(BannerView):
    title = "Boom! We made some agents."
    sparkle = "(ﾉ>ω<)ﾉ :｡･:*:･ﾟ’★,｡･:*:･ﾟ’☆"
    subtitle = "Now lets make some tasks for the agents to accomplish!"


class TaskView(FormView):
    title = "Define your Task"
    
    def __init__(self, app: 'App'):
        super().__init__(app)
        self.task_name = Node()
        self.task_description = Node()
        self.expected_output = Node()
    
    def submit(self):
        if not self.task_name.value:
            self.error("Task name is required.")
            return

        if not is_snake_case(self.task_name.value):
            self.error("Task name must be in snake_case.")
            return

        self.app.state.create_task(
            name=self.task_name.value,
            description=self.task_description.value,
            expected_output=self.expected_output.value,
        )
        self.app.advance()
    
    def form(self) -> list[Renderable]:
        return [
            Text((12, 2), (1, 11), color=COLOR_FORM, value="Name"),
            TextInput((12, 13), (2, self.width - 15), self.task_name, **FIELD_COLORS), 
            
            Text((14, 2), (1, 11), color=COLOR_FORM, value="Description"),
            TextInput((14, 13), (5, self.width - 15), self.task_description, **FIELD_COLORS),
            
            Text((19, 2), (1, 11), color=COLOR_FORM, value="Expected Output"),
            TextInput((19, 13), (5, self.width - 15), self.expected_output, **FIELD_COLORS),
        ]


class AgentSelectionView(FormView):
    title = "Select an Agent for your Task"
    
    def __init__(self, app: 'App'):
        super().__init__(app)
        self.agent_name = Node()
    
    def set_agent_choice(self, index: int, value: str):
        self.agent_name.value = value
    
    def get_agent_options(self) -> list[str]:
        return list(self.app.state.agents.keys())
    
    def submit(self):
        if not self.agent_name.value:
            self.error("Agent is required.")
            return
        
        self.app.state.update_active_task(agent=self.agent_name.value)
        self.app.advance()

    def form(self) -> list[Renderable]:
        return [
            RadioSelect(
                (12, 1), (self.height-18, round(self.width/2)-3), 
                options=self.get_agent_options(),
                color=COLOR_FORM_BORDER, 
                highlight=ColorAnimation(
                        COLOR_BUTTON.sat(0), COLOR_BUTTON, duration=0.2
                ), 
                on_select=self.set_agent_choice
            ),
            # TODO agent info pane
        ]


class AfterTaskView(BannerView):
    title = "Let there be tasks!"
    sparkle = "(ノ ˘_˘)ノ　ζ|||ζ　ζ|||ζ　ζ|||ζ"
    subtitle = "Tasks are the heart of your agent's work. "


class DebugView(WizardView):
    name = "debug"
    def layout(self) -> list[Renderable]:
        from agentstack.utils import get_version
        
        return [
            Box((0, 0), (self.height-1, self.width), color=COLOR_BORDER, modules=[
                ColorWheel((1, 1)),
                Title((self.height-6, 3), (1, self.width-5), color=COLOR_MAIN, 
                     value=f"AgentStack version {get_version()}"),
                Title((self.height-4, 3), (1, self.width-5), color=COLOR_MAIN,
                        value=f"Window size: {self.width}x{self.height}"),
            ]),
            HelpText((self.height-1, 0), (1, self.width)),
        ]


class State:
    project: dict[str, Any]
    # `active_agent` is the agent we are currently working on
    active_agent: str
    # `active_task` is the task we are currently working on
    active_task: str
    # `tool_category` is a temporary value while an agent is being created
    tool_category: str
    # `agents` is a dictionary of agents we have created
    agents: dict[str, dict]
    # `tasks` is a dictionary of tasks we have created
    tasks: dict[str, dict]
    
    def __init__(self):
        self.project = {}
        self.agents = {}
        self.tasks = {}
    
    def __repr__(self):
        return f"State(project={self.project}, agents={self.agents}, tasks={self.tasks})"
    
    def create_project(self, name: str, description: str):
        self.project = {
            'name': name,
            'description': description,
        }
        self.active_project = name
    
    def update_active_project(self, **kwargs):
        for key, value in kwargs.items():
            self.project[key] = value
    
    def create_agent(self, name: str, role: str, goal: str, backstory: str):
        self.agents[name] = {
            'role': role, 
            'goal': goal, 
            'backstory': backstory, 
            'llm': None, 
            'tools': [], 
        }
        self.active_agent = name
    
    def update_active_agent(self, **kwargs):
        agent = self.agents[self.active_agent]
        for key, value in kwargs.items():
            agent[key] = value
    
    def update_active_agent_tools(self, tool_name: str):
        self.agents[self.active_agent]['tools'].append(tool_name)

    def create_task(self, name: str, description: str, expected_output: str):
        self.tasks[name] = {
            'description': description, 
            'expected_output': expected_output, 
        }
        self.active_task = name
    
    def update_active_task(self, **kwargs):
        task = self.tasks[self.active_task]
        for key, value in kwargs.items():
            task[key] = value

    def to_template_config(self) -> TemplateConfig:
        tools = []
        for agent_name, agent_data in self.agents.items():
            for tool_name in agent_data['tools']:
                tools.append(TemplateConfig.Tool(
                    name=tool_name,
                    agents=[agent_name],
                ))
        
        return TemplateConfig(
            template_version=4,
            name=self.project['name'],
            description=self.project['description'],
            framework=self.project['framework'],
            method="sequential",
            agents=[TemplateConfig.Agent(
                name=agent_name,
                role=agent_data['role'],
                goal=agent_data['goal'],
                backstory=agent_data['backstory'],
                llm=agent_data['llm'],
            ) for agent_name, agent_data in self.agents.items()],
            tasks=[TemplateConfig.Task(
                name=task_name,
                description=task_data['description'],
                expected_output=task_data['expected_output'],
                agent=self.active_agent,
            ) for task_name, task_data in self.tasks.items()],
            tools=tools,
        )


class WizardApp(App):
    views = {
        'welcome': BannerView, 
        'framework': FrameworkView, 
        'project': ProjectView, 
        'after_project': AfterProjectView, 
        'agent': AgentView, 
        'model': ModelView, 
        'tool_category': ToolCategoryView, 
        'tool': ToolView, 
        'after_agent': AfterAgentView, 
        'task': TaskView, 
        'agent_selection': AgentSelectionView, 
        'after_task': AfterTaskView, 
        'debug': DebugView, 
    }
    shortcuts = {
        'd': 'debug',
    }
    workflow = {
        'project': [  # initialize a project
            'welcome', 
            'project', 
            'framework', 
            'after_project', 
        ],
        'agent': [  # add agents
            'agent', 
            'model', 
            'tool_category', 
            'tool', 
            'after_agent', 
        ], 
        'task': [  # add tasks
            'task', 
            'agent_selection', 
            'after_task',
        ],
        # 'tool': [ # add tools to an agent
        #     'agent_select', 
        #     'tool_category',
        #     'tool',
        #     'after_agent',
        # ]
    }
    
    state: State
    active_workflow: Optional[str]
    active_view: Optional[str]
    
    min_width: int = 80
    min_height: int = 30
    
    # the main loop can still execute once more after this; so we create an 
    # explicit marker to ensure the template is only written once
    _finish_run_once: bool = True
    
    def start(self):
        """Load the first view in the default workflow."""
        view = self.workflow['project'][0]
        self.load(view, workflow='project')
    
    def finish(self):
        """Create the project, write the config file, and exit."""
        template = self.state.to_template_config()
        
        self.stop()
        
        if self._finish_run_once:
            log.set_stdout(sys.stdout)  # re-enable on-screen logging
            
            init_project(
                slug_name=template.name,
                template_data=template,
            )
            
            template.write_to_file(conf.PATH / "wizard")
            log.info(f"Saved template to: {conf.PATH / 'wizard.json'}")
            self._finish_run_once = False
    
    def advance(self):
        """Load the next view in the active workflow."""
        workflow = self.workflow[self.active_workflow]
        current_index = workflow.index(self.active_view)
        view = workflow[current_index + 1]
        self.load(view, workflow=self.active_workflow)
    
    def back(self):
        """Load the previous view in the active workflow."""
        workflow = self.workflow[self.active_workflow]
        current_index = workflow.index(self.active_view)
        view = workflow[current_index - 1]
        self.load(view, workflow=self.active_workflow)
    
    def load(self, view: str, workflow: Optional[str] = None):
        """Load a view from a workflow."""
        self.active_workflow = workflow
        self.active_view = view
        super().load(view)
    
    @classmethod
    def wrapper(cls, stdscr):
        app = cls(stdscr)
        app.state = State()
        
        app.start()
        app.run()


def main():
    import io
    log.set_stdout(io.StringIO())  # disable on-screen logging
    
    curses.wrapper(WizardApp.wrapper)

