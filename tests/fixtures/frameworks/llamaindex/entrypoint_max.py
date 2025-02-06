import asyncio
from llama_index.core.llms import ChatMessage
from llama_index.core.agent.workflow import (
    FunctionAgent, 
    AgentWorkflow, 
    AgentOutput, 
    ToolCallResult, 
)
from llama_index.llms.openai import OpenAI

import agentstack


class LlamaindexStack:
    def _format_history(self, history: list[ChatMessage]) -> str:
        # ideally we would pass these directly to `chat_history`, but passing
        # messages directly overrides the system prompt. this allows us to
        # pass them as a string to `user_msg`.
        return "\n\n".join([f"{msg.role}: {msg.content}" for msg in history])

    @agentstack.task
    def task_name(self) -> ChatMessage:
        task_config = agentstack.get_task('task_name')
        return ChatMessage(role="user", content=task_config.prompt)

    @agentstack.task
    def task_name_two(self) -> ChatMessage:
        task_config = agentstack.get_task('task_name_two')
        return ChatMessage(role="user", content=task_config.prompt)

    @agentstack.agent
    def agent_name(self) -> FunctionAgent:
        agent_config = agentstack.get_agent('agent_name')
        llm = OpenAI(
            model=agent_config.model, 
        )
        return FunctionAgent(
            name=agent_config.name, 
            description=agent_config.role, 
            system_prompt=agent_config.prompt, 
            llm=llm, 
            tools=[], 
        )

    @agentstack.agent
    def second_agent_name(self) -> FunctionAgent:
        agent_config = agentstack.get_agent('second_agent_name')
        llm = OpenAI(
            model=agent_config.model, 
        )
        return FunctionAgent(
            name=agent_config.name, 
            description=agent_config.role, 
            system_prompt=agent_config.prompt, 
            llm=llm, 
            tools=[], 
        )

    async def run(self, inputs: dict[str, str]):
        # TODO interpolate inputs into prompts
        history: list[ChatMessage] = []
        for task_config in agentstack.get_all_tasks():
            task = getattr(self, task_config.name)
            agent = getattr(self, task_config.agent)
            workflow = AgentWorkflow(
                agents=[agent(), ], 
            )
            history.append(task())
            handler = workflow.run(
                user_msg=self._format_history(history), 
                # chat_history=history, 
            )
            
            async for event in handler.stream_events():
                if isinstance(event, AgentOutput) and event.response.content:
                    agentstack.log.notify(event.current_agent_name)
                    agentstack.log.info(event.response.content)
                    history.append(ChatMessage(role="assistant", content=event.response.content))
                elif isinstance(event, ToolCallResult):
                    agentstack.log.notify(f"tool: {event.tool_name}")
                    agentstack.log.info(event.tool_output)