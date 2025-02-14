import os, sys
import curses
import time
import math
from random import randint
from dataclasses import dataclass
from typing import Optional, Any, Union, TypedDict
from enum import Enum
from pathlib import Path
from abc import abstractmethod, ABCMeta

from agentstack import conf, log
from agentstack.utils import is_snake_case
from agentstack.tui import *
from agentstack import providers
from agentstack import frameworks
from agentstack._tools import (
    get_all_tools,
    get_tool,
    get_all_tool_categories,
    get_all_tool_category_names,
)
from agentstack.templates import TemplateConfig
from agentstack.cli import LOGO, init_project


COLOR_BORDER = Color(90)
COLOR_MAIN = Color(220)
COLOR_TITLE = Color(220, 100, 40, reversed=True)
COLOR_ERROR = Color(0, 70)
COLOR_BANNER = Color(80, 80, 80)
COLOR_FORM = Color(300)
COLOR_FORM_BORDER = Color(300, 80)
COLOR_BUTTON = Color(300, 100, 80, reversed=True)
COLOR_FIELD_BG = Color(300, 50, 50, reversed=True)
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
        self.left_offset = max(0, round((self.width - content_width) / 2))

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
            try:
                self.grid.addch(y, self.left_offset + x, '*', self._get_star_color(i).to_curses())
            except curses.error:
                pass  # overflow


class StarBox(Box):
    """Renders random stars that animate down the page in the background of the box."""

    def __init__(self, coords: tuple[int, int], dims: tuple[int, int], **kwargs):
        super().__init__(coords, dims, **kwargs)
        self.stars = [(randint(0, self.width - 1), randint(0, self.height - 1)) for _ in range(11)]
        self.star_colors = [
            ColorAnimation(
                Color(randint(0, 150)),
                Color(randint(200, 360)),
                duration=2.0,
                loop=False,
            )
            for _ in range(11)
        ]
        self.star_y = [randint(0, self.height - 1) for _ in range(11)]
        self.star_x = [randint(0, self.width - 1) for _ in range(11)]
        self.star_speed = 0.001
        self.star_timer = 0.0
        self.star_index = 0

    def render(self) -> None:
        self.grid.clear()
        for i in range(len(self.stars)):
            if self.star_y[i] > 0:  # undraw previous star position
                self.grid.addch(self.star_y[i] - 1, self.star_x[i], ' ')
            else:  # previous star was at bottom of screen
                self.grid.addch(self.height - 1, self.star_x[i], ' ')

            if self.star_y[i] < self.height:
                self.grid.addch(self.star_y[i], self.star_x[i], '*', self.star_colors[i].to_curses())
                self.star_y[i] += 1
            else:
                self.star_y[i] = 0
                self.star_x[i] = randint(0, self.width - 1)
        super().render()


class HelpText(Text):
    def __init__(self, coords: tuple[int, int], dims: tuple[int, int]) -> None:
        super().__init__(coords, dims)
        self.color = Color(0, 0, 70)
        self.value = " | ".join(
            [
                "select [tab]",
                "navigate [up / down]",
                "confirm [space / enter]",
                "[q]uit",
            ]
        )
        if conf.DEBUG:
            self.value += " | [d]ebug"


class WizardView(View):
    app: 'WizardApp'


