from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import sys
import os

# Add the AgentStack package to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from agentstack.tools import get_all_tools
from agentstack.agents import AgentConfig
from agentstack.generation.agent_generation import generate_agent

app = FastAPI()

# Configure CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite's default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AgentRequest(BaseModel):
    prompt: str
    tools: List[str]

@app.get("/api/tools")
async def get_tools():
    try:
        tools = get_all_tools()
        return [{"name": tool.name, "category": tool.category} for tool in tools]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/agents")
async def create_agent(request: AgentRequest):
    try:
        # Create agent configuration
        agent_config = AgentConfig(
            name=f"Agent for: {request.prompt[:30]}...",
            description=request.prompt,
            tools=request.tools
        )

        # Generate the agent
        agent = generate_agent(agent_config)

        return {
            "name": agent.name,
            "description": agent.description,
            "tools": [{"id": tool, "name": tool, "description": ""} for tool in agent.tools]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
