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
    def run(self, inputs: list[str]):
        self.graph = StateGraph(State)
        tools = ToolNode([])
        self.graph.add_node("tools", tools)

        app = self.graph.compile()
        result = app.invoke({
            'inputs': inputs, 
            'messages': [], 
        })

