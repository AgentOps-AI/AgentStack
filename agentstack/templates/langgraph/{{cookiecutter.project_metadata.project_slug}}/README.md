# {{ cookiecutter.project_metadata.project_name }}
{{ cookiecutter.project_metadata.description }}

## How to build your LangGraph Agent
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

This will initialize your AI agent project and begin task execution as defined in your configuration in the main.py file.

> 🪩 Project built with [AgentStack](https://github.com/AgentOps-AI/AgentStack)