class BannerView(WizardView):
    name = "banner"
    title = "Welcome to AgentStack"
    sparkle = "The easiest way to build a robust agent application."
    subtitle = "Let's get started!"

    def _get_color(self) -> Color:
        return ColorAnimation(
            start=COLOR_BANNER.sat(0).val(0),
            end=COLOR_BANNER,
            duration=0.5,
        )

    def layout(self) -> list[Renderable]:
        buttons_conf: dict[str, Callable] = {}

        if not self.app.state.project:
            buttons_conf["Create Project"] = lambda: self.app.load('project', workflow='project')
        else:
            buttons_conf["New Agent"] = lambda: self.app.load('agent', workflow='agent')

        if len(self.app.state.agents):
            buttons_conf["New Task"] = lambda: self.app.load('task', workflow='task')
            buttons_conf["Add Tools"] = lambda: self.app.load('tool_agent_selection', workflow='tool')

        if self.app.state.project:
            buttons_conf["Finish"] = lambda: self.app.finish()

        buttons: list[Button] = []
        num_buttons = len(buttons_conf)
        button_width = min(round(self.width / 2), round(self.width / num_buttons) - 2)
        left_offset = round((self.width - (num_buttons * button_width)) / 2) if num_buttons == 1 else 2

        for title, action in buttons_conf.items():
            buttons.append(
                Button(
                    (self.height - 5, left_offset),
                    (3, button_width),
                    title,
                    color=COLOR_BUTTON,
                    on_confirm=action,
                )
            )
            left_offset += button_width + 1

        return [
            StarBox(
                (0, 0),
                (self.height - 1, self.width),
                color=COLOR_BORDER,
                modules=[
                    LogoElement((1, 1), (7, self.width - 2)),
                    Box(
                        (round(self.height / 3), round(self.width / 4)),
                        (9, round(self.width / 2)),
                        color=COLOR_BANNER,
                        modules=[
                            BoldText(
                                (1, 2),
                                (2, round(self.width / 2) - 3),
                                color=self._get_color(),
                                value=self.title,
                            ),
                            WrappedText(
                                (3, 2),
                                (3, round(self.width / 2) - 3),
                                color=self._get_color(),
                                value=self.sparkle,
                            ),
                            WrappedText(
                                (6, 2),
                                (2, round(self.width / 2) - 3),
                                color=self._get_color(),
                                value=self.subtitle,
                            ),
                        ],
                    ),
                    *buttons,
                ],
            ),
            HelpText((self.height - 1, 0), (1, self.width)),
        ]


class FormView(WizardView, metaclass=ABCMeta):
    title: str
    error_message: Node

    def __init__(self, app: 'App'):
        super().__init__(app)
        self.error_message = Node()

    def submit(self):
        pass

    def error(self, message: str):
        self.error_message.value = message

    @abstractmethod
    def form(self) -> list[Renderable]: ...

    def layout(self) -> list[Renderable]:
        return [
            Box(
                (0, 0),
                (self.height - 1, self.width),
                color=COLOR_BORDER,
                modules=[
                    LogoElement((1, 1), (7, self.width - 2)),
                    Title((9, 1), (1, self.width - 2), color=COLOR_TITLE, value=self.title),
                    Title(
                        (self.height - 5, round(self.width / 3)),
                        (3, round(self.width / 3)),
                        color=COLOR_ERROR,
                        value=self.error_message,
                    ),
                    *self.form(),
                    Button(
                        (self.height - 5, self.width - 17),
                        (3, 15),
                        "Next",
                        color=COLOR_BUTTON,
                        on_confirm=self.submit,
                    ),
                ],
            ),
            HelpText((self.height - 1, 0), (1, self.width)),
        ]


