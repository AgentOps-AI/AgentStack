from typing import Annotated
from typing_extensions import TypedDict

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

import agentstack
import tools


class State(TypedDict):
    inputs: dict[str, str]
    messages: Annotated[list, add_messages]


class {{ cookiecutter.project_metadata.project_name|replace('-', '')|replace('_', '')|capitalize }}Graph:


{%- for agent in cookiecutter.structure.agents %}
    @agentstack.agent
    def {{ agent.name }}(self, state: State):
        agent_config = agentstack.get_agent('{{ agent.name }}')
        messages = ChatPromptTemplate.from_messages([
            ("user", agent_config.prompt), 
        ])
        messages = messages.format_messages(**state['inputs'])
{%- if agent.model.startswith('anthropic') %}
        agent = ChatAnthropic(model=agent_config.model)
{%- elif agent.model.startswith('openai') %}
        agent = ChatOpenAI(model=agent_config.model)
{%- endif %}
        agent = agent.bind_tools([])
        response = agent.invoke(
            messages + state['messages'],
        )
        return {'messages': [response, ]}
{% endfor %}


{%- for task in cookiecutter.structure.tasks %}
    @agentstack.task
    def {{ task.name }}(self, state: State):
        task_config = agentstack.get_task('{{ task.name }}')
        messages = ChatPromptTemplate.from_messages([
            ("user", task_config.prompt), 
        ])
        messages = messages.format_messages(**state['inputs'])
        return {'messages': messages + state['messages']}
{% endfor %}

    def run(self, inputs: list[str]):
        self.graph = StateGraph(State)

        tools = ToolNode([])
        self.graph.add_node("tools", tools)

{%- for agent in cookiecutter.structure.agents %}
        self.graph.add_node("{{ agent.name }}", self.{{ agent.name }})
        self.graph.add_edge("{{ agent.name }}", "tools")
        self.graph.add_conditional_edges("{{ agent.name }}", tools_condition)
{% endfor %}

{%- for edge in cookiecutter.structure.graph %}
    {%- if edge[0].type == 'special' %}
        self.graph.add_edge({{ edge[0].name }}, "{{ edge[1].name }}")
    {%- elif edge[1].type == 'special' %}
        self.graph.add_edge("{{ edge[0].name }}", {{ edge[1].name }})
    {%- else %}
        self.graph.add_edge("{{ edge[0].name }}", "{{ edge[1].name }}")
    {%- endif %}
{%- endfor %}

        app = self.graph.compile()
        result = app.invoke({
            'inputs': inputs, 
            'messages': [], 
        })
        print(result['messages'][-1].content)

