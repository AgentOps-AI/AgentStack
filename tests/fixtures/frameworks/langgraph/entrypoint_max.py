from typing import Annotated
from typing_extensions import TypedDict

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

import agentstack


class State(TypedDict):
    inputs: dict[str, str]
    messages: Annotated[list, add_messages]


class TestGraph:
    @agentstack.agent
    def agent_name(self, state: State):
        agent_config = agentstack.get_agent('agent_name')
        messages = ChatPromptTemplate.from_messages([
            ("user", agent_config.prompt), 
        ])
        messages = messages.format_messages(**state['inputs'])
        agent = ChatOpenAI(model=agent_config.model)
        agent = agent.bind_tools([])
        response = agent.invoke(
            messages + state['messages'],
        )
        return {'messages': [response, ]}

    @agentstack.agent
    def second_agent_name(self, state: State):
        agent_config = agentstack.get_agent('second_agent_name')
        messages = ChatPromptTemplate.from_messages([
            ("user", agent_config.prompt), 
        ])
        messages = messages.format_messages(**state['inputs'])
        agent = ChatOpenAI(model=agent_config.model)
        agent = agent.bind_tools([])
        response = agent.invoke(
            messages + state['messages'],
        )
        return {'messages': [response, ]}

    @agentstack.task
    def task_name(self, state: State):
        task_config = agentstack.get_task('task_name')
        messages = ChatPromptTemplate.from_messages([
            ("user", task_config.prompt), 
        ])
        messages = messages.format_messages(**state['inputs'])
        return {'messages': messages + state['messages']}

    @agentstack.task
    def task_name_two(self, state: State):
        task_config = agentstack.get_task('task_name_two')
        messages = ChatPromptTemplate.from_messages([
            ("user", task_config.prompt), 
        ])
        messages = messages.format_messages(**state['inputs'])
        return {'messages': messages + state['messages']}

    def run(self, inputs: list[str]):
        self.graph = StateGraph(State)
        tools = ToolNode([])
        self.graph.add_node("tools", tools)
        
        self.graph.add_node("agent_name", self.agent_name)
        self.graph.add_edge("agent_name", "tools")
        self.graph.add_conditional_edges("agent_name", tools_condition)

        self.graph.add_node("second_agent_name", self.agent_name)
        self.graph.add_edge("second_agent_name", "tools")
        self.graph.add_conditional_edges("second_agent_name", tools_condition)

        self.graph.add_node("task_name", self.task_name)
        self.graph.add_node("task_name_two", self.task_name)

        self.graph.add_edge(START, "task_name")
        self.graph.add_edge(START, "task_name_two")
        self.graph.add_edge("task_name", "agent_name")
        self.graph.add_edge("task_name_two", "second_agent_name")
        self.graph.add_edge("agent_name", END)
        self.graph.add_edge("second_agent_name", END)

        app = self.graph.compile()
        result = app.invoke({
            'inputs': inputs, 
            'messages': [], 
        })
        print(result['messages'][-1].content)

