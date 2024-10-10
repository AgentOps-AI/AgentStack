# AgentStack CLI Documentation

## Overview
The **AgentStack CLI** is the easiest way to scaffold and build agent applications. This command-line interface allows you to quickly initialize projects, generate agents or tasks, and manage tools to support agent development. Below is a detailed explanation of the commands available in the CLI.

---

## Command Options

### `-v, --version`
- **Description:** Displays the current version of AgentStack.
- **Usage:**
  ```bash
  agentstack -v
  ```

---

## Top-Level Commands

### `init` (`i`)
- **Description:** Initializes a directory for an AgentStack project, setting up the basic structure.
- **Aliases:** `i`
- **Usage:**
  ```bash
  agentstack init
  ```

### `generate` (`g`)
- **Description:** Generates agents or tasks within the project. This command contains additional subcommands for generating agents and tasks.
- **Aliases:** `g`

#### Subcommands for `generate`:

1. **`agent` (`a`)**
   - **Description:** Generates a new agent with optional specifications such as role, goal, backstory, and language model.
   - **Aliases:** `a`
   - **Arguments:**
     - `name`: Name of the agent (required).
     - `--role, -r`: Role of the agent (optional).
     - `--goal, -g`: Goal of the agent (optional).
     - `--backstory, -b`: Backstory of the agent (optional).
     - `--llm, -l`: Language model to use (optional).
   - **Usage:**
     ```bash
     agentstack generate agent <name> --role <role> --goal <goal> --backstory <backstory> --llm <llm>
     ```

2. **`task` (`t`)**
   - **Description:** Generates a new task, optionally associating it with an agent.
   - **Aliases:** `t`
   - **Arguments:**
     - `name`: Name of the task (required).
     - `--description, -d`: Description of the task (optional).
     - `--expected_output, -e`: Expected output of the task (optional).
     - `--agent, -a`: Name of the agent associated with the task (optional).
   - **Usage:**
     ```bash
     agentstack generate task <name> --description <description> --expected_output <expected_output> --agent <agent>
     ```

---

### `tools` (`t`)
- **Description:** Manages tools within the AgentStack environment. This command contains subcommands for listing and adding tools.
- **Aliases:** `t`

#### Subcommands for `tools`:

1. **`list` (`l`)**
   - **Description:** Lists all available tools in the current environment.
   - **Aliases:** `l`
   - **Usage:**
     ```bash
     agentstack tools list
     ```

2. **`add` (`a`)**
   - **Description:** Adds a new tool to the environment by specifying its name.
   - **Aliases:** `a`
   - **Arguments:**
     - `name`: Name of the tool to add (required).
   - **Usage:**
     ```bash
     agentstack tools add <name>
     ```

---

## Examples

1. **Initialize a new project:**
   ```bash
   agentstack init
   ```

2. **Generate a new agent:**
   ```bash
   agentstack generate agent "JohnDoe" --role "Leader" --goal "Build a strong team" --backstory "John has a history in management." --llm "GPT-4"
   ```

3. **Generate a new task:**
   ```bash
   agentstack generate task "PlanEvent" --description "Plan an event for the team" --expected_output "Event agenda" --agent "JohnDoe"
   ```

4. **List all available tools:**
   ```bash
   agentstack tools list
   ```

5. **Add a new tool:**
   ```bash
   agentstack tools add "TimeTracker"
   ```
