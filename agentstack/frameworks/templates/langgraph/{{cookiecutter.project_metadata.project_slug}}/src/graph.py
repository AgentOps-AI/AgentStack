from typing import Annotated
from typing_extensions import TypedDict

from langchain.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

import agentstack


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
        result_generator = app.stream({
            'inputs': inputs,
            'messages': [],
        })

        for message in result_generator:
            for k, item in message.items():
                for m in item['messages']:
                    agentstack.log.notify(f"\n\n{k}:")
                    agentstack.log.info(m.content)

