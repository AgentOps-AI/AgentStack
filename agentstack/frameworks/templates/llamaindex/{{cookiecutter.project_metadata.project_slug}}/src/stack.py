import asyncio
from llama_index.core.llms import ChatMessage
from llama_index.core.agent.workflow import (
    FunctionAgent, 
    AgentWorkflow, 
    AgentOutput, 
    ToolCallResult, 
)
import agentstack


class {{ cookiecutter.project_metadata.class_name }}Stack:

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
                chat_history=history, 
            )
            
            async for event in handler.stream_events():
                if isinstance(event, AgentOutput) and event.response.content:
                    agentstack.log.notify(event.current_agent_name)
                    agentstack.log.info(event.response.content)
                    history.append(ChatMessage(role="assistant", content=event.response.content))
                elif isinstance(event, ToolCallResult):
                    agentstack.log.notify(f"tool: {event.tool_name}")
                    agentstack.log.info(event.tool_output)