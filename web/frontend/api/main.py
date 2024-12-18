from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import sys
import os
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Add the AgentStack package to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from agentstack.tools import get_all_tools, ToolConfig
from agentstack.agents import AgentConfig
from agentstack.generation.agent_generation import add_agent
from agentstack import frameworks
from agentstack.utils import verify_agentstack_project
from agentstack.conf import ConfigFile

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
        logger.error(f"Error getting tools: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/agents")
async def create_agent(request: AgentRequest):
    try:
        logger.debug("Starting agent creation process")

        # Verify AgentStack project structure
        try:
            verify_agentstack_project()
        except Exception as e:
            logger.error(f"Project verification failed: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Project verification failed: {str(e)}")

        # Generate a name from the first few words of the prompt
        words = [w.lower() for w in request.prompt.split()[:3] if w.isalnum()]
        agent_name = f"agent_{'_'.join(words)}"
        logger.debug(f"Generated agent name: {agent_name}")

        try:
            # Create the agent using AgentStack's add_agent function
            add_agent(
                agent_name=agent_name,
                role="AI Assistant",
                goal=request.prompt,  # Use the prompt as the agent's goal
                backstory="I am an AI assistant created to help with specific tasks.",
                llm=None  # Use default LLM
            )
            logger.debug(f"Agent {agent_name} created successfully")
        except Exception as e:
            logger.error(f"Error creating agent: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error creating agent: {str(e)}")

        # Add selected tools to the agent
        for tool_name in request.tools:
            try:
                tool_config = ToolConfig.from_tool_name(tool_name)
                frameworks.add_tool(tool_config, agent_name)
                logger.debug(f"Added tool {tool_name} to agent {agent_name}")
            except Exception as e:
                logger.error(f"Error adding tool {tool_name}: {str(e)}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"Error adding tool {tool_name}: {str(e)}")

        return {
            "name": agent_name,
            "description": request.prompt,
            "tools": [{"id": tool, "name": tool, "description": ""} for tool in request.tools]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