class AgentSelectionView(FormView, metaclass=ABCMeta):
    title = "Select an Agent"

    def __init__(self, app: 'App'):
        super().__init__(app)
        self.agent_key = Node()
        self.agent_name = Node()
        self.agent_llm = Node()
        self.agent_description = Node()

    def set_agent_selection(self, index: int, value: str):
        agent_data = self.app.state.agents[value]
        self.agent_name.value = value
        self.agent_llm.value = agent_data['llm']
        self.agent_description.value = agent_data['role']

    def set_agent_choice(self, index: int, value: str):
        self.agent_key.value = value

    def get_agent_options(self) -> list[str]:
        return list(self.app.state.agents.keys())

    @abstractmethod
    def submit(self): ...

    def form(self) -> list[Renderable]:
        return [
            RadioSelect(
                (10, 1),
                (self.height - 15, round(self.width / 2) - 2),
                options=self.get_agent_options(),
                color=COLOR_FORM_BORDER,
                highlight=ColorAnimation(COLOR_BUTTON.sat(0), COLOR_BUTTON, duration=0.2),
                on_change=self.set_agent_selection,
                on_select=self.set_agent_choice,
            ),
            Box(
                (10, round(self.width / 2) + 1),
                (self.height - 15, round(self.width / 2) - 2),
                color=COLOR_FORM_BORDER,
                modules=[
                    ASCIIText(
                        (1, 3),
                        (4, round(self.width / 2) - 10),
                        color=COLOR_FORM.sat(40),
                        value=self.agent_name,
                    ),
                    BoldText((5, 3), (1, round(self.width / 2) - 10), color=COLOR_FORM, value=self.agent_llm),
                    WrappedText(
                        (7, 3),
                        (min(5, self.height - 24), round(self.width / 2) - 10),
                        color=COLOR_FORM.sat(50),
                        value=self.agent_description,
                    ),
                ],
            ),
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

        if os.path.exists(conf.PATH / self.project_name.value):
            self.error(f"Directory '{self.project_name.value}' already exists.")
            return

        self.app.state.create_project(
            name=self.project_name.value,
            description=self.project_description.value,
        )
        self.app.advance()

    def form(self) -> list[Renderable]:
        return [
            Text((11, 2), (1, 12), color=COLOR_FORM, value="Name"),
            TextInput(
                (11, 14),
                (2, self.width - 15),
                self.project_name,
                placeholder="This will be used to create a new directory. Must be snake_case.",
                **FIELD_COLORS,
            ),
            Text((13, 2), (1, 12), color=COLOR_FORM, value="Description"),
            TextInput(
                (13, 14),
                (5, self.width - 15),
                self.project_description,
                placeholder="Describe what you project will do.",
                **FIELD_COLORS,
            ),
        ]


class FrameworkView(FormView):
    title = "Select a Framework"

    def __init__(self, app: 'App'):
        super().__init__(app)
        self.framework_key = Node()
        self.framework_name = Node()
        self.framework_description = Node()
        self.framework_options = {
            key: frameworks.get_framework_info(key) for key in frameworks.SUPPORTED_FRAMEWORKS
        }

    def set_framework_selection(self, index: int, value: str):
        """Update the content of the framework info box."""
        data = self.framework_options[value]
        self.framework_name.value = data['name']
        self.framework_description.value = data['description']

    def set_framework_choice(self, index: int, value: str):
        """Save the selection."""
        self.framework_key.value = value

    def submit(self):
        if not self.framework_key.value:
            self.error("Framework is required.")
            return

        self.app.state.update_framework(self.framework_key.value)
        self.app.advance()

    def form(self) -> list[Renderable]:
        return [
            RadioSelect(
                (10, 1),
                (self.height - 15, round(self.width / 2) - 2),
                options=list(self.framework_options.keys()),
                color=COLOR_FORM_BORDER,
                highlight=ColorAnimation(COLOR_BUTTON.sat(0), COLOR_BUTTON, duration=0.2),
                on_change=self.set_framework_selection,
                on_select=self.set_framework_choice,
            ),
            Box(
                (10, round(self.width / 2)),
                (self.height - 15, round(self.width / 2) - 2),
                color=COLOR_FORM_BORDER,
                modules=[
                    ASCIIText(
                        (1, 3),
                        (4, round(self.width / 2) - 10),
                        color=COLOR_FORM.sat(40),
                        value=self.framework_name,
                    ),
                    BoldText(
                        (5, 3), (1, round(self.width / 2) - 10), color=COLOR_FORM, value=self.framework_name
                    ),
                    WrappedText(
                        (7, 3),
                        (min(5, self.height - 24), round(self.width / 2) - 10),
                        color=COLOR_FORM.sat(50),
                        value=self.framework_description,
                    ),
                ],
            ),
        ]


class AfterProjectView(BannerView):
    title = "We've got a project!"
    sparkle = "(づ ◕‿◕ )づ *ﾟ･:*:･ﾟ’★,｡･:*:･ﾟ’☆"
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
        agent_name = self.agent_name.value
        if not agent_name:
            self.error("Name is required.")
            return

        if not is_snake_case(agent_name):
            self.error("Name must be in snake_case.")
            return

        if agent_name in self.app.state.agents.keys():
            self.error("Agent name must be unique.")
            return

        if agent_name in self.app.state.tasks.keys():
            self.error("Agent name cannot match a task name.")
            return

        self.app.state.create_agent(
            name=agent_name,
            role=self.agent_role.value,
            goal=self.agent_goal.value,
            backstory=self.agent_backstory.value,
        )
        self.app.advance()

    def form(self) -> list[Renderable]:
        large_field_height = min(5, round((self.height - 17) / 3))
        return [
            Text((11, 2), (1, 12), color=COLOR_FORM, value="Name"),
            TextInput(
                (11, 14),
                (2, self.width - 16),
                self.agent_name,
                placeholder="A unique name for this agent. Must be snake_case.",
                **FIELD_COLORS,
            ),
            Text((13, 2), (1, 12), color=COLOR_FORM, value="Role"),
            TextInput(
                (13, 14),
                (large_field_height, self.width - 16),
                self.agent_role,
                placeholder="A prompt to the agent that describes the role it takes in your project.",
                ** FIELD_COLORS,
            ),
            Text((13 + large_field_height, 2), (1, 12), color=COLOR_FORM, value="Goal"),
            TextInput(
                (13 + large_field_height, 14),
                (large_field_height, self.width - 16),
                self.agent_goal,
                placeholder="A prompt to the agent that describes the goal it is trying to achieve.",
                **FIELD_COLORS,
            ),
            Text((13 + (large_field_height * 2), 2), (1, 12), color=COLOR_FORM, value="Backstory"),
            TextInput(
                (13 + (large_field_height * 2), 14),
                (large_field_height, self.width - 16),
                self.agent_backstory,
                placeholder="A prompt to the agent that describes the backstory of it's purpose.",
                **FIELD_COLORS,
            ),
        ]


class ModelView(FormView):
    title = "Select a Model"

    def __init__(self, app: 'App'):
        super().__init__(app)
        self.MODEL_CHOICES = providers.get_preferred_models()
        self.model_choice = Node()
        self.model_logo = Node()
        self.model_name = Node()
        self.model_description = Node()

    def set_model_selection(self, index: int, value: str):
        """Update the content of the model info box."""
        model = self.MODEL_CHOICES[index]
        self.model_logo.value = model.host
        self.model_name.value = model.name
        self.model_description.value = model.description

    def set_model_choice(self, index: int, value: str):
        """Save the selection."""
        # list in UI shows the actual key
        self.model_choice.value = value

    def get_model_options(self):
        return providers.get_preferred_model_ids()

    def submit(self):
        if not self.model_choice.value:
            self.error("Model is required.")
            return

        self.app.state.update_active_agent(llm=self.model_choice.value)
        self.app.advance()

    def form(self) -> list[Renderable]:
        return [
            RadioSelect(
                (10, 1),
                (self.height - 15, round(self.width / 2) - 2),
                options=self.get_model_options(),
                color=COLOR_FORM_BORDER,
                highlight=ColorAnimation(COLOR_BUTTON.sat(0), COLOR_BUTTON, duration=0.2),
                on_change=self.set_model_selection,
                on_select=self.set_model_choice,
            ),
            Box(
                (10, round(self.width / 2)),
                (self.height - 15, round(self.width / 2) - 2),
                color=COLOR_FORM_BORDER,
                modules=[
                    ASCIIText(
                        (1, 3),
                        (4, round(self.width / 2) - 10),
                        color=COLOR_FORM.sat(40),
                        value=self.model_logo,
                    ),
                    BoldText(
                        (5, 3), (1, round(self.width / 2) - 10), color=COLOR_FORM, value=self.model_name
                    ),
                    WrappedText(
                        (7, 3),
                        (min(5, self.height - 24), round(self.width / 2) - 10),
                        color=COLOR_FORM.sat(50),
                        value=self.model_description,
                    ),
                ],
            ),
        ]


class ToolCategoryView(FormView):
    title = "Select a Tool Category"

    def __init__(self, app: 'App'):
        super().__init__(app)
        self.tool_category_key = Node()
        self.tool_category_name = Node()
        self.tool_category_description = Node()

    def set_tool_category_selection(self, index: int, value: str):
        tool_category = None
        for _tool_category in get_all_tool_categories():
            if _tool_category.name == value:  # search by name
                tool_category = _tool_category
                break

        if tool_category:
            self.tool_category_name.value = tool_category.title
            self.tool_category_description.value = tool_category.description

    def set_tool_category_choice(self, index: int, value: str):
        self.tool_category_key.value = value

    def submit(self):
        if not self.tool_category_key.value:
            self.error("Tool category is required.")
            return

        self.app.state.tool_category = self.tool_category_key.value
        self.app.advance()

    def skip(self):
        self.app.advance(steps=2)

    def form(self) -> list[Renderable]:
        return [
            RadioSelect(
                (10, 1),
                (self.height - 15, round(self.width / 2) - 2),
                options=get_all_tool_category_names(),
                color=COLOR_FORM_BORDER,
                highlight=ColorAnimation(COLOR_BUTTON.sat(0), COLOR_BUTTON, duration=0.2),
                on_change=self.set_tool_category_selection,
                on_select=self.set_tool_category_choice,
            ),
            Box(
                (10, round(self.width / 2) + 1),
                (self.height - 15, round(self.width / 2) - 2),
                color=COLOR_FORM_BORDER,
                modules=[
                    ASCIIText(
                        (1, 3),
                        (4, round(self.width / 2) - 10),
                        color=COLOR_FORM.sat(40),
                        value=self.tool_category_name,
                    ),
                    BoldText(
                        (5, 3),
                        (1, round(self.width / 2) - 10),
                        color=COLOR_FORM,
                        value=self.tool_category_name,
                    ),
                    WrappedText(
                        (7, 3),
                        (min(5, self.height - 24), round(self.width / 2) - 10),
                        color=COLOR_FORM.sat(50),
                        value=self.tool_category_description,
                    ),
                ],
            ),
            Button(
                (self.height - 5, 2),
                (3, 15),
                "Skip",
                color=COLOR_BUTTON,
                on_confirm=self.skip,
            ),
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
                (10, 1),
                (self.height - 15, round(self.width / 2) - 2),
                options=self.get_tool_options(),
                color=COLOR_FORM_BORDER,
                highlight=ColorAnimation(COLOR_BUTTON.sat(0), COLOR_BUTTON, duration=0.2),
                on_change=self.set_tool_selection,
                on_select=self.set_tool_choice,
            ),
            Box(
                (10, round(self.width / 2) + 1),
                (self.height - 15, round(self.width / 2) - 2),
                color=COLOR_FORM_BORDER,
                modules=[
                    ASCIIText(
                        (1, 3),
                        (4, round(self.width / 2) - 10),
                        color=COLOR_FORM.sat(40),
                        value=self.tool_name,
                    ),
                    BoldText((5, 3), (1, round(self.width / 2) - 10), color=COLOR_FORM, value=self.tool_name),
                    WrappedText(
                        (7, 3),
                        (min(5, self.height - 24), round(self.width / 2) - 10),
                        color=COLOR_FORM.sat(50),
                        value=self.tool_description,
                    ),
                ],
            ),
            Button(
                (self.height - 5, 2),
                (3, 15),
                "Back",
                color=COLOR_BUTTON,
                on_confirm=self.back,
            ),
        ]


