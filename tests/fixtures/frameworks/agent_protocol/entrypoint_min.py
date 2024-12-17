"""
Minimal implementation of agent-protocol for testing.
"""

from fastapi import FastAPI
from agent_protocol import AgentProtocol, Step, Task

import tools

app = FastAPI()
agent_protocol = AgentProtocol(app)

tools = []  # Initial tool setup


@agent_protocol.on_task
async def handle_task(task: Task) -> None:
    pass


@agent_protocol.on_step
async def handle_step(step: Step) -> None:
    pass


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
