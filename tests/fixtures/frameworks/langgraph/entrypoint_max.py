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
    def test_agent(self, state: State):
        agent_config = agentstack.get_agent('test_agent')
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
    def test_task(self, state: State):
        task_config = agentstack.get_task('test_task')
        messages = ChatPromptTemplate.from_messages([
            ("user", task_config.prompt), 
        ])
        messages = messages.format_messages(**state['inputs'])
        return {'messages': messages + state['messages']}

    def run(self, inputs: list[str]):
        self.graph = StateGraph(State)
        tools = ToolNode([])
        self.graph.add_node("tools", tools)
        
        self.graph.add_node("test_agent", self.test_agent)
        self.graph.add_edge("test_agent", "tools")
        self.graph.add_conditional_edges("test_agent", tools_condition)

        self.graph.add_edge(START, "test_task")
        self.graph.add_edge("test_task", "test_agent")
        self.graph.add_edge("test_agent", END)

        app = self.graph.compile()
        result = app.invoke({
            'inputs': inputs, 
            'messages': [], 
        })
        print(result['messages'][-1].content)

