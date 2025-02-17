## Wizard


## LangGraph

[ ] Bug: empty `bind_tools` list on a new Agent throws an error

[ ] Reliably handle adding two Tasks and two Agent via CLI

[ ] Create a new template demonstrating graph usage


"Top of Funnel"

[√] Hello World!

[√] Catch common exception types from the user's first `agentstack run` and provide a helpful error message.
    - In order to avoid importing all the sub-libraries, use string matching to determine what the exception is. 

[√] Allow the user to select from a list of tools if a <tool_name> is not provided to `agenstack add tools`

[ ] Handle all setup tasks that `agentstack init` needs. 
    - Wrap the output in a `curses` window to show progress.
    - Prevent the user from having to scroll back up to find the help text from the `init` command.
    - Use `uv` for all package management. 

[√] Modify agentops init to indicate which tools are being used.
    - Possibly with an `agentstack.get_tags()` method that automatically sets relevant tags.

[√] If there is only one agent in the project, treat it as a default. 
    - New tasks should be assigned to it. 

[√] Wrap tools in the framework's protocol before including them in the project.
    - Access tools with `agentstack.tools['tool_name']` which dynamically generates the wrapped tool. 
    - This will be a breaking change with the 0.3 release.