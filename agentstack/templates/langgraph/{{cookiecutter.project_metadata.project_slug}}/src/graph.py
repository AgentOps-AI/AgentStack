from typing import Annotated
from typing_extensions import TypedDict

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

    def run(self, inputs: list[str]):
        tools = ToolNode([])
        self.graph = StateGraph(State)
        self.graph.add_node("tools", tools)
        self.graph.add_edge(START, END)

        app = self.graph.compile()
        result = app.invoke({
            'inputs': inputs, 
            'messages': [], 
        })
        print(result['messages'][-1].content)

