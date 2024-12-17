"""
Maximum implementation of agent-protocol for testing.
"""

from typing import Optional, Dict, Any, List
from fastapi import FastAPI
from agent_protocol import AgentProtocol, Step, Task

import tools

app = FastAPI()
agent_protocol = AgentProtocol(app)


def test_agent() -> None:
    pass


def test_agent_two() -> None:
    pass


def task_test() -> None:
    pass


def task_test_two() -> None:
    pass


tools = []


@agent_protocol.on_task
async def task_handler(task: Task) -> None:
    await task.step.create_step("Processing task", is_last=False)


@agent_protocol.on_step
async def step_handler(step: Step) -> None:
    await step.create_step("Processing step", is_last=True)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