class ToolAgentSelectionView(AgentSelectionView):
    title = "Select an Agent for your Tool"

    def submit(self):
        if not self.agent_key.value:
            self.error("Agent is required.")
            return

        self.app.state.active_agent = self.agent_key.value
        self.app.advance()


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
        task_name = self.task_name.value
        if not self.task_name:
            self.error("Task name is required.")
            return

        if not is_snake_case(task_name):
            self.error("Task name must be in snake_case.")
            return

        if task_name in self.app.state.tasks.keys():
            self.error("Task name must be unique.")
            return

        if task_name in self.app.state.agents.keys():
            self.error("Task name cannot match an agent name.")
            return

        self.app.state.create_task(
            name=task_name,
            description=self.task_description.value,
            expected_output=self.expected_output.value,
        )
        self.app.advance()

    def form(self) -> list[Renderable]:
        large_field_height = min(5, round((self.height - 17) / 3))
        return [
            Text((11, 2), (1, 12), color=COLOR_FORM, value="Name"),
            TextInput(
                (11, 14),
                (2, self.width - 16),
                self.task_name,
                placeholder="A unique name for this task. Must be snake_case.",
                **FIELD_COLORS,
            ),
            Text((13, 2), (1, 12), color=COLOR_FORM, value="Description"),
            TextInput(
                (13, 14),
                (large_field_height, self.width - 16),
                self.task_description,
                placeholder="A prompt for this task that describes what should be done.",
                **FIELD_COLORS,
            ),
            Text((13 + large_field_height, 2), (2, 12), color=COLOR_FORM, value="Expected\nOutput"),
            TextInput(
                (13 + large_field_height, 14),
                (large_field_height, self.width - 16),
                self.expected_output,
                placeholder="A prompt for this task that describes what the output should look like.",
                **FIELD_COLORS,
            ),
        ]


