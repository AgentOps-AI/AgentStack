"""
Agent Protocol implementation for AgentStack.

This module implements a FastAPI server that follows the agent-protocol specification
for serving LLM agents in production.
"""
from typing import Optional, Dict, Any
from fastapi import FastAPI
from agent_protocol import AgentProtocol, Step, Task

app = FastAPI()
agent_protocol = AgentProtocol(app)


@agent_protocol.on_task
async def task_handler(task: Task) -> None:
    """
    Handle incoming tasks from the agent protocol.

    Args:
        task: The task to be processed
    """
    # Initialize task processing
    await task.step.create_step(
        "Initializing task processing",
        is_last=False
    )


@agent_protocol.on_step
async def step_handler(step: Step) -> None:
    """
    Handle individual steps within a task.

    Args:
        step: The step to be processed
    """
    # Process step and return result
    await step.create_step(
        "Processing step",
        is_last=True
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
