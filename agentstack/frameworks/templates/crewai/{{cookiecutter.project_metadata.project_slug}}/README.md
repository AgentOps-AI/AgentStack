# {{ cookiecutter.project_metadata.project_name }}
{{ cookiecutter.project_metadata.description }}

## How to build your Crew Agent
### With the CLI
Add an agent using AgentStack with the CLI:  
`agentstack generate agent <agent_name>`  
You can also shorten this to `agentstack g a <agent_name>`  
For wizard support use `agentstack g a <agent_name> --wizard`  
Finally for creation in the CLI alone, use `agentstack g a <agent_name> --role/-r <role> --goal/-g <goal> --backstory/-b <backstory> --model/-m <provider/model>`

This will automatically create a new agent in the `agents.yaml` config as well as in your code. Either placeholder strings will be used, or data included in the wizard.

Similarly, tasks can be created with `agentstack g t <tool_name>`

Add tools with `agentstack tools add` and view tools available with `agentstack tools list`

## How to use your Agent
In this directory, run `uv pip install --requirements pyproject.toml`

To run your project, use the following command:  
`agentstack run`

This will initialize your crew of AI agents and begin task execution as defined in your configuration in the main.py file.

#### Replay Tasks from Latest Crew Kickoff:

CrewAI now includes a replay feature that allows you to list the tasks from the last run and replay from a specific one. To use this feature, run:  
`crewai replay <task_id>`  
Replace <task_id> with the ID of the task you want to replay.

#### Reset Crew Memory
If you need to reset the memory of your crew before running it again, you can do so by calling the reset memory feature:  
`crewai reset-memory`  
This will clear the crew's memory, allowing for a fresh start.

> 🪩 Project built with [AgentStack](https://github.com/AgentOps-AI/AgentStack)