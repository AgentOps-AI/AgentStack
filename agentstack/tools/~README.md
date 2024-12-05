

Tool Implementations
====================
Each tool gets a directory in this folder. 

The directory should contain the following files:

`config.json`
-------------
This contains the configuration for the tool for use by agentstack.

`pyproject.toml`
----------------
This contains the build configuration for the tool and any dependencies.

`crew.py`
---------
Python package which contains the tool implementation specific to CrewAI.
Use relative imports to include shared code from the root of the tool's package.
Deploy/install command should handle both single files and directories.

Additional frameworks will get their own directories.


`config.json` Format
--------------------
Tools are configured for installation & removal using JSON files in this directory. 

## Parameters

### `name` (string) [required]
The name of the tool in snake_case. This is used to identify the tool in the system.

### `tools` (list) [required]
List of public methods that are accessible in the tool implementation.

### `tools_bundled` (boolean) [optional]
Indicates that the tool file exports a `list` of tools. Specify the variable name
of the list in the `tools` field.

### `cta` (string) [optional]
String to print in the terminal when the tool is installed that provides a call to action.

### `env` (list[dict(str, Any)]) [optional]
Definitions for environment variables that will be appended to the local `.env` file.
This is a list of key-value pairs ie. `[{"ENV_VAR": "value"}, ...]`.
In cases where the user is expected to provide a value, the value is `"..."`.

### `post_install` (string) [optional]
Shell command that will be executed after packages have been installed and environment 
variables have been set.

### `post_remove` (string) [optional]
Shell command that will be executed after the tool has been removed.

