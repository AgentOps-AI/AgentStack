# Contributing
First of all, __thank you__ for your interest in contributing to AgentStack! Even the smallest contributions help a _ton_.

Our vision is to build the defacto CLI for quickly spinning up an AI Agent project. We want to be the [create-react-app](https://create-react-app.dev/) of agents. Our inspiration also includes the oh-so-convenient [Angular CLI](https://v17.angular.io/cli).

## How to Help

Grab an issue from the [issues tab](https://github.com/AgentOps-AI/AgentStack/issues)! Plenty are labelled "Good First Issue". Fork the repo and create a PR when ready!

The best place to engage in conversation about your contribution is in the Issue chat or on our [Discord](https://discord.gg/ahqWRGquEV).

## Setup

1. Clone the repo
2. `poetry install`
3. `pip install -e .`
   - This will install the CLI locally and in editable mode so you can use `agentstack <command>` to test your latest changes

## Project Structure
TODO

## Adding Tools
If you're reading this section, you probably have a product that AI agents can use as a tool. We're glad you're here!

Adding tools is easy once you understand the project structure. A few things need to be done for a tool to be considered completely supported:

1. Modify `agentstack/tools/tools.json`
   - Add your tool and relevant information to this file as appropriate.
2. Create a config for your tool
   - As an example, look at `mem0.json`
   - AgentStack uses this to know what code to insert where. Follow the structure to add your tool.
3. Create your implementation for each framework
   - In `agentstack/templates/<framework>/tools`, you'll see other implementations of tools.
   - Build your tool implementation for that framework. This file will be inserted in the user's project.
   - The tools that are exported from this file should be listed in the tool's config json.
4. Manually test your tool integration by running `agentstack tools add <your_tool>` and ensure it behaves as expected.

## Tests
HAHAHAHAHAHAHA good one