# AgentStack [![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/release/python-3100/) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<img alt="Logo" align="right" src="assets/agentopslogo.png" width="20%" />

Create AI agent projects with no build configuration.

- [Creating an Agent Project](#creating-an-agent-project) – How to create a new agent project.
- [User Guide](https://docs.agentops.ai) – How to develop agent projects bootstrapped with AgentStack.

AgentStack works on macOS, Windows, and Linux.<br>
If something doesn't work, please [file an issue](https://github.com/agentops-ai/agentops/issues/new).<br>
If you have questions or need help, please ask in our [Discord community](https://discord.gg/a4VQ23Aps5).

## Quick Overview

```sh
pip install agentstack
agentstack init my-agent-project
cd my-agent-project
python main.py
```

Then open [http://localhost:3000/](http://localhost:3000/) to see your agent project.<br>
When you're ready to deploy to production, create a production-ready version with `python build.py`.

<p align='center'>
<img src='assets/screenshot.png' width='600' alt='agentstack init'>
</p>

### Get Started Immediately

You **don't** need to install or configure tools like LangChain or LlamaIndex.<br>
They are preconfigured and hidden so that you can focus on the code.

Create a project, and you're good to go.

## Creating an Agent Project

**You'll need to have Python 3.10+ on your local development machine** (but it's not required on the server). We recommend using the latest version. You can use [pyenv](https://github.com/pyenv/pyenv) to switch Python versions between different projects.

To create a new agent project, run:

```sh
pip install agentstack
agentstack init my-agent-project
```

It will create a directory called `my-agent-project` inside the current folder.<br>
Inside that directory, it will generate the initial project structure and install the transitive dependencies:

```
my-agent-project/
├── README.md
├── requirements.txt
├── .gitignore
├── main.py
├── agents/
│   └── (agent files based on your setup)
└── tasks/
    └── (task files based on your setup)
```

No configuration or complicated folder structures, only the files you need to build your agent project.<br>
Once the initialization is done, you can open your project folder:

```sh
cd my-agent-project
```

Inside the newly created project, you can run some built-in commands:

### `python main.py`

Runs the agent project in development mode.<br>
Open [http://localhost:3000](http://localhost:3000) to view it in the browser.

The page will automatically reload if you make changes to the code.<br>
You will see the build errors and lint warnings in the console.

### `python test.py`

Runs the test suite in an interactive mode.<br>
By default, runs tests related to files changed since the last commit.

### `python build.py`

Builds the agent project for production to the `build` folder.<br>
It correctly bundles the project in production mode and optimizes the build for the best performance.

Your agent project is ready to be deployed.

## User Guide

You can find detailed instructions on using AgentStack and many tips in [its documentation](https://docs.agentops.ai).

## How to Update to New Versions?

Please refer to the [User Guide](https://docs.agentops.ai/updating-to-new-releases) for this and other information.

## Philosophy

- **One Dependency:** There is only one build dependency. It uses popular agent frameworks and LLM providers, but provides a cohesive curated experience on top of them.

- **No Configuration Required:** You don't need to configure anything. A reasonably good configuration of both development and production builds is handled for you so you can focus on writing code.

- **No Lock-In:** You can "eject" to a custom setup at any time. Run a single command, and all the configuration and build dependencies will be moved directly into your project, so you can pick up right where you left off.

## What's Included?

Your environment will have everything you need to build a modern AI agent project:

- Support for popular agent frameworks like CrewAI, Autogen, and LiteLLM.
- Easy integration of tools for browsing, RAG, and more.
- A fast interactive test runner with built-in support for coverage reporting.
- A live development server that warns about common mistakes.
- A build script to bundle your project for production.
- Integration with [AgentOps](https://agentops.ai) for AI agent observability.
- Hassle-free updates for the above tools with a single dependency.

## Contributing

We'd love to have your helping hand on AgentStack! See [CONTRIBUTING.md](CONTRIBUTING.md) for more information on what we're looking for and how to get started.

## License

AgentStack is open source software [licensed as MIT](LICENSE).