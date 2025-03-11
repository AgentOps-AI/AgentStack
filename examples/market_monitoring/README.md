# market_monitoring

Tracks competitor websites for pricing and product updates.

## How to Build this Project

### With the CLI

```bash
agentstack init market_monitoring

agentstack generate agent web_scraper
agentstack generate task scrape_site

agentstack generate agent market_reporter
agentstack generate task report

agentstack tools add agentql
```

Add more agents with `agentstack agent <agent_name>` and more tasks with `agentstack task <task_name>`

Add tools with `agentstack tools add <tool_name>` and view tools available with `agentstack tools list`

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