class TaskAgentSelectionView(AgentSelectionView):
    title = "Select an Agent for your Task"

    def submit(self):
        if not self.agent_key.value:
            self.error("Agent is required.")
            return

        self.app.state.update_active_task(agent=self.agent_key.value)
        self.app.advance()


class AfterTaskView(BannerView):
    title = "Let there be tasks!"
    sparkle = "(ノ ˘_˘)ノ　ζ|||ζ　ζ|||ζ　ζ|||ζ"
    subtitle = "Tasks are the heart of your agent's work. "


class DebugView(WizardView):
    name = "debug"

    def layout(self) -> list[Renderable]:
        from agentstack.utils import get_version

        return [
            Box(
                (0, 0),
                (self.height - 1, self.width),
                color=COLOR_BORDER,
                modules=[
                    ColorWheel((1, 1)),
                    Title(
                        (self.height - 6, 3),
                        (1, self.width - 5),
                        color=COLOR_MAIN,
                        value=f"AgentStack version {get_version()}",
                    ),
                    Title(
                        (self.height - 4, 3),
                        (1, self.width - 5),
                        color=COLOR_MAIN,
                        value=f"Window size: {self.width}x{self.height}",
                    ),
                ],
            ),
            HelpText((self.height - 1, 0), (1, self.width)),
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

    def update_framework(self, framework: str):
        self.project['framework'] = framework

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
                tools.append(
                    TemplateConfig.Tool(
                        name=tool_name,
                        agents=[agent_name],
                    )
                )

        return TemplateConfig(
            template_version=4,
            name=self.project['name'],
            description=self.project['description'],
            framework=self.project['framework'],
            method="sequential",
            agents=[
                TemplateConfig.Agent(
                    name=agent_name,
                    role=agent_data['role'],
                    goal=agent_data['goal'],
                    backstory=agent_data['backstory'],
                    llm=agent_data['llm'],
                )
                for agent_name, agent_data in self.agents.items()
            ],
            tasks=[
                TemplateConfig.Task(
                    name=task_name,
                    description=task_data['description'],
                    expected_output=task_data['expected_output'],
                    agent=self.active_agent,
                )
                for task_name, task_data in self.tasks.items()
            ],
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
        'tool_agent_selection': ToolAgentSelectionView,
        'tool_category': ToolCategoryView,
        'tool': ToolView,
        'after_agent': AfterAgentView,
        'task': TaskView,
        'task_agent_selection': TaskAgentSelectionView,
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
            'task_agent_selection',
            'after_task',
        ],
        'tool': [  # add tools to an agent
            'tool_agent_selection',
            'tool_category',
            'tool',
            'after_agent',
        ],
    }

    state: State
    active_workflow: Optional[str]
    active_view: Optional[str]

    min_width: int = 80
    min_height: int = 24

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
            self._finish_run_once = False
            log.set_stdout(sys.stdout)  # re-enable on-screen logging

            init_project(
                slug_name=template.name,
                template_data=template,
            )

            template.write_to_file(conf.PATH / "wizard")
            log.info(f"Saved template to: {conf.PATH / 'wizard.json'}")

    def advance(self, steps: int = 1):
        """Load the next view in the active workflow."""
        assert self.active_workflow, "No active workflow set."
        assert self.active_view, "No active view set."

        workflow = self.workflow[self.active_workflow]
        current_index = workflow.index(self.active_view)
        view = workflow[current_index + steps]
        self.load(view, workflow=self.active_workflow)

    def back(self):
        """Load the previous view in the active workflow."""
        return self.advance(-1)

    def load(self, view: str, workflow: Optional[str] = None):
        """Load a view from a workflow."""
        self.active_workflow = workflow if workflow else self.active_workflow
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
