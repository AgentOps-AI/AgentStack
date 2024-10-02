```text
    ___       ___       ___       ___       ___       ___       ___       ___       ___       ___   
   /\  \     /\  \     /\  \     /\__\     /\  \     /\  \     /\  \     /\  \     /\  \     /\__\  
  /::\  \   /::\  \   /::\  \   /:| _|_    \:\  \   /::\  \    \:\  \   /::\  \   /::\  \   /:/ _/_ 
 /::\:\__\ /:/\:\__\ /::\:\__\ /::|/\__\   /::\__\ /\:\:\__\   /::\__\ /::\:\__\ /:/\:\__\ /::-"\__\
 \/\::/  / \:\:\/__/ \:\:\/  / \/|::/  /  /:/\/__/ \:\:\/__/  /:/\/__/ \/\::/  / \:\ \/__/ \;:;-",-"
   /:/  /   \::/  /   \:\/  /    |:/  /   \/__/     \::/  /   \/__/      /:/  /   \:\__\    |:|  |  
   \/__/     \/__/     \/__/     \/__/               \/__/               \/__/     \/__/     \|__|  
```

The quickest way to build robust agent projects.

---

AgentStack is a Python package designed to quickly scaffold AI agent projects, similar to how `create-react-app` scaffolds React applications. With AgentStack, you can easily set up, develop, and deploy AI agents using popular frameworks, tools, and LLM providers.

## Features

- **Quick Setup**: Scaffold AI agent-based applications in seconds.
- **Framework Flexibility**: Supports a variety of agent and LLM frameworks.
- **Extensible**: Add your own configurations, models, and workflows.
- **Easy Integration**: Use our CLI to generate agents, tasks and tools with one command.

## Installation

To install AgentStack, simply run the following:

```bash
pip install agentstack
```

To start your first AgentStack project, run

```bash
agentstack init
```

## Tools
The power of AgentStack is the ability to quickly add tools to your agents. 

| **Memory / Storage** | **RAG**         | **Browsing**                             | **Sandboxing**  |
|----------------------|-----------------|------------------------------------------|-----------------|
|                      | 🔜 Mem0ai       | 🔜 browserbasehq                         | 🔜 E2b_dev      |
|                      | 🔜 llama_index  | 🔜 firecrawl                             | 🔜 Browserbase  |
|                      |                 | 🔜 MultiOn_AI                            |                 |
|                      |                 | 🔜 Crawl4AI                              |                 |
|                      |                 | 🔜 [Dendrite](https://dendrite.systems/) |                 |

Add tools with the CLI:
```bash
agentstack generate tool <tool_name>
```

[CLI Docs]()

## Models
Any model supported by [LiteLLM](https://docs.litellm.ai/docs/providers) is supported by AgentStack frameworks

## Observability
AI Agent observability is provided by [AgentOps](https://agentops.ai)

AgentOps is baked into AgentStack agents by default. To enable usage, create an AgentOps account and add your API key to the .env file:
```env
AGENTOPS_API_KEY=<your_api_key>
